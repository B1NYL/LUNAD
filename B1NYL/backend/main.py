from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pathlib
import uuid
import os
from services import s2t, send, translate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Worker(BaseModel):
    id: str
    name: str
    status: str

class PositionUpdate(BaseModel):
    x: float
    y: float
    z: float

# Dummy data for workers with 3D coordinates (x, y, z)
# y=0: 1층, y=4: 2층, y=8: 3층
workers_data = [
    {"id": "1", "name": "김철수", "status": "normal", "position": {"x": 2, "y": 0, "z": -3}},
    {"id": "2", "name": "오지훈", "status": "accident", "position": {"x": -4, "y": 4, "z": 2}},
    {"id": "3", "name": "박민준", "status": "normal", "position": {"x": 1, "y": 8, "z": 4}},
    {"id": "4", "name": "이영희", "status": "normal", "position": {"x": -2, "y": 0, "z": 1}},
]

@app.get("/api/workers")
async def get_workers():
    return workers_data

@app.put("/api/workers/{worker_id}/position")
async def update_worker_position(worker_id: str, pos: PositionUpdate):
    for w in workers_data:
        if w["id"] == worker_id:
            w["position"] = {"x": pos.x, "y": pos.y, "z": pos.z}
            return w
    raise HTTPException(status_code=404, detail="Worker not found")

@app.post("/api/workers/reset")
async def reset_workers_position():
    for w in workers_data:
        w["position"]["y"] = 0
    return workers_data

@app.post("/api/broadcast")
async def broadcast(
    audio: UploadFile = File(...),
    selected_workers: str = Form(...) # comma separated ids
):
    # Save audio file
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    file_extension = audio.filename.split('.')[-1] if '.' in audio.filename else 'wav'
    file_path = pathlib.Path(f"outputs/{uuid.uuid4()}.{file_extension}")
    file_path.parent.mkdir(exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(await audio.read())
        
    try:
        # Run STT
        transcribed_text = await s2t(file_path)
        
        # Determine worker names if needed, but per user request, just send the text
        worker_ids = selected_workers.split(",") if selected_workers else []
        
        # Send Telegram Message (just text)
        token = os.getenv("LUNAD_TOKEN")
        if token:
            await send(token, transcribed_text)
        else:
            print("LUNAD_TOKEN is not set.")
        
        return {"success": True, "text": transcribed_text}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_path.exists():
            file_path.unlink()
