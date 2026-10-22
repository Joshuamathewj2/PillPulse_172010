from app.services.llm_service import extract_json, generate
import json

SYSTEM = (
    "You are a cautious symptom triage assistant. You do not diagnose. Estimate urgency conservatively "
    "and always recommend professional care when in doubt."
)

EMERGENCY_TERMS = ("chest pain", "breath", "unconscious", "faint", "seizure", "bleeding", "confusion", "stroke")
HIGH_TERMS = ("high fever", "103", "104", "severe", "blood", "stiff neck", "rash with fever", "dehydrat")


def rule_based_triage(answers: dict) -> dict:
    text = " ".join(str(v) for v in answers.values()).lower()
    if any(t in text for t in EMERGENCY_TERMS):
        return {
            "risk_level": "high",
            "possible_conditions": ["Symptoms that need urgent medical assessment"],
            "recommendations": ["Call 112 or go to the nearest emergency department now.", "Do not drive yourself if you feel faint or short of breath."],
        }
    if any(t in text for t in HIGH_TERMS):
        return {
            "risk_level": "moderate",
            "possible_conditions": ["Possible infection or condition needing a doctor's examination"],
            "recommendations": ["See a doctor within 24 hours.", "Keep hydrated and monitor your temperature.", "Seek emergency care if symptoms suddenly worsen."],
        }
    return {
        "risk_level": "low",
        "possible_conditions": ["Likely a minor, self-limiting illness"],
        "recommendations": ["Rest and stay hydrated.", "See a doctor if symptoms last more than 3 days or get worse."],
    }


def analyze_symptoms(answers: dict):
    prompt = f"""Based on these symptoms, estimate risk level, possible conditions, and recommended actions.
Symptoms provided:
{json.dumps(answers, indent=2)}

Return ONLY a JSON object exactly like:
{{"risk_level": "low" | "moderate" | "high", "possible_conditions": ["..."], "recommendations": ["..."]}}"""
    result = extract_json(generate(prompt, SYSTEM, json_mode=True))
    if result and result.get("risk_level") in ("low", "moderate", "high"):
        # Safety floor: a model can never downgrade a red-flag symptom.
        floor = rule_based_triage(answers)
        if floor["risk_level"] == "high":
            return floor
        return {
            "risk_level": result["risk_level"],
            "possible_conditions": list(result.get("possible_conditions") or [])[:5],
            "recommendations": list(result.get("recommendations") or [])[:5],
        }
    return rule_based_triage(answers)
