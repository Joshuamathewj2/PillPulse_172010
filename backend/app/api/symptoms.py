from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid
from app.database.db import get_db
from app.models.symptom_session import SymptomSession
from app.models.assessment import Assessment
from app.services.symptom_engine import analyze_symptoms
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter(prefix="/api/symptoms", tags=["Symptoms"])

class StartSessionResponse(BaseModel):
    session_id: str

class StepRequest(BaseModel):
    session_id: str
    step: str
    value: str

class AnalyzeRequest(BaseModel):
    session_id: str

class AnalyzeResponse(BaseModel):
    risk_level: str
    possible_conditions: List[str]
    recommendations: List[str]

@router.post("/start", response_model=StartSessionResponse)
def start_session(db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    session = SymptomSession(id=new_id, answers={})
    db.add(session)
    db.commit()
    return {"session_id": new_id}

@router.post("/step")
def submit_step(request: StepRequest, db: Session = Depends(get_db)):
    session = db.query(SymptomSession).filter(SymptomSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    answers = session.answers
    if answers is None:
        answers = {}
    answers[request.step] = request.value
    session.answers = answers
    
    flag_modified(session, "answers")
    db.commit()
    
    return {"status": "success", "session_id": request.session_id, "answers": session.answers}

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    session = db.query(SymptomSession).filter(SymptomSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    analysis_result = analyze_symptoms(session.answers or {})
    
    assessment = Assessment(
        session_id=request.session_id,
        risk_level=analysis_result.get("risk_level", "unknown"),
        possible_conditions=analysis_result.get("possible_conditions", []),
        recommendations=analysis_result.get("recommendations", [])
    )
    db.add(assessment)
    db.commit()
    
    return analysis_result
