"""Known timing interactions and automatic dose re-spacing.

The rules here are about *timing* (things that must not be swallowed together)
plus a few well-known combinations worth flagging. It is a safety net, not a
substitute for a pharmacist: every warning tells the patient to confirm.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

# Each side is matched against a drug's generic name and class (case-insensitive substring).
_ANTACID = ["antacid", "aluminium hydroxide", "magnesium hydroxide", "sodium bicarbonate", "sucralfate"]
_CALCIUM = ["calcium-supplement", "calcium carbonate", "calcium citrate"]
_IRON = ["iron-supplement", "ferrous", "ferric"]
_ZINC = ["zinc"]
_QUINOLONE = ["fluoroquinolone"]
_TETRACYCLINE = ["tetracycline"]
_THYROID = ["levothyroxine"]


@dataclass(frozen=True)
class Rule:
    a: Sequence[str]
    b: Sequence[str]
    min_gap_hours: float
    severity: str  # "info" | "caution" | "serious"
    message: str


RULES: List[Rule] = [
    Rule(_ANTACID, _QUINOLONE, 2, "caution", "Antacids block absorption of fluoroquinolone antibiotics. Keep them at least 2 hours apart."),
    Rule(_ANTACID, _TETRACYCLINE, 2, "caution", "Antacids block absorption of tetracycline antibiotics. Keep them at least 2 hours apart."),
    Rule(_ANTACID, _THYROID, 4, "caution", "Antacids reduce levothyroxine absorption. Keep them at least 4 hours apart."),
    Rule(_ANTACID, _IRON, 2, "caution", "Antacids reduce iron absorption. Keep them at least 2 hours apart."),
    Rule(_ANTACID, ["azithromycin"], 2, "info", "Antacids can lower azithromycin levels. Keep them at least 2 hours apart."),
    Rule(_ANTACID, ["digoxin"], 2, "caution", "Antacids reduce digoxin absorption. Keep them at least 2 hours apart."),
    Rule(_ANTACID, ["hydroxychloroquine", "chloroquine"], 4, "caution", "Antacids reduce (hydroxy)chloroquine absorption. Keep them 4 hours apart."),
    Rule(_CALCIUM, _QUINOLONE, 2, "caution", "Calcium blocks absorption of fluoroquinolone antibiotics. Keep them at least 2 hours apart."),
    Rule(_CALCIUM, _TETRACYCLINE, 2, "caution", "Calcium blocks absorption of tetracycline antibiotics. Keep them at least 2 hours apart."),
    Rule(_CALCIUM, _THYROID, 4, "caution", "Calcium reduces levothyroxine absorption. Keep them at least 4 hours apart."),
    Rule(_CALCIUM, _IRON, 2, "info", "Calcium and iron compete for absorption. Keep them at least 2 hours apart."),
    Rule(_IRON, _QUINOLONE, 2, "caution", "Iron blocks absorption of fluoroquinolone antibiotics. Keep them at least 2 hours apart."),
    Rule(_IRON, _TETRACYCLINE, 2, "caution", "Iron blocks absorption of tetracycline antibiotics. Keep them at least 2 hours apart."),
    Rule(_IRON, _THYROID, 4, "caution", "Iron reduces levothyroxine absorption. Keep them at least 4 hours apart."),
    Rule(_ZINC, _QUINOLONE, 2, "caution", "Zinc blocks absorption of fluoroquinolone antibiotics. Keep them at least 2 hours apart."),
    Rule(_ZINC, _TETRACYCLINE, 2, "caution", "Zinc blocks absorption of tetracycline antibiotics. Keep them at least 2 hours apart."),
    Rule(["proton-pump-inhibitor"], _THYROID, 0, "info", "Acid reducers can lower levothyroxine absorption over time; your doctor may check thyroid levels."),
    Rule(["proton-pump-inhibitor"], ["itraconazole"], 0, "caution", "Acid reducers lower itraconazole absorption. Take itraconazole with food."),
    Rule(["warfarin", "acenocoumarol"], ["nsaid"], 0, "serious", "Blood thinner + painkiller (NSAID) raises bleeding risk. Confirm with your doctor before taking both."),
    Rule(["warfarin", "acenocoumarol"], ["aspirin"], 0, "serious", "Blood thinner + aspirin raises bleeding risk. Confirm this combination with your doctor."),
    Rule(["warfarin", "acenocoumarol"], ["metronidazole", "fluconazole", "ciprofloxacin", "levofloxacin", "sulfamethoxazole"], 0, "serious", "This antibiotic/antifungal can strongly raise blood-thinner levels. Your INR may need checking."),
    Rule(["clopidogrel"], ["omeprazole", "esomeprazole"], 0, "caution", "Omeprazole/esomeprazole can weaken clopidogrel. Pantoprazole is usually preferred - ask your doctor."),
    Rule(["clopidogrel", "aspirin"], ["nsaid"], 0, "caution", "Antiplatelet + NSAID raises stomach-bleeding risk."),
    Rule(["ace-inhibitor", "arb-antihypertensive"], ["potassium-sparing-diuretic"], 0, "caution", "This combination can raise potassium. Your doctor may monitor blood potassium."),
    Rule(["ace-inhibitor", "arb-antihypertensive"], ["nsaid"], 0, "caution", "NSAIDs can reduce blood-pressure control and strain the kidneys with this medicine."),
    Rule(["ssri-antidepressant", "snri-antidepressant"], ["tramadol"], 0, "serious", "Antidepressant + tramadol can cause serotonin syndrome or seizures. Confirm with your doctor."),
    Rule(["ssri-antidepressant", "snri-antidepressant"], ["sumatriptan"], 0, "caution", "Antidepressant + triptan has a small serotonin-syndrome risk. Report agitation, fever or tremor."),
    Rule(["ssri-antidepressant", "snri-antidepressant"], ["nsaid", "aspirin"], 0, "caution", "Antidepressant + NSAID/aspirin raises bleeding risk."),
    Rule(["benzodiazepine", "sedative-hypnotic"], ["opioid-analgesic", "tramadol"], 0, "serious", "Sedative + opioid painkiller can dangerously slow breathing. Do not combine without medical advice."),
    Rule(["benzodiazepine"], ["sedative-hypnotic", "antipsychotic"], 0, "caution", "Two sedating medicines together increase drowsiness and fall risk."),
    Rule(["metformin"], ["furosemide", "torsemide"], 0, "info", "Loop diuretics can affect blood sugar; keep monitoring sugars."),
    Rule(["sulfonylurea-antidiabetic"], ["fluconazole"], 0, "caution", "Fluconazole can raise glimepiride/gliclazide levels and cause low sugar."),
    Rule(["statin"], ["clarithromycin"], 0, "serious", "Clarithromycin raises statin levels (muscle damage risk). Your doctor may pause the statin."),
    Rule(["statin"], ["fenofibrate"], 0, "info", "Statin + fibrate slightly raises muscle side-effect risk. Report unexplained muscle pain."),
    Rule(["digoxin"], ["clarithromycin", "azithromycin"], 0, "caution", "Macrolide antibiotics can raise digoxin levels."),
    Rule(["methotrexate"], ["sulfamethoxazole"], 0, "serious", "Methotrexate + co-trimoxazole can cause serious blood toxicity."),
    Rule(["methotrexate"], ["nsaid"], 0, "caution", "NSAIDs can raise methotrexate levels."),
    Rule(["lithium"], ["nsaid", "ace-inhibitor", "arb-antihypertensive", "thiazide-diuretic"], 0, "serious", "This medicine can raise lithium to toxic levels. Lithium levels need checking."),
    Rule(["pde5-inhibitor"], ["nitrate"], 0, "serious", "Sildenafil/tadalafil with nitrates can cause a dangerous drop in blood pressure. Never combine."),
]

# Single-drug advice surfaced next to the medicine (food / lifestyle notes).
DRUG_NOTES: List[tuple[Sequence[str], str]] = [
    (["metronidazole", "tinidazole", "ornidazole"], "Avoid alcohol during the course and for 48 hours after."),
    (["levothyroxine"], "Take on an empty stomach, 30-60 minutes before breakfast."),
    (["fluoroquinolone", "tetracycline"], "Avoid milk, curd and calcium/iron supplements within 2 hours of a dose."),
    (["doxycycline"], "Take with a full glass of water and stay upright for 30 minutes."),
    (["iron-supplement"], "Vitamin C (e.g. orange juice) helps absorption; tea and coffee reduce it."),
    (["statin"], "Report unexplained muscle pain or weakness."),
    (["warfarin", "acenocoumarol"], "Keep leafy-green intake consistent and do not start new painkillers without advice."),
    (["metformin"], "Take with or after meals to reduce stomach upset."),
    (["nsaid"], "Take after food to protect the stomach."),
    (["corticosteroid"], "Take after breakfast; do not stop suddenly after long courses."),
    (["benzodiazepine", "sedative-hypnotic", "antihistamine"], "May cause drowsiness. Avoid driving if affected; avoid alcohol."),
]


def drug_notes(generic: str, drug_class: str) -> List[str]:
    hay = f"{generic} {drug_class}".lower()
    return [note for terms, note in DRUG_NOTES if any(t in hay for t in terms)]


@dataclass
class MedTiming:
    key: str  # unique id within the prescription
    name: str
    generic: str
    drug_class: str
    times: List[str]  # "HH:MM"
    movable: bool = True


@dataclass
class Warning_:
    severity: str
    message: str
    between: List[str]
    adjusted: bool = False


def _matches(med: MedTiming, terms: Sequence[str]) -> bool:
    hay = f"{med.generic} {med.drug_class} {med.name}".lower()
    return any(t in hay for t in terms)


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _hhmm(total: int) -> str:
    total %= 1440
    return f"{total // 60:02d}:{total % 60:02d}"


def _circular_gap(a: int, b: int) -> int:
    d = abs(a - b) % 1440
    return min(d, 1440 - d)


def _respace(fixed: MedTiming, moving: MedTiming, gap_min: int, latest: int = 23 * 60) -> bool:
    """Shift conflicting doses of ``moving`` later (in 30 min steps) until every dose
    sits ``gap_min`` away from ``fixed``. Returns True if something moved."""
    fixed_m = [_minutes(t) for t in fixed.times]
    changed = False
    new_times = []
    for t in moving.times:
        m = _minutes(t)
        original = m
        steps = 0
        while any(_circular_gap(m, f) < gap_min for f in fixed_m) and steps < 24:
            m += 30
            steps += 1
        if m > latest or steps >= 24:  # could not push later: try earlier instead
            m = original
            steps = 0
            while any(_circular_gap(m, f) < gap_min for f in fixed_m) and steps < 24:
                m -= 30
                steps += 1
        if m != original:
            changed = True
        new_times.append(_hhmm(m))
    moving.times = sorted(set(new_times), key=_minutes)
    return changed


def check_and_respace(meds: List[MedTiming]) -> Dict[str, List[Warning_]]:
    """Apply every rule; mutate ``meds`` times in place to honour minimum gaps.

    Returns warnings keyed by ``MedTiming.key`` (each warning is attached to both drugs).
    """
    out: Dict[str, List[Warning_]] = {m.key: [] for m in meds}
    for rule in RULES:
        for a in meds:
            if not _matches(a, rule.a):
                continue
            for b in meds:
                if a is b or not _matches(b, rule.b):
                    continue
                adjusted = False
                if rule.min_gap_hours and a.times and b.times:
                    # Move the "absorption victim" (b side, e.g. the antibiotic) away from the binder.
                    target = b if b.movable else a
                    other = a if target is b else b
                    adjusted = _respace(other, target, int(rule.min_gap_hours * 60))
                w = Warning_(rule.severity, rule.message, [a.name, b.name], adjusted)
                out[a.key].append(w)
                out[b.key].append(w)
    return out


def pairwise_min_gap(a: MedTiming, b: MedTiming) -> Optional[int]:
    if not a.times or not b.times:
        return None
    return min(_circular_gap(_minutes(x), _minutes(y)) for x in a.times for y in b.times)
