from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database.db import Base

class Medicine(Base):
    __tablename__ = "medicines"
    
    medicine_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    medicine_name = Column(String, index=True)
    dosage_per_day = Column(Integer, default=1)
    schedule_times = Column(String)  # JSON string or comma-separated times like '09:00,21:00'
    total_pills = Column(Integer, default=0)
    remaining_pills = Column(Integer, default=0)
