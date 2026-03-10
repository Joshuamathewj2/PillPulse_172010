from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import json
from app.database.db import get_db
from app.models.message import Message
from app.services.llm_service import generate_async
from app.services import n8n_service
from app.models.medicine import Medicine
from app.models.adherence_log import AdherenceLog
from datetime import date

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    suggestions: List[str]

async def detect_intent(message_text: str) -> str:
    prompt = f"""
Classify the user's intent into one of these categories:
symptom_check, doctor_booking, emergency, medication_reminder.

Return only the category name. Here is the user's text:
"{message_text}"
"""
    intent_resp = await generate_async(prompt)
    intent = intent_resp.strip().lower()
    for cat in ["symptom_check", "doctor_booking", "emergency", "medication_reminder"]:
        if cat in intent:
            return cat
    return "symptom_check"

@router.post("", response_model=ChatResponse)
async def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_msg = Message(session_id=request.session_id, sender="user", content=request.message)
    db.add(user_msg)
    db.commit()
    
    # Check if there's user medicine context
    user_id = 1
    meds = db.query(Medicine).filter(Medicine.user_id == user_id).all()
    today = date.today()
    med_context = "Medication Status for today:\\n"
    for m in meds:
        logs = db.query(AdherenceLog).filter(AdherenceLog.medicine_id == m.medicine_id, AdherenceLog.user_id == user_id).all()
        taken_times = [log.scheduled_time for log in logs if log.timestamp.date() == today and log.taken_status]
        med_context += f"- {m.medicine_name}: Remaining pills: {m.remaining_pills}, Schedule: {m.schedule_times}. Taken today at: {', '.join(taken_times) if taken_times else 'Not taken yet'}\\n"
    
    # 1. Generate normal AI response
    prompt = f"""
You have access to the user's real-time medication data:
{med_context}

The user says: "{request.message}"

Respond helpfully as a healthcare AI assistant called PillPulse AI. Use the exact Medication Status provided above to answer any questions about remaining pills, missed doses, or whether they took their medications today. Also provide 3 short suggested actions or questions the user could ask next.
Format your response EXACTLY as a JSON object:
{{
   "response": "Your helpful response here",
   "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
}}
"""
    
    llm_output = await generate_async(prompt)
    if "Sorry, I am currently unable" in llm_output or "Error" in llm_output:
        # Fallback if Ollama is down completely
        return ChatResponse(
            response="I am currently experiencing connection issues to my core systems. Please try again later.",
            suggestions=["Try again", "Call emergency services if urgent"]
        )

    try:
        if "```json" in llm_output:
            json_str = llm_output.split("```json")[1].split("```")[0].strip()
        elif "```" in llm_output:
            json_str = llm_output.split("```")[1].strip()
        else:
            json_str = llm_output.strip()
        
        parsed = json.loads(json_str)
        ai_response_text = parsed.get("response", llm_output)
        suggestions = parsed.get("suggestions", ["Check symptoms", "Find doctor near me", "Medication reminder"])
    except:
        ai_response_text = llm_output
        suggestions = ["Check symptoms", "Find doctor near me", "Medication reminder"]

    ai_msg = Message(session_id=request.session_id, sender="ai", content=ai_response_text)
    db.add(ai_msg)
    db.commit()

    # 2. Intent Detection & Automation Trigger
    intent = await detect_intent(request.message)
    
    if intent == "doctor_booking":
        await n8n_service.trigger_doctor_booking(db, request.session_id, request.message)
    elif intent == "emergency":
        await n8n_service.trigger_emergency_alert(db, request.session_id, request.message, risk_level="high")
    elif intent == "medication_reminder":
        # simple parsing placeholder for medicine_name/time
        await n8n_service.trigger_medication_reminder(db, request.session_id, medicine_name="prescribed medicine")
    
    return ChatResponse(response=ai_response_text, suggestions=suggestions)
