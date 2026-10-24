import re
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.medicines import get_today_medicines, get_remaining
from app.database.db import get_db
from app.models.message import Message
from app.services import n8n_service
from app.services.llm_service import extract_json, generate_async
from app.services.prescription.drug_db import match_drug

router = APIRouter(prefix="/api/chat", tags=["Chat"])

SYSTEM_PROMPT = """You are PillPulse AI, a careful medication-adherence assistant for patients in India.
- Use the patient's medication data provided to answer questions about their schedule, doses and refills.
- Give general, conservative health information only. Never diagnose, never change a prescribed dose,
  never tell someone to stop a medicine. For anything beyond general information, advise speaking to
  their doctor or pharmacist.
- If the user describes an emergency (chest pain, trouble breathing, stroke signs, fainting, severe
  bleeding, overdose, thoughts of self-harm), set emergency=true and tell them to call 112 now.
- Be brief: at most 4 short sentences or a short list.
Reply as JSON: {"response": string, "suggestions": [3 short follow-up questions], "emergency": boolean}"""

# Deterministic red flags: these never wait on (or depend on) a model.
RED_FLAGS = re.compile(
    r"chest pain|chest tightness|can'?t breathe|cannot breathe|difficulty breathing|short(ness)? of breath|"
    r"unconscious|fainted|passed out|seizure|fits|stroke|face droop|slurred speech|severe bleeding|"
    r"vomiting blood|coughing blood|overdose|took too many|suicid|kill myself|end my life|self[- ]harm|"
    r"anaphyla|throat swelling|swollen tongue",
    re.I,
)

DEFAULT_SUGGESTIONS = ["When is my next dose?", "What is each medicine for?", "Which doses did I miss today?"]


class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str]
    emergency: bool = False
    source: str = "rule-based"


def _fmt12(hhmm: str) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def medication_context(db: Session, user_id: Optional[str]) -> tuple[str, list, list]:
    if not user_id:
        return "No patient profile linked; no medication data.", [], []
    today = get_today_medicines(user_id, db)
    remaining = get_remaining(user_id, db)
    if not today and not remaining:
        return "The patient has no medicines added yet.", today, remaining
    lines = ["Today's doses:"]
    for d in today:
        state = "taken" if d["taken"] else ("OVERDUE" if d["overdue"] else "upcoming")
        lines.append(f"- {d['medicine_name']} at {_fmt12(d['scheduled_time'])}: {state}")
    lines.append("Stock:")
    for r in remaining:
        lines.append(f"- {r['medicine_name']}: {r['remaining_pills']} left (~{r['remaining_days']} days)")
    return "\n".join(lines), today, remaining


def rule_based_reply(text: str, today: list, remaining: list) -> tuple[str, List[str]]:
    t = text.lower()
    if re.search(r"next dose|when.*(take|dose)|what time", t):
        upcoming = [d for d in today if not d["taken"] and not d["overdue"]]
        if upcoming:
            d = upcoming[0]
            return f"Your next dose is {d['medicine_name']} at {_fmt12(d['scheduled_time'])}.", DEFAULT_SUGGESTIONS
        if today:
            return "You have no more doses scheduled for today.", DEFAULT_SUGGESTIONS
        return "You have no medicines scheduled yet. Upload a prescription or add a medicine to get started.", [
            "How do I upload a prescription?", "Add a medicine", "Check my symptoms"]
    if re.search(r"miss|forgot|skipp|did i take|taken today", t):
        overdue = [d for d in today if d["overdue"]]
        taken = [d for d in today if d["taken"]]
        if not today:
            return "There are no doses scheduled for today.", DEFAULT_SUGGESTIONS
        parts = []
        if taken:
            parts.append("Taken today: " + ", ".join(f"{d['medicine_name']} ({_fmt12(d['scheduled_time'])})" for d in taken) + ".")
        if overdue:
            parts.append("Not yet marked as taken: " + ", ".join(f"{d['medicine_name']} ({_fmt12(d['scheduled_time'])})" for d in overdue) + ".")
            parts.append("If you missed a dose, take it when you remember unless it's almost time for the next one. Never double up. Your pharmacist can advise for your specific medicine.")
        else:
            parts.append("You're on track: nothing overdue.")
        return " ".join(parts), DEFAULT_SUGGESTIONS
    if re.search(r"refill|run out|left|remaining|stock", t):
        if not remaining:
            return "No medicines are being tracked yet.", DEFAULT_SUGGESTIONS
        low = sorted(remaining, key=lambda r: r["remaining_days"])
        msg = "; ".join(f"{r['medicine_name']}: {r['remaining_pills']} left (~{r['remaining_days']:g} days)" for r in low[:5])
        return f"Stock: {msg}.", DEFAULT_SUGGESTIONS
    m = re.search(r"(?:what is|what's|whats|use of|used for|tell me about)\s+([a-z0-9 \-]+?)(?:\s+(?:for|used))?\??$", t)
    if m:
        hit = match_drug(m.group(1))
        if hit:
            e = hit.entry
            return (
                f"{e.brand} contains {e.generic} ({e.drug_class.replace('-', ' ')}). It is commonly used for: {e.use.lower()}. "
                "Take it exactly as your doctor prescribed.",
                [f"Side effects of {e.generic}?", "When is my next dose?", "Can I take it with food?"],
            )
    if re.search(r"my (medicines|meds|medications)|list", t) and remaining:
        return "You're taking: " + ", ".join(r["medicine_name"] for r in remaining) + ".", DEFAULT_SUGGESTIONS
    return (
        "I can help with your medication schedule, missed doses, refills and what your medicines are for. "
        "For symptoms, try the Symptom Checker. (AI answers are offline right now, so I'm answering from your saved data.)",
        DEFAULT_SUGGESTIONS,
    )


@router.post("", response_model=ChatResponse)
async def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    db.add(Message(session_id=request.session_id, sender="user", content=request.message))
    db.commit()

    context, today, remaining = medication_context(db, request.user_id)

    if RED_FLAGS.search(request.message):
        reply = ChatResponse(
            response="This could be a medical emergency. Call 112 (or your local emergency number) now, or go to the nearest hospital. Don't wait for an online answer.",
            suggestions=["Find nearest hospital", "Notify my caregiver", "Call 112"],
            emergency=True,
            source="safety-rule",
        )
        await n8n_service.trigger_emergency_alert(db, request.session_id, request.message, risk_level="high")
    else:
        history = (
            db.query(Message).filter(Message.session_id == request.session_id).order_by(Message.id.desc()).limit(8).all()
        )
        transcript = "\n".join(f"{m.sender}: {m.content}" for m in reversed(history))
        prompt = f"Patient medication data:\n{context}\n\nConversation so far:\n{transcript}\n\nReply to the last user message."
        parsed = extract_json(await generate_async(prompt, SYSTEM_PROMPT, json_mode=True))
        if parsed and parsed.get("response"):
            reply = ChatResponse(
                response=str(parsed["response"]),
                suggestions=[str(s) for s in (parsed.get("suggestions") or DEFAULT_SUGGESTIONS)][:3],
                emergency=bool(parsed.get("emergency")),
                source="llm",
            )
        else:
            text, suggestions = rule_based_reply(request.message, today, remaining)
            reply = ChatResponse(response=text, suggestions=suggestions, source="rule-based")

    db.add(Message(session_id=request.session_id, sender="ai", content=reply.response))
    db.commit()
    return reply
