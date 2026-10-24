"""Extraction engines: each turns a prescription photo into raw medicine lines.

Engines only *read*; they never invent schedules. Timing, matching and safety
checks happen afterwards in deterministic code (see ``pipeline.py``).
"""
from __future__ import annotations

import base64
import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from typing import List, Optional

from . import preprocess
from .drug_db import find_drug_mentions

log = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are reading a photo of a (possibly handwritten) medical prescription.
List every medicine the doctor prescribed, exactly as written. Do not guess medicines that are not
on the page, do not add advice, and do not correct the doctor. If a field is illegible, leave it empty
and lower the confidence.

For each medicine return:
- name: the medicine name as written (brand or generic), without the form prefix (Tab/Cap/Syp)
- form: tablet, capsule, syrup, injection, cream, drops, inhaler, ... or empty
- strength: e.g. "650 mg", or empty
- sig: the complete dosing instruction as written, e.g. "1-0-1 x 5 days after food" or "BD PC 1 week"
- raw_line: the whole line as it appears on the page
- confidence: 0-1, how sure you are you read the NAME correctly

Also return raw_text: a plain transcription of the whole prescription body."""

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "medicines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "form": {"type": "string"},
                    "strength": {"type": "string"},
                    "sig": {"type": "string"},
                    "raw_line": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["name", "form", "strength", "sig", "raw_line", "confidence"],
                "additionalProperties": False,
            },
        },
        "raw_text": {"type": "string"},
    },
    "required": ["medicines", "raw_text"],
    "additionalProperties": False,
}


@dataclass
class RawMedicine:
    name: str
    sig: str = ""
    form: str = ""
    strength: str = ""
    raw_line: str = ""
    confidence: float = 0.5


@dataclass
class ExtractionResult:
    engine: str
    medicines: List[RawMedicine] = field(default_factory=list)
    raw_text: str = ""


class EngineUnavailable(RuntimeError):
    pass


def _clamp(x) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except (TypeError, ValueError):
        return 0.5


def _from_payload(engine: str, payload: dict) -> ExtractionResult:
    meds = []
    for m in payload.get("medicines", []) or []:
        name = (m.get("name") or "").strip()
        if not name:
            continue
        meds.append(
            RawMedicine(
                name=name,
                sig=(m.get("sig") or "").strip(),
                form=(m.get("form") or "").strip(),
                strength=(m.get("strength") or "").strip(),
                raw_line=(m.get("raw_line") or "").strip(),
                confidence=_clamp(m.get("confidence", 0.5)),
            )
        )
    return ExtractionResult(engine=engine, medicines=meds, raw_text=payload.get("raw_text", "") or "")


class Engine:
    name = "base"

    def available(self) -> bool:  # pragma: no cover - trivial
        return False

    def extract(self, image_bytes: bytes) -> ExtractionResult:  # pragma: no cover - interface
        raise NotImplementedError


class GeminiEngine(Engine):
    name = "gemini"

    def available(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    def extract(self, image_bytes: bytes) -> ExtractionResult:
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:  # pragma: no cover - depends on install
            raise EngineUnavailable("google-genai not installed") from e
        data, mime = preprocess.for_vision(image_bytes)
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=[types.Part.from_bytes(data=data, mime_type=mime), EXTRACTION_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=EXTRACTION_SCHEMA,
                temperature=0,
            ),
        )
        return _from_payload(self.name, json.loads(response.text))


class AnthropicEngine(Engine):
    name = "claude"

    def available(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def extract(self, image_bytes: bytes) -> ExtractionResult:
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover - depends on install
            raise EngineUnavailable("anthropic not installed") from e
        data, mime = preprocess.for_vision(image_bytes)
        client = anthropic.Anthropic()
        response = client.beta.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5"),
            max_tokens=16000,
            # Route around safety-classifier false positives on medical images.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": EXTRACTION_SCHEMA}},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": mime, "data": base64.standard_b64encode(data).decode()},
                        },
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )
        if response.stop_reason == "refusal":
            raise EngineUnavailable("Claude declined to read this image")
        text = next((b.text for b in response.content if b.type == "text"), "")
        return _from_payload(self.name, json.loads(text))


class TesseractEngine(Engine):
    """Offline fallback: OCR + reference-list matching. Works for printed and neat
    handwritten prescriptions; messy handwriting needs a vision engine."""

    name = "tesseract"

    def available(self) -> bool:
        try:
            import pytesseract  # noqa: F401
        except ImportError:
            return False
        cmd = os.getenv("TESSERACT_CMD")
        if cmd:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = cmd
            return os.path.exists(cmd)
        return shutil.which("tesseract") is not None

    def extract(self, image_bytes: bytes) -> ExtractionResult:
        import pytesseract

        page = preprocess.for_ocr(image_bytes)
        text = pytesseract.image_to_string(page, config="--oem 1 --psm 6")
        return self.parse_text(text)

    @classmethod
    def parse_text(cls, text: str) -> ExtractionResult:
        meds = []
        for line, match in find_drug_mentions(text):
            meds.append(
                RawMedicine(
                    name=match.entry.brand,
                    sig=line,
                    raw_line=line,
                    confidence=round(match.score / 100 * 0.85, 2),  # OCR is never fully certain
                )
            )
        return ExtractionResult(engine=cls.name, medicines=meds, raw_text=text)


ENGINES = {"gemini": GeminiEngine, "claude": AnthropicEngine, "tesseract": TesseractEngine}


def engine_chain() -> List[Engine]:
    order = os.getenv("PRESCRIPTION_ENGINES", "gemini,claude,tesseract")
    return [ENGINES[n.strip()]() for n in order.split(",") if n.strip() in ENGINES]


def available_engines() -> List[str]:
    return [e.name for e in engine_chain() if e.available()]


def run_chain(image_bytes: bytes, engines: Optional[List[Engine]] = None) -> ExtractionResult:
    engines = engines if engines is not None else engine_chain()
    errors = []
    for engine in engines:
        if not engine.available():
            continue
        try:
            result = engine.extract(image_bytes)
            log.info("prescription read by %s: %d medicines", engine.name, len(result.medicines))
            return result
        except preprocess.InvalidImageError:
            raise
        except Exception as e:  # try the next engine
            log.warning("engine %s failed: %s", engine.name, e)
            errors.append(f"{engine.name}: {e}")
    if errors:
        raise EngineUnavailable("All extraction engines failed: " + "; ".join(errors))
    raise EngineUnavailable(
        "No prescription reader is configured. Set GEMINI_API_KEY or ANTHROPIC_API_KEY, or install Tesseract."
    )
