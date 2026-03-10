from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import engine, Base
from app.models import message, symptom_session, assessment, automation_log, user, medicine, adherence_log, alert
from app.api import chat, symptoms, automations, users, medicines, adherence

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PillPulse AI", description="Healthcare AI Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(symptoms.router)
app.include_router(automations.router)
app.include_router(users.router)
app.include_router(medicines.router)
app.include_router(adherence.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to PillPulse AI Backend"}
