from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database.db import Base

class AdherenceLog(Base):
    __tablename__ = "adherence_logs"
    
    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    medicine_id = Column(Integer, index=True)
    scheduled_time = Column(String)  # '09:00'
    taken_status = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
