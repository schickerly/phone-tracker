from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import sqlite3

app = FastAPI()

# DB setup
conn = sqlite3.connect("locations.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS locations (
    device_id TEXT,
    lat REAL,
    lng REAL,
    timestamp TEXT
)
""")
conn.commit()

# Data model
class Location(BaseModel):
    device_id: str
    lat: float
    lng: float
    timestamp: Optional[str] = None

@app.post("/location")
def save_location(loc: Location):
    ts = loc.timestamp or datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO locations (device_id, lat, lng, timestamp) VALUES (?, ?, ?, ?)",
        (loc.device_id, loc.lat, loc.lng, ts)
    )
    conn.commit()
    return {"status": "ok"}

@app.get("/location/{device_id}")
def get_latest_location(device_id: str):
    cursor.execute(
        "SELECT lat, lng, timestamp FROM locations WHERE device_id = ? ORDER BY timestamp DESC LIMIT 1",
        (device_id,)
    )
    row = cursor.fetchone()
    if row:
        return {"device_id": device_id, "lat": row[0], "lng": row[1], "timestamp": row[2]}
    return {"error": "No location found"}
