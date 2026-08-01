from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pathlib
import uuid
import os
import asyncio
import json
from telegram import Bot
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
    {"id": "1", "name": "조수아", "status": "normal", "position": {"x": 2, "y": 0, "z": -3}},
    {"id": "2", "name": "황정빈", "status": "normal", "position": {"x": -4, "y": 0, "z": 2}},
]

alerts_queue = []
device_to_worker = {}

async def telegram_listener():
    token = os.getenv("SOLAD_TOKEN") or os.getenv("RECEIVER_BOT_TOKEN")
    if not token:
        print("Telegram receiver token not set. Listener won't start.")
        return
        
    bot = Bot(token)
    offset = None
    print("Telegram listener started...")
    try:
        async with bot:
            while True:
                try:
                    updates = await bot.get_updates(offset=offset, timeout=20, allowed_updates=[])
                    for u in updates:
                        if u.message and u.message.text:
                            text = u.message.text
                            print(f"[Telegram Listener] Received message: {text}")
                            try:
                                data = json.loads(text)
                                msg_content = data.get("data", "")
                                device_id = str(data.get("id", "unknown"))
                                
                                # 매핑 로직: 새 기기면 조수아(1)에 매핑, 그 다음은 황정빈(2)
                                if device_id not in device_to_worker:
                                    device_to_worker[device_id] = "1" if len(device_to_worker) == 0 else "2"
                                    
                                worker_id = device_to_worker[device_id]

                                if "낙상 발생" in msg_content or "아파요" in msg_content or "도와주세요" in msg_content:
                                    is_already_accident = False
                                    for w in workers_data:
                                        if w["id"] == worker_id:
                                            if w["status"] == "accident":
                                                is_already_accident = True
                                            w["status"] = "accident"
                                    
                                    if not is_already_accident:
                                        alerts_queue.append({
                                            "id": str(uuid.uuid4()),
                                            "device_id": device_id,
                                            "worker_id": worker_id,
                                            "message": msg_content,
                                        })
                                else:
                                    # 일반 음성 메시지
                                    messages_queue.append({
                                        "id": str(uuid.uuid4()),
                                        "worker_id": worker_id,
                                        "message": msg_content,
                                    })
                                    if len(messages_queue) > 10:
                                        messages_queue.pop(0)
                            except Exception:
                                pass
                        offset = u.update_id + 1
                except Exception as e:
                    print(f"Polling error: {e}")
                    await asyncio.sleep(5)
    except Exception as e:
        print(f"Bot session error: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(telegram_listener())

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

@app.post("/api/workers/reset_status")
async def reset_workers_status():
    for w in workers_data:
        w["status"] = "normal"
    return workers_data

@app.get("/api/alerts")
async def get_alerts():
    return alerts_queue

messages_queue = []

@app.get("/api/messages")
async def get_messages():
    return messages_queue

@app.post("/api/alerts/webhook")
async def receive_webhook(payload: dict):
    msg_content = payload.get("data", "")
    device_id = str(payload.get("id", "unknown"))
    
    if device_id not in device_to_worker:
        device_to_worker[device_id] = "1" if len(device_to_worker) == 0 else "2"
        
    worker_id = device_to_worker[device_id]

    if "낙상 발생" in msg_content or "아파요" in msg_content or "도와주세요" in msg_content:
        is_already_accident = False
        for w in workers_data:
            if w["id"] == worker_id:
                if w["status"] == "accident":
                    is_already_accident = True
                w["status"] = "accident"
        
        if not is_already_accident:
            alerts_queue.append({
                "id": str(uuid.uuid4()),
                "device_id": device_id,
                "worker_id": worker_id,
                "message": msg_content,
            })
    else:
        # 일반 음성 메시지
        messages_queue.append({
            "id": str(uuid.uuid4()),
            "worker_id": worker_id,
            "message": msg_content,
        })
        
        # 10개까지만 유지
        if len(messages_queue) > 10:
            messages_queue.pop(0)

    return {"success": True}

@app.post("/api/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    global alerts_queue
    resolved_alert = next((a for a in alerts_queue if a["id"] == alert_id), None)
    if resolved_alert:
        alerts_queue = [a for a in alerts_queue if a["id"] != alert_id]
    return {"success": True}

@app.post("/api/broadcast")
async def broadcast(
    audio: UploadFile = File(...),
    selected_workers: str = Form(...) # comma separated ids
):
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    file_extension = audio.filename.split('.')[-1] if '.' in audio.filename else 'wav'
    file_path = pathlib.Path(f"outputs/{uuid.uuid4()}.{file_extension}")
    file_path.parent.mkdir(exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(await audio.read())
        
    try:
        transcribed_text = await s2t(file_path)
        token = os.getenv("LUNAD_TOKEN") or os.getenv("SENDER_BOT_TOKEN")
        if token:
            worker_ids = [w.strip() for w in selected_workers.split(',') if w.strip()]
            for w_id in worker_ids:
                # 사용자 요청 포맷: {"id": 보낼 사용자 아이디, "data": 보낼 데이터}
                payload_str = json.dumps({"id": w_id, "data": transcribed_text}, ensure_ascii=False)
                await send(token, payload_str)
        else:
            print("SENDER_TOKEN is not set.")
        return {"success": True, "text": transcribed_text}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_path.exists():
            file_path.unlink()

