"""Text generation with a provider chain: Gemini -> Claude -> Ollama.

Returns ``None`` when no provider is configured or all fail, so callers can
fall back to deterministic behaviour instead of showing a fake answer.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

import httpx

log = logging.getLogger(__name__)


def _gemini(system: str, prompt: str, json_mode: bool) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.3,
            response_mime_type="application/json" if json_mode else "text/plain",
        ),
    )
    return response.text or ""


def _claude(system: str, prompt: str, json_mode: bool) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5"),
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "low"},
        system=system + ("\nRespond with a single JSON object and nothing else." if json_mode else ""),
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("refused")
    return "".join(b.text for b in response.content if b.type == "text")


def _ollama(system: str, prompt: str, json_mode: bool) -> str:
    payload = {
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "system": system,
        "prompt": prompt,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    r = httpx.post(f"{os.environ['OLLAMA_URL'].rstrip('/')}/api/generate", json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "")


_PROVIDERS = [
    ("gemini", lambda: bool(os.getenv("GEMINI_API_KEY")), _gemini),
    ("claude", lambda: bool(os.getenv("ANTHROPIC_API_KEY")), _claude),
    ("ollama", lambda: bool(os.getenv("OLLAMA_URL")), _ollama),
]


def available_providers() -> list[str]:
    return [name for name, ok, _ in _PROVIDERS if ok()]


def generate(prompt: str, system: str = "", json_mode: bool = False) -> Optional[str]:
    for name, ok, fn in _PROVIDERS:
        if not ok():
            continue
        try:
            text = fn(system, prompt, json_mode)
            if text.strip():
                return text
        except Exception as e:
            log.warning("LLM provider %s failed: %s", name, e)
    return None


async def generate_async(prompt: str, system: str = "", json_mode: bool = False) -> Optional[str]:
    return await asyncio.to_thread(generate, prompt, system, json_mode)


def extract_json(text: Optional[str]):
    """Pull the first JSON object out of a model reply (tolerates ```json fences)."""
    if not text:
        return None
    t = text.strip()
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(t[start : end + 1])
    except json.JSONDecodeError:
        return None
