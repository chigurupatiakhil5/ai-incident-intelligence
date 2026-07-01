from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    server_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    description = Column(String, nullable=False)
    cpu_percent = Column(Float, nullable=True)
    memory_percent = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())