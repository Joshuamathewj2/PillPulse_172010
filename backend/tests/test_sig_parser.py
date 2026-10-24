import pytest

from app.services.prescription.sig_parser import DayPlan, describe_slot, format_12h, parse_sig


@pytest.mark.parametrize(
    "text, code, times",
    [
        ("1-0-1", "BD", ["08:00", "20:00"]),
        ("1-1-1", "TDS", ["08:00", "13:00", "20:00"]),
        ("0-0-1", "OD", ["20:00"]),
        ("1-0-0", "OD", ["08:00"]),
        ("0-1-0", "OD", ["13:00"]),
        ("1-1-1-1", "QID", ["08:00", "13:00", "17:00", "20:00"]),
        ("BD", "BD", ["08:00", "20:00"]),
        ("b.d.", "BD", ["08:00", "20:00"]),
        ("TDS", "TDS", ["08:00", "13:00", "20:00"]),
        ("tid", "TDS", ["08:00", "13:00", "20:00"]),
        ("OD", "OD", ["08:00"]),
        ("QID", "QID", ["08:00", "13:00", "17:00", "22:00"]),
        ("twice daily", "BD", ["08:00", "20:00"]),
        ("three times a day", "TDS", ["08:00", "13:00", "20:00"]),
        ("once a day", "OD", ["08:00"]),
        ("q8h", "Q8H", ["06:00", "14:00", "22:00"]),
        ("every 12 hours", "Q12H", ["08:00", "20:00"]),
        ("q6h", "Q6H", ["00:00", "06:00", "12:00", "18:00"]),
    ],
)
def test_frequencies(text, code, times):
    sig = parse_sig(text)
    assert sig.frequency_code == code
    assert sig.times == times


def test_full_indian_line():
    sig = parse_sig("Tab Dolo 650 1-0-1 x 5 days AC")
    assert sig.frequency_code == "BD"
    assert sig.food_relation == "before food"
    assert sig.times == ["07:30", "19:30"]  # 30 min before breakfast and dinner
    assert sig.duration_days == 5
    assert sig.total_quantity == 10
    assert sig.confidence >= 0.75


def test_after_food_shifts_later():
    assert parse_sig("1-0-1 PC").times == ["08:15", "20:15"]


def test_hs_bedtime():
    sig = parse_sig("0-0-1 HS x 7 days")
    assert sig.times == ["22:00"]
    assert sig.duration_days == 7
    assert parse_sig("Tab Thyronorm OD HS").times == ["22:00"]
    assert parse_sig("HS").frequency_code == "HS"


def test_sos_has_no_fixed_times():
    sig = parse_sig("Tab Dolo 650 SOS for fever")
    assert sig.as_needed and sig.times == [] and sig.times_per_day == 0


def test_stat():
    sig = parse_sig("Inj Dexona STAT")
    assert sig.frequency_code == "STAT" and sig.duration_days == 1


@pytest.mark.parametrize(
    "text, days",
    [
        ("BD x 5 days", 5),
        ("BD for 10 days", 10),
        ("OD x 1 week", 7),
        ("OD for 2 weeks", 14),
        ("OD x 1 month", 30),
        ("BD 5/7", 5),
        ("OD 2/52", 14),
        ("OD 1/12", 30),
        ("BD for a week", 7),
        ("TDS 3 days", 3),
        ("1-0-1 x5d", 5),
    ],
)
def test_durations(text, days):
    assert parse_sig(text).duration_days == days


def test_dates_are_not_dose_patterns():
    sig = parse_sig("Date: 12-05-2025")
    assert sig.frequency_code != "TDS" and sig.confidence < 0.5


def test_strength_not_mistaken_for_slots():
    assert parse_sig("Dolo 650 BD").frequency_code == "BD"


def test_half_tablet():
    sig = parse_sig("½-0-½ x 10 days")
    assert sig.dose_qty == 0.5
    assert sig.total_quantity == 10


def test_explicit_dose_and_unit():
    sig = parse_sig("Syp Ascoril 10 ml TDS x 5 days")
    assert sig.dose_qty == 10 and sig.dose_unit == "ml" and sig.total_quantity == 150


def test_word_slots():
    sig = parse_sig("2 tsp with milk morning")
    assert sig.times == ["08:00"] and sig.dose_qty == 2 and sig.dose_unit == "tsp"
    assert parse_sig("morning and night").frequency_code == "BD"


def test_custom_day_plan():
    plan = DayPlan(breakfast="09:30", dinner="21:30")
    assert parse_sig("1-0-1", plan).times == ["09:30", "21:30"]


def test_empty_stomach():
    assert parse_sig("OD empty stomach").times == ["07:00"]


def test_unparseable_has_low_confidence():
    assert parse_sig("as discussed").confidence == 0


def test_labels():
    assert format_12h("00:00") == "12:00 AM"
    assert format_12h("13:05") == "01:05 PM"
    sig = parse_sig("1-0-1 PC")
    assert describe_slot("08:15", sig) == "08:15 AM — After breakfast"
    assert describe_slot("22:00", sig) == "10:00 PM — Bedtime"
