"""Deterministic parser for prescription "sig" instructions.

Turns shorthand that Indian prescriptions commonly use (``1-0-1``, ``BD``,
``TDS``, ``HS``, ``AC/PC``, ``x 5 days``, ``5/7``) into concrete clock times,
dose counts and a duration. No model involved: the same input always yields
the same schedule, which is what you want for medication timing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from fractions import Fraction
from typing import List, Optional


@dataclass
class DayPlan:
    """Anchor times (HH:MM, 24h) the schedule is built around."""

    wake: str = "07:00"
    breakfast: str = "08:00"
    lunch: str = "13:00"
    dinner: str = "20:00"
    bedtime: str = "22:00"


@dataclass
class Sig:
    dose_qty: float = 1.0
    dose_unit: str = "tablet"
    frequency_code: str = "OD"
    frequency_label: str = "Once daily (OD)"
    times_per_day: int = 1
    slot_names: List[str] = field(default_factory=lambda: ["morning"])
    times: List[str] = field(default_factory=list)  # "HH:MM" 24h, sorted
    food_relation: Optional[str] = None  # "before food" | "after food" | "empty stomach" | "with food"
    as_needed: bool = False
    duration_days: Optional[int] = None
    total_quantity: Optional[float] = None
    parsed_tokens: List[str] = field(default_factory=list)
    confidence: float = 0.0  # how much of the sig we actually understood (0-1)

    def end_date(self, start: Optional[date] = None) -> Optional[date]:
        if not self.duration_days:
            return None
        start = start or date.today()
        return start + timedelta(days=self.duration_days - 1)


# ---------------------------------------------------------------- helpers

def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _from_minutes(total: int) -> str:
    total %= 24 * 60
    return f"{total // 60:02d}:{total % 60:02d}"


def format_12h(hhmm: str) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    period = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12:02d}:{m:02d} {period}"


def _parse_qty(token: str) -> Optional[float]:
    token = token.strip().replace("½", "1/2").replace("¼", "1/4")
    try:
        if "/" in token:
            return float(Fraction(token))
        return float(token)
    except (ValueError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------- patterns

_QTY = r"(?:\d+(?:\.\d+)?|\d/\d|½|¼)"
# 1-0-1, 1-1-1, 0-0-1, 1-0-0-1, ½-0-½ (also with spaces or dots as separators)
# Slot quantities are restricted to 0-4 / halves / quarters so dates like 12-05-2025 never match.
_SLOT_QTY = r"(?:1/2|1/4|½|¼|[0-4])"
_SLOT_PATTERN = re.compile(
    rf"(?<![\d/.])({_SLOT_QTY})\s*[-–]\s*({_SLOT_QTY})\s*[-–]\s*({_SLOT_QTY})(?:\s*[-–]\s*({_SLOT_QTY}))?(?![\d/])"
)

_FREQ_CODES = [
    # (regex, code, times/day, slot names, label)
    (r"\bq\.?\s*6\s*h(?:rs?|ourly)?\b|\bevery\s+6\s+hours?\b", "Q6H", 4, ["06:00", "12:00", "18:00", "00:00"], "Every 6 hours"),
    (r"\bq\.?\s*8\s*h(?:rs?|ourly)?\b|\bevery\s+8\s+hours?\b", "Q8H", 3, ["06:00", "14:00", "22:00"], "Every 8 hours"),
    (r"\bq\.?\s*12\s*h(?:rs?|ourly)?\b|\bevery\s+12\s+hours?\b", "Q12H", 2, ["08:00", "20:00"], "Every 12 hours"),
    (r"\bq\.?i\.?d\.?\b|\bqds\b|\bfour\s+times\b|\b4\s*times\b", "QID", 4, ["morning", "afternoon", "evening", "bedtime"], "Four times daily (QID)"),
    (r"\bt\.?d\.?s\.?\b|\bt\.?i\.?d\.?\b|\bthrice\b|\bthree\s+times\b|\b3\s*times\b", "TDS", 3, ["morning", "afternoon", "night"], "Three times daily (TDS)"),
    (r"\bb\.?d\.?\b|\bb\.?i\.?d\.?\b|\btwice\b|\btwo\s+times\b|\b2\s*times\b", "BD", 2, ["morning", "night"], "Twice daily (BD)"),
    (r"\bo\.?d\.?\b|\bq\.?d\.?\b|\bonce\b|\bdaily\b|\bonce\s+a\s+day\b|\b1\s*time\b", "OD", 1, ["morning"], "Once daily (OD)"),
]

_HS = re.compile(r"\bh\.?s\.?\b|\bbed\s*time\b|\bat\s+night\b|\bbefore\s+(?:sleep|bed)\b", re.I)
_SOS = re.compile(r"\bs\.?o\.?s\.?\b|\bp\.?r\.?n\.?\b|\bas\s+(?:and\s+when\s+)?needed\b|\bif\s+(?:needed|required)\b", re.I)
_STAT = re.compile(r"\bstat\b", re.I)
_AC = re.compile(r"\ba\.?c\.?\b|\bbefore\s+(?:food|meals?|breakfast|lunch|dinner)\b|\bb/?f\b", re.I)
_PC = re.compile(r"\bp\.?c\.?\b|\bafter\s+(?:food|meals?|breakfast|lunch|dinner)\b|\ba/?f\b", re.I)
_EMPTY = re.compile(r"\bempty\s+stomach\b", re.I)
_WITH_FOOD = re.compile(r"\bwith\s+(?:food|meals?|milk)\b", re.I)

_DURATION = [
    (re.compile(r"(?:x|for|×|\*)\s*(\d+)\s*(?:d\b|days?)", re.I), 1),
    (re.compile(r"(?:x|for|×|\*)\s*(\d+)\s*(?:w\b|wks?|weeks?)", re.I), 7),
    (re.compile(r"(?:x|for|×|\*)\s*(\d+)\s*(?:m\b|mon(?:th)?s?)", re.I), 30),
    (re.compile(r"(?<![\d/])(\d+)\s*/\s*7(?![\d])"), 1),  # 5/7 = 5 days
    (re.compile(r"(?<![\d/])(\d+)\s*/\s*52(?![\d])"), 7),  # 2/52 = 2 weeks
    (re.compile(r"(?<![\d/])(\d+)\s*/\s*12(?![\d])"), 30),  # 1/12 = 1 month
    (re.compile(r"(\d+)\s*(?:days?)\b", re.I), 1),
    (re.compile(r"(\d+)\s*(?:weeks?)\b", re.I), 7),
    (re.compile(r"(\d+)\s*(?:months?)\b", re.I), 30),
]
_WORD_DURATION = re.compile(r"(?:x|for)\s*(?:a|one)\s+(day|week|month)\b", re.I)

_DOSE = re.compile(rf"\b({_QTY})\s*(tabs?|tablets?|caps?|capsules?|ml|drops?|puffs?|sachets?|units?|tsp|teaspoons?)\b", re.I)


def _slot_time(slot: str, plan: DayPlan, food: Optional[str]) -> str:
    if ":" in slot:
        return slot
    meal = {
        "morning": plan.breakfast,
        "afternoon": plan.lunch,
        "evening": "17:00",
        "night": plan.dinner,
        "bedtime": plan.bedtime,
    }[slot]
    if slot in ("bedtime", "evening"):
        return meal
    minutes = _to_minutes(meal)
    if food == "before food":
        minutes -= 30
    elif food == "empty stomach":
        minutes -= 60
    elif food == "after food":
        minutes += 15
    return _from_minutes(minutes)


def parse_sig(text: str, plan: Optional[DayPlan] = None) -> Sig:
    """Parse a free-text prescription line or instruction into a :class:`Sig`."""
    plan = plan or DayPlan()
    sig = Sig()
    if not text:
        return sig
    s = " " + text.strip() + " "
    understood = 0

    # food relation (checked first because it shifts slot times)
    if _EMPTY.search(s):
        sig.food_relation = "empty stomach"
    elif _AC.search(s):
        sig.food_relation = "before food"
    elif _PC.search(s):
        sig.food_relation = "after food"
    elif _WITH_FOOD.search(s):
        sig.food_relation = "with food"
    if sig.food_relation:
        understood += 1
        sig.parsed_tokens.append(sig.food_relation)

    # dose quantity / unit
    dose_match = _DOSE.search(s)
    if dose_match:
        qty = _parse_qty(dose_match.group(1))
        if qty:
            sig.dose_qty = qty
        unit = dose_match.group(2).lower()
        sig.dose_unit = {
            "tab": "tablet", "tabs": "tablet", "tablets": "tablet", "cap": "capsule", "caps": "capsule",
            "capsules": "capsule", "drops": "drop", "puffs": "puff", "sachets": "sachet", "units": "unit",
            "teaspoon": "tsp", "teaspoons": "tsp",
        }.get(unit, unit)
        understood += 1

    hs = bool(_HS.search(s))

    # 1) slot notation 1-0-1 is the most explicit, so it wins
    slot_match = _SLOT_PATTERN.search(s)
    if slot_match:
        raw = [g for g in slot_match.groups() if g is not None]
        qtys = [_parse_qty(g) or 0.0 for g in raw]
        names = ["morning", "afternoon", "night"] if len(qtys) == 3 else ["morning", "afternoon", "evening", "night"]
        chosen = [(n, q) for n, q in zip(names, qtys) if q > 0]
        if chosen:
            sig.slot_names = [n for n, _ in chosen]
            sig.times_per_day = len(chosen)
            if not dose_match:
                sig.dose_qty = max(q for _, q in chosen)
            code = {1: "OD", 2: "BD", 3: "TDS", 4: "QID"}.get(len(chosen), f"{len(chosen)}x")
            sig.frequency_code = code
            sig.frequency_label = f"{slot_match.group(0).strip()} ({code})"
            if hs and sig.slot_names == ["night"]:
                sig.slot_names = ["bedtime"]
            understood += 2
            sig.parsed_tokens.append(slot_match.group(0).strip())
    else:
        for pattern, code, n, slots, label in _FREQ_CODES:
            if re.search(pattern, s, re.I):
                sig.frequency_code, sig.times_per_day, sig.frequency_label = code, n, label
                sig.slot_names = list(slots)
                understood += 2
                sig.parsed_tokens.append(code)
                break
        else:
            words = [n for n in ("morning", "afternoon", "evening", "night") if re.search(rf"\b{n}s?\b", s, re.I)]
            if hs:
                sig.frequency_code, sig.times_per_day = "HS", 1
                sig.frequency_label = "Once at bedtime (HS)"
                sig.slot_names = ["bedtime"]
                understood += 2
                sig.parsed_tokens.append("HS")
            elif words:  # "2 tsp in milk morning", "morning and night"
                code = {1: "OD", 2: "BD", 3: "TDS", 4: "QID"}[len(words)]
                sig.frequency_code, sig.times_per_day, sig.slot_names = code, len(words), words
                sig.frequency_label = f"{' & '.join(w.capitalize() for w in words)} ({code})"
                understood += 2
                sig.parsed_tokens.extend(words)
        if hs and sig.frequency_code == "OD":
            sig.slot_names = ["bedtime"]
            sig.frequency_label = "Once daily at bedtime (OD HS)"

    if _SOS.search(s):
        sig.as_needed = True
        sig.frequency_code = "SOS"
        sig.frequency_label = "Only when needed (SOS)"
        sig.slot_names = []
        sig.times_per_day = 0
        understood += 2
        sig.parsed_tokens.append("SOS")
    elif _STAT.search(s) and not slot_match:
        sig.frequency_code = "STAT"
        sig.frequency_label = "Single dose immediately (STAT)"
        sig.times_per_day = 1
        sig.duration_days = 1
        understood += 2

    # duration
    if sig.duration_days is None:
        for pattern, mult in _DURATION:
            m = pattern.search(s)
            if m:
                sig.duration_days = int(m.group(1)) * mult
                understood += 1
                sig.parsed_tokens.append(m.group(0).strip())
                break
        else:
            m = _WORD_DURATION.search(s)
            if m:
                sig.duration_days = {"day": 1, "week": 7, "month": 30}[m.group(1).lower()]
                understood += 1

    sig.times = sorted({_slot_time(n, plan, sig.food_relation) for n in sig.slot_names}, key=_to_minutes)
    if sig.duration_days and sig.times_per_day:
        sig.total_quantity = sig.dose_qty * sig.times_per_day * sig.duration_days
    sig.confidence = min(1.0, understood / 4)
    return sig


def describe_slot(hhmm: str, sig: Sig) -> str:
    """Human label used in the UI, e.g. ``08:15 AM — After breakfast``."""
    minutes = _to_minutes(hhmm)
    if minutes < 11 * 60:
        meal = "breakfast"
    elif minutes < 16 * 60:
        meal = "lunch"
    elif minutes < 21 * 60 + 30:
        meal = "dinner"
    else:
        return f"{format_12h(hhmm)} — Bedtime"
    if sig.food_relation == "before food":
        return f"{format_12h(hhmm)} — Before {meal}"
    if sig.food_relation == "after food":
        return f"{format_12h(hhmm)} — After {meal}"
    if sig.food_relation == "empty stomach":
        return f"{format_12h(hhmm)} — Empty stomach"
    return f"{format_12h(hhmm)} — With {meal}" if sig.food_relation == "with food" else format_12h(hhmm)
