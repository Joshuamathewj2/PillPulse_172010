"""Fuzzy matching of OCR'd / handwritten drug names against a bundled reference list."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from rapidfuzz import fuzz, process

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "medicines.csv"

# Dosage-form prefixes and noise that appear on prescriptions but are not part of the name.
_FORM_PREFIX = re.compile(r"^\s*(?:\d+[.)]\s*)?(?:tab|tabs|tablet|cap|caps|capsule|syp|syr|syrup|inj|oint|crm|cream|gel|drops?|susp|sachet|rx)\b\.?\s*", re.I)
# Drop only the unit: the number is often part of the brand ("Dolo 650", "Pan 40").
_STRENGTH = re.compile(r"(\d)\s*(?:mg|mcg|g|ml|iu)\b|(\d)\s*%", re.I)


@dataclass(frozen=True)
class DrugEntry:
    brand: str
    generic: str
    strength: str
    form: str
    drug_class: str
    use: str


@dataclass
class DrugMatch:
    entry: DrugEntry
    score: float  # 0-100
    matched_on: str  # "brand" | "generic"


def normalize_name(raw: str) -> str:
    name = _FORM_PREFIX.sub("", raw or "")
    name = _STRENGTH.sub(lambda m: m.group(1) or m.group(2), name)
    name = re.sub(r"[^A-Za-z0-9+ ]", " ", name)
    return re.sub(r"\s+", " ", name).strip().lower()


@lru_cache(maxsize=1)
def load_drugs() -> List[DrugEntry]:
    with DATA_FILE.open(encoding="utf-8") as f:
        return [
            DrugEntry(
                brand=row["brand"].strip(),
                generic=row["generic"].strip(),
                strength=row["strength"].strip(),
                form=row["form"].strip(),
                drug_class=row["drug_class"].strip(),
                use=row["use"].strip(),
            )
            for row in csv.DictReader(f)
        ]


@lru_cache(maxsize=1)
def _choices():
    drugs = load_drugs()
    keys: list[str] = []
    meta: list[tuple[int, str]] = []
    for i, d in enumerate(drugs):
        keys.append(d.brand.lower())
        meta.append((i, "brand"))
        keys.append(d.generic.lower())
        meta.append((i, "generic"))
    return keys, meta


def match_drug(raw_name: str, min_score: float = 72.0) -> Optional[DrugMatch]:
    """Return the best reference match for ``raw_name`` or ``None`` if nothing is close enough."""
    query = normalize_name(raw_name)
    if len(query) < 3:
        return None
    keys, meta = _choices()
    drugs = load_drugs()

    # Exact hit on brand or generic first - cheap and unambiguous.
    for key, (idx, kind) in zip(keys, meta):
        if key == query:
            return DrugMatch(drugs[idx], 100.0, kind)

    best = None
    # WRatio handles partial / token-order differences ("dolo" vs "dolo 650");
    # plain ratio protects against short queries matching long names too eagerly.
    for scorer in (fuzz.WRatio, fuzz.ratio):
        hit = process.extractOne(query, keys, scorer=scorer)
        if hit is None:
            continue
        key, score, pos = hit
        if scorer is fuzz.WRatio and len(query) < 5:
            score = min(score, fuzz.ratio(query, key))
        if best is None or score > best[1]:
            best = (pos, score)
    if best is None or best[1] < min_score:
        return None
    idx, kind = meta[best[0]]
    return DrugMatch(drugs[idx], round(float(best[1]), 1), kind)


def find_drug_mentions(text: str, min_score: float = 86.0) -> List[tuple[str, DrugMatch]]:
    """Scan free OCR text line by line and return (line, match) for lines that name a drug."""
    results = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if len(stripped) < 3:
            continue
        candidate = normalize_name(stripped)
        words = candidate.split()
        best: Optional[DrugMatch] = None
        # Try the first 1-3 words of the line as the drug name (names lead the line on prescriptions).
        for n in (3, 2, 1):
            if len(words) >= n:
                m = match_drug(" ".join(words[:n]), min_score=min_score)
                if m and (best is None or m.score > best.score):
                    best = m
        if best:
            results.append((stripped, best))
    return results
