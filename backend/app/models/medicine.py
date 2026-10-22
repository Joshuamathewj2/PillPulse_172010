from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.sql import func
from app.database.db import Base

class Medicine(Base):
    __tablename__ = "medicines"

    medicine_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # patient code, e.g. "JOSH-4521"
    medicine_name = Column(String, index=True)
    generic_name = Column(String, nullable=True)
    dosage = Column(String, nullable=True)  # "1 tablet (650 mg)"
    dosage_per_day = Column(Integer, default=1)
    schedule_times = Column(String)  # comma-separated 24h times like '08:00,20:00'
    instructions = Column(Text, nullable=True)
    duration_days = Column(Integer, nullable=True)
    start_date = Column(Date, server_default=func.current_date())
    total_pills = Column(Integer, default=0)
    remaining_pills = Column(Integer, default=0)
