from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.realtime.ws_manager import manager

router = APIRouter(prefix="/realtime", tags=["Realtime"])


# ==========================================
# MAIN WEBSOCKET ENDPOINT
# ==========================================

@router.websocket("/ws")
async def realtime_websocket(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            # Optional: heartbeat or ping handling
            await manager.broadcast({
                "type": "ping",
                "message": data
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)