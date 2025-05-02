from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional

import os

# Use the DATABASE_URL from Render's environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Database model
class LocationModel(Base):
    __tablename__ = "locations"
    id = Column(String, primary_key=True, index=True)
    lat = Column(Float)
    lng = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic schema
class LocationIn(BaseModel):
    device_id: str
    lat: float
    lng: float
    timestamp: Optional[str] = None

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/location")
def save_location(loc: LocationIn, db: Session = Depends(get_db)):
    ts = loc.timestamp or datetime.utcnow().isoformat()
    location = LocationModel(
        id=loc.device_id,
        lat=loc.lat,
        lng=loc.lng,
        timestamp=datetime.fromisoformat(ts)
    )
    db.merge(location)  # merge = insert or update if exists
    db.commit()
    return {"status": "ok"}

@app.get("/location/{device_id}")
def get_latest_location(device_id: str, db: Session = Depends(get_db)):
    location = db.query(LocationModel).filter(LocationModel.id == device_id).first()
    if location:
        return {
            "device_id": location.id,
            "lat": location.lat,
            "lng": location.lng,
            "timestamp": location.timestamp.isoformat()
        }
    return {"error": "No location found"}

@app.get("/")
def ping():
    return {"status": "running"}
