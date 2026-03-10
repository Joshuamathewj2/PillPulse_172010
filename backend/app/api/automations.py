from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid
from app.database.db import get_db
from app.services import n8n_service

router = APIRouter(prefix="/api/test-automation", tags=["Test Automation"])

class TestAutomationRequest(BaseModel):
    type: str

@router.post("")
async def test_automation(request: TestAutomationRequest, db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    
    success, err = False, ""
    if request.type == "doctor_booking":
        success, err = await n8n_service.trigger_doctor_booking(db, session_id, "Test symptom: headache", location="Test Location")
    elif request.type == "emergency":
        success, err = await n8n_service.trigger_emergency_alert(db, session_id, "Test symptom: chest pain", risk_level="high")
    elif request.type == "medication_reminder":
        success, err = await n8n_service.trigger_medication_reminder(db, session_id, medicine_name="Test Medicine", reminder_time="10:00 AM")
    else:
        raise HTTPException(status_code=400, detail="Invalid automation type")

    if success:
        return {"status": "success", "message": f"Successfully triggered {request.type} workflow. Logged in database."}
    else:
        raise HTTPException(status_code=500, detail={"error": f"Failed to trigger {request.type} workflow. n8n might be down.", "details": err})
