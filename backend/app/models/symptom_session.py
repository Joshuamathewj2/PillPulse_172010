from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database.db import Base

class SymptomSession(Base):
    __tablename__ = "symptom_sessions"

    id = Column(String, primary_key=True, index=True)
    answers = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
