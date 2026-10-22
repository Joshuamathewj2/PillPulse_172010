import io

import cv2
import numpy as np

from app.services.prescription import extractors
from app.services.prescription.extractors import ExtractionResult, RawMedicine, TesseractEngine


def _png() -> bytes:
    img = np.full((60, 120, 3), 255, np.uint8)
    cv2.putText(img, "Rx", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    return cv2.imencode(".png", img)[1].tobytes()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["prescription_engines"] == []


def test_predict_without_engine_is_honest(client):
    r = client.post("/api/predict", files={"image": ("rx.png", _png(), "image/png")})
    assert r.status_code == 503
    assert "No prescription reader" in r.json()["error"]


def test_predict_rejects_garbage(client):
    r = client.post("/api/predict", files={"image": ("rx.png", b"not an image", "image/png")})
    assert r.status_code in (400, 503)


def test_predict_builds_verified_schedule(client, monkeypatch):
    fake = ExtractionResult(
        engine="stub",
        raw_text="Tab Augmentin 625 1-0-1 PC x 5 days\nTab Digene 1-0-1 PC\nTab Zqxv OD",
        medicines=[
            RawMedicine("Augmentin", "1-0-1 PC x 5 days", "tablet", "625 mg", "Tab Augmentin 625 1-0-1 PC x 5 days", 0.95),
            RawMedicine("Ciplox", "1-0-1 PC x 5 days", "tablet", "500 mg", "Tab Ciplox 500 1-0-1 PC x 5 days", 0.9),
            RawMedicine("Digene", "1-0-1 PC", "tablet", "", "Tab Digene 1-0-1 PC", 0.9),
            RawMedicine("Zqxv", "OD", "tablet", "", "Tab Zqxv OD", 0.4),
        ],
    )
    monkeypatch.setattr(extractors, "run_chain", lambda data: fake)
    r = client.post("/api/predict", files={"image": ("rx.png", _png(), "image/png")}, data={"breakfast": "09:00"})
    body = r.json()
    assert r.status_code == 200 and body["engine"] == "stub" and body["total_found"] == 4
    aug, cipro, digene, unknown = body["medicines"]

    assert aug["generic"].startswith("Amoxicillin")
    assert aug["schedule_times"] == ["09:15", "20:15"]  # patient's own breakfast time, after food
    assert aug["duration_days"] == 5 and aug["total_quantity"] == 10
    assert aug["status"] == "identified"

    # Antacid + fluoroquinolone: warned AND automatically spaced apart.
    assert any(w["adjusted"] for w in cipro["warnings"])
    assert not set(cipro["schedule_times"]) & set(digene["schedule_times"])

    assert unknown["needs_review"] and unknown["generic"] is None
    assert body["needs_review"] is True


def test_tesseract_text_parser():
    result = TesseractEngine.parse_text("Rx\nTab. Pan 40 1-0-0 AC x 10 days\nCap Omez 20 BD\nsignature")
    assert [m.name for m in result.medicines] == ["Pan 40", "Omez"]
    assert all(m.confidence <= 0.85 for m in result.medicines)


def test_patient_caregiver_flow(client):
    assert client.post("/api/register-patient", json={"patientCode": "JOSH-4521", "name": "Josh", "token": "dummy-token"}).json()["success"]
    r = client.post("/api/register-caregiver", json={"patientCode": "JOSH-4521", "caregiverName": "Mom", "relation": "Family Member"})
    assert r.json() == {"success": True, "patientName": "Josh"}
    assert client.post("/api/register-caregiver", json={"patientCode": "NOPE-0000", "caregiverName": "X"}).status_code == 404

    client.post("/api/log-dose", json={"patientCode": "JOSH-4521", "medicineName": "Dolo 650", "timingSlot": "08:00 AM", "status": "skipped"})
    status = client.get("/api/patient-status", params={"patientCode": "josh-4521"}).json()
    assert status["patientName"] == "Josh" and status["doseLog"][-1]["status"] == "skipped"
    assert status["caregivers"] == [{"name": "Mom", "relation": "Family Member"}]

    notify = client.post("/api/notify-caregiver", json={"patientCode": "JOSH-4521", "medicineName": "Dolo 650", "timingSlot": "08:00 AM", "skipCount": 2}).json()
    assert notify["success"] and notify["caregivers"] == 1 and notify["push_configured"] is False


def test_medicines_and_adherence(client):
    uid = "TEST-1111"
    added = client.post(
        "/medicines/add",
        json={"user_id": uid, "medicine_name": "Dolo 650", "schedule_times": ["00:00 AM", "23:59"], "duration_days": 5},
    ).json()
    assert added["schedule_times"] == "00:00,23:59" and added["total_pills"] == 10

    # Re-adding updates instead of duplicating.
    client.post("/medicines/add", json={"user_id": uid, "medicine_name": "Dolo 650", "schedule_times": "00:00,23:59", "duration_days": 5})
    assert len(client.get("/medicines/list", params={"user_id": uid}).json()) == 1

    today = client.get("/medicines/today", params={"user_id": uid}).json()
    assert [d["scheduled_time"] for d in today] == ["00:00", "23:59"]
    mid = today[0]["medicine_id"]

    ok = client.post("/medicines/confirm-dose", json={"user_id": uid, "medicine_id": mid, "scheduled_time": "12:00 AM"}).json()
    assert ok["remaining_pills"] == 9
    again = client.post("/medicines/confirm-dose", json={"user_id": uid, "medicine_id": mid, "scheduled_time": "00:00"}).json()
    assert again["message"] == "Dose already recorded" and again["remaining_pills"] == 9

    score = client.get("/adherence/score", params={"user_id": uid}).json()
    assert score["has_data"] and score["taken"] == 1 and score["score"] == 100.0  # 23:59 slot not due yet

    week = client.get("/adherence/weekly", params={"user_id": uid}).json()
    assert len(week) == 7 and week[-1]["taken"] == 1
    assert client.get("/adherence/score", params={"user_id": "EMPTY-0000"}).json()["score"] is None

    # A "taken" tap on a reminder notification counts too.
    client.post("/api/register-patient", json={"patientCode": uid, "name": "T"})
    client.post("/api/log-dose", json={"patientCode": uid, "medicineName": "Dolo 650", "timingSlot": "11:59 PM", "status": "taken"})
    assert client.get("/adherence/score", params={"user_id": uid}).json()["taken"] == 2


def test_chat_rule_based_uses_real_data(client):
    uid = "CHAT-2222"
    client.post("/medicines/add", json={"user_id": uid, "medicine_name": "Pan 40", "schedule_times": "23:58"})
    r = client.post("/api/chat", json={"session_id": "s1", "message": "When is my next dose?", "user_id": uid}).json()
    assert r["source"] == "rule-based" and "Pan 40" in r["response"] and "11:58 PM" in r["response"]

    r = client.post("/api/chat", json={"session_id": "s1", "message": "what is augmentin used for?", "user_id": uid}).json()
    assert "Amoxicillin" in r["response"]


def test_chat_red_flags_skip_the_model(client):
    r = client.post("/api/chat", json={"session_id": "s2", "message": "I have crushing chest pain"}).json()
    assert r["emergency"] is True and "112" in r["response"] and r["source"] == "safety-rule"


def test_symptoms_flow_with_safety_floor(client):
    sid = client.post("/api/symptoms/start").json()["session_id"]
    client.post("/api/symptoms/step", json={"session_id": sid, "step": "main", "value": "shortness of breath"})
    result = client.post("/api/symptoms/analyze", json={"session_id": sid}).json()
    assert result["risk_level"] == "high"
