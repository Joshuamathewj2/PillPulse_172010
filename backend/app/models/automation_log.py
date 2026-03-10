from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database.db import Base

class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=True)
    automation_type = Column(String, index=True)
    payload = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
