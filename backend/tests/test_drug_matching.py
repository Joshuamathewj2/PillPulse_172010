from app.services.prescription.drug_db import find_drug_mentions, match_drug, normalize_name
from app.services.prescription.interactions import MedTiming, check_and_respace, pairwise_min_gap


def test_normalize_strips_form_and_strength():
    assert normalize_name("Tab. Dolo 650 mg") == "dolo 650"  # unit dropped, brand number kept
    assert normalize_name("Cap Omez 20mg") == "omez 20"
    assert match_drug("Tab. Dolo 650 mg").entry.brand == "Dolo 650"
    assert match_drug("Cap Omez 20mg").entry.generic == "Omeprazole"
    assert match_drug("Finax 1mg").entry.generic == "Finasteride"


def test_exact_brand_and_generic():
    m = match_drug("Augmentin")
    assert m.entry.generic.startswith("Amoxicillin") and m.score == 100
    assert match_drug("pantoprazole").matched_on == "generic"


def test_misspelled_handwriting():
    assert match_drug("Azithrall").entry.generic == "Azithromycin"
    assert match_drug("Pantocld").entry.generic == "Pantoprazole"
    assert match_drug("Montair L C").entry.generic.startswith("Montelukast")
    assert match_drug("Thyronrm").entry.generic == "Levothyroxine"


def test_unknown_names_are_not_forced():
    hit = match_drug("Hairbless")
    assert hit is None or hit.score < 90
    assert match_drug("xyzzy") is None
    assert match_drug("ab") is None


def test_find_mentions_in_ocr_text():
    text = "Dr. Sharma MBBS\nRx\nTab Augmentin 625 1-0-1 x 5 days\nTab Pan 40 1-0-0 AC\nReview after 1 week"
    names = [m.entry.brand for _, m in find_drug_mentions(text)]
    assert "Augmentin" in names and "Pan 40" in names
    assert len(names) == 2


def _med(key, generic, cls, times):
    return MedTiming(key, generic, generic, cls, times)


def test_antacid_respaces_antibiotic():
    antacid = _med("a", "Aluminium hydroxide", "antacid", ["08:15", "20:15"])
    cipro = _med("c", "Ciprofloxacin", "fluoroquinolone-antibiotic", ["08:15", "20:15"])
    warnings = check_and_respace([antacid, cipro])
    assert warnings["c"] and warnings["c"][0].adjusted
    assert pairwise_min_gap(antacid, cipro) >= 120


def test_levothyroxine_four_hour_gap():
    thyro = _med("t", "Levothyroxine", "thyroid-hormone", ["07:00"])
    calcium = _med("k", "Calcium carbonate + Vitamin D3", "calcium-supplement", ["08:15"])
    check_and_respace([calcium, thyro])
    assert pairwise_min_gap(calcium, thyro) >= 240


def test_serious_warning_without_respacing():
    warf = _med("w", "Warfarin", "anticoagulant", ["20:00"])
    ibu = _med("i", "Ibuprofen", "nsaid", ["08:00"])
    w = check_and_respace([warf, ibu])
    assert w["w"][0].severity == "serious" and not w["w"][0].adjusted


def test_no_false_alarm():
    a = _med("a", "Paracetamol", "analgesic-antipyretic", ["08:00"])
    b = _med("b", "Cetirizine", "antihistamine", ["20:00"])
    assert check_and_respace([a, b]) == {"a": [], "b": []}
