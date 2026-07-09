import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db, create_tables
from app.models.incident import Incident
from app.workers.sqs_worker import run_worker
from app.routers import query

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    asyncio.create_task(run_worker())
    yield

app = FastAPI(title="AI Incident Intelligence Platform", lifespan=lifespan)

app.include_router(query.router)

class IncidentCreate(BaseModel):
    server_name: str
    severity: str
    description: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None

class IncidentResponse(BaseModel):
    id: int
    server_name: str
    severity: str
    description: str
    cpu_percent: Optional[float]
    memory_percent: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "AI Incident Intelligence Platform"}

@app.get("/incidents", response_model=list[IncidentResponse])
def get_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).all()

@app.post("/incidents", response_model=IncidentResponse)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    db_incident = Incident(**incident.model_dump())
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident