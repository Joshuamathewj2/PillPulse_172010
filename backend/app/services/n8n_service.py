import httpx
import json
import logging
from sqlalchemy.orm import Session
from app.models.automation_log import AutomationLog

N8N_BASE_URL = "http://localhost:5678"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_automation(db: Session, session_id: str, automation_type: str, payload: dict, success: bool, error_msg: str):
    log_entry = AutomationLog(
        session_id=session_id,
        automation_type=automation_type,
        payload={"request": payload, "success": success, "error": error_msg}
    )
    db.add(log_entry)
    db.commit()

async def _trigger_webhook(endpoint: str, data: dict, max_retries: int = 1):
    url = f"{N8N_BASE_URL}{endpoint}"
    retries = 0
    while retries <= max_retries:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data)
            
            if response.status_code == 404:
                error_body = response.json()
                if "is not registered" in error_body.get("message", ""):
                    error_msg = f"Webhook {endpoint} missing/inactive. Does it use a Manual Trigger instead of Webhook? The workflow must start with a Webhook node and be active."
                    logger.error(error_msg)
                    return False, error_msg

            response.raise_for_status()
            logger.info(f"Successfully triggered {endpoint}")
            return True, None
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP Error {e.response.status_code}: {e.response.text}"
            logger.error(f"Attempt {retries + 1} failed for n8n webhook {endpoint}: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Attempt {retries + 1} failed for n8n webhook {endpoint}: {error_msg}")
            
        retries += 1
        if retries > max_retries:
            return False, error_msg
    return False, "Retries exceeded"

async def trigger_doctor_booking(db: Session, session_id: str, symptoms: str, location: str = "Unknown"):
    payload = {
        "user_id": session_id,
        "symptoms": symptoms,
        "location": location
    }
    success, err = await _trigger_webhook("/webhook/book-doctor", payload)
    log_automation(db, session_id, "doctor_booking", payload, success, err)
    return success, err

async def trigger_emergency_alert(db: Session, session_id: str, symptoms: str, risk_level: str = "high"):
    payload = {
        "user_id": session_id,
        "symptoms": symptoms,
        "risk_level": risk_level
    }
    success, err = await _trigger_webhook("/webhook/emergency-alert", payload)
    log_automation(db, session_id, "emergency", payload, success, err)
    return success, err

async def trigger_medication_reminder(db: Session, session_id: str, medicine_name: str, reminder_time: str = "08:00 AM"):
    payload = {
        "user_id": session_id,
        "medicine_name": medicine_name,
        "reminder_time": reminder_time
    }
    success, err = await _trigger_webhook("/webhook/medication-reminder", payload)
    log_automation(db, session_id, "medication_reminder", payload, success, err)
    return success, err
