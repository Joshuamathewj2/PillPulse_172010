from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database.db import Base

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("symptom_sessions.id"))
    risk_level = Column(String)
    possible_conditions = Column(JSON)
    recommendations = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
