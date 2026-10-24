import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import engine, Base
from app.models import message, symptom_session, assessment, automation_log, user, medicine, adherence_log, alert, patient  # noqa: F401 (register tables)
from app.api import chat, symptoms, automations, users, medicines, adherence, patients, prescription
from app.services import fcm, llm_service
from app.services.prescription import extractors

logging.basicConfig(level=logging.INFO)

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PillPulse AI", description="Prescription-to-schedule medication adherence API", version="2.0.0")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prescription.router)
app.include_router(patients.router)
app.include_router(chat.router)
app.include_router(symptoms.router)
app.include_router(automations.router)
app.include_router(users.router)
app.include_router(medicines.router)
app.include_router(adherence.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to PillPulse AI Backend", "docs": "/docs"}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "prescription_engines": extractors.available_engines(),
        "llm_providers": llm_service.available_providers(),
        "push_notifications": fcm.is_configured(),
    }
