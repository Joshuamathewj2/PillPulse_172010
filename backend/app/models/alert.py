from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.db import Base

class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    alert_type = Column(String)  # 'missed_dose', 'refill'
    message = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
