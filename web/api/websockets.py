from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

router = APIRouter()

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection might be closed
                pass

manager = WebSocketManager()

@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            data = {
                "type": "dashboard_update",
                "timestamp": "2024-01-01T00:00:00Z",
                "data": {
                    "active_batches": 0,
                    "system_health": "healthy"
                }
            }
            await manager.send_personal_message(json.dumps(data), websocket)
            await asyncio.sleep(30)  # Send updates every 30 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)