"""Prescription photo -> verified medication schedule."""
from __future__ import annotations

from dataclasses import asdict
from typing import List, Optional

from . import extractors
from .drug_db import match_drug
from .extractors import ExtractionResult, RawMedicine
from .interactions import MedTiming, check_and_respace, drug_notes
from .sig_parser import DayPlan, Sig, describe_slot, format_12h, parse_sig

REVIEW_THRESHOLD = 75  # combined confidence (%) below which the patient must confirm


def _duration_label(days: Optional[int]) -> str:
    if not days:
        return "As prescribed"
    if days % 30 == 0 and days >= 30:
        n = days // 30
        return f"{n} month{'s' if n > 1 else ''}"
    if days % 7 == 0 and days >= 7:
        n = days // 7
        return f"{n} week{'s' if n > 1 else ''} ({days} days)"
    return f"{days} day{'s' if days > 1 else ''}"


def _dosage_label(sig: Sig, raw: RawMedicine) -> str:
    qty = int(sig.dose_qty) if float(sig.dose_qty).is_integer() else sig.dose_qty
    unit = sig.dose_unit if not raw.form or raw.form.lower() in ("tablet", "capsule") else raw.form.lower()
    plural = "s" if qty != 1 and unit in ("tablet", "capsule", "drop", "puff", "sachet", "unit") else ""
    label = f"{qty} {unit}{plural}"
    return f"{label} ({raw.strength})" if raw.strength else label


def build_schedule(result: ExtractionResult, plan: Optional[DayPlan] = None) -> dict:
    plan = plan or DayPlan()
    items = []
    timings: List[MedTiming] = []

    for i, raw in enumerate(result.medicines):
        match = match_drug(raw.name)
        # Matching against the bundled list is a second opinion on what the engine read.
        match_score = match.score if match else 0.0
        read_conf = raw.confidence * 100
        confidence = round(0.6 * read_conf + 0.4 * match_score, 1) if match else round(read_conf * 0.6, 1)

        sig_text = raw.sig or raw.raw_line
        sig = parse_sig(sig_text, plan)
        entry = match.entry if match else None
        generic = entry.generic if entry else ""
        drug_class = entry.drug_class if entry else ""

        needs_review = confidence < REVIEW_THRESHOLD or not match or sig.confidence < 0.5
        review_reasons = []
        if not match:
            review_reasons.append("Medicine name not found in the reference list. Check the spelling with your pharmacist.")
        elif confidence < REVIEW_THRESHOLD:
            review_reasons.append("Handwriting was hard to read. Confirm the medicine name.")
        if sig.confidence < 0.5 and not sig.as_needed:
            review_reasons.append("Dosing instructions were unclear. Confirm how often to take it.")

        key = f"m{i}"
        timings.append(MedTiming(key, raw.name, generic, drug_class, list(sig.times)))
        items.append(
            {
                "key": key,
                "raw": raw,
                "match": match,
                "sig": sig,
                "confidence": confidence,
                "needs_review": needs_review,
                "review_reasons": review_reasons,
            }
        )

    warnings = check_and_respace(timings)
    by_key = {t.key: t for t in timings}

    medicines = []
    for item in items:
        raw: RawMedicine = item["raw"]
        sig: Sig = item["sig"]
        match = item["match"]
        times = by_key[item["key"]].times
        sig.times = times  # may have been re-spaced
        entry = match.entry if match else None
        notes = drug_notes(entry.generic, entry.drug_class) if entry else []
        food = sig.food_relation.capitalize() if sig.food_relation else ""
        instructions = ". ".join(x for x in [food, *notes] if x)
        med_warnings = [asdict(w) for w in warnings[item["key"]]]
        refill = None
        if sig.duration_days and sig.duration_days > 5:
            refill = f"Day {sig.duration_days - 3} of {sig.duration_days}"

        medicines.append(
            {
                "name": entry.brand if entry and match.score >= 90 else raw.name,
                "written_as": raw.name,
                "generic": entry.generic if entry else None,
                "drug_class": entry.drug_class if entry else None,
                "typical_use": entry.use if entry else None,
                "match_score": match.score if match else 0,
                "confidence": item["confidence"],
                "status": "needs_review" if item["needs_review"] else "identified",
                "needs_review": item["needs_review"],
                "review_reasons": item["review_reasons"],
                "dosage": _dosage_label(sig, raw),
                "frequency": sig.frequency_label,
                "frequency_code": sig.frequency_code,
                "times_per_day": sig.times_per_day,
                "schedule_times": times,
                "timing": [describe_slot(t, sig) for t in times] if times else (["Only when needed"] if sig.as_needed else []),
                "duration": _duration_label(sig.duration_days),
                "duration_days": sig.duration_days,
                "total_quantity": sig.total_quantity,
                "as_needed": sig.as_needed,
                "instructions": instructions,
                "food_interaction": " ".join(w["message"] for w in med_warnings) or "",
                "warnings": med_warnings,
                "refill_reminder": refill,
                "rx_line": raw.raw_line or f"{raw.name} {raw.sig}".strip(),
                "sig_text": raw.sig,
            }
        )

    return {
        "success": True,
        "engine": result.engine,
        "raw_text": result.raw_text,
        "medicines": medicines,
        "total_found": len(medicines),
        "needs_review": any(m["needs_review"] for m in medicines),
        "day_plan": asdict(plan),
        "disclaimer": "PillPulse reads prescriptions to help you remember doses. Always confirm with your doctor or pharmacist.",
    }


def process_prescription(image_bytes: bytes, plan: Optional[DayPlan] = None) -> dict:
    result = extractors.run_chain(image_bytes)
    return build_schedule(result, plan)


__all__ = ["process_prescription", "build_schedule", "format_12h"]
