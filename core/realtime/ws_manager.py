from fastapi import WebSocket
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

        # ==========================================
        # CONNECTION METADATA (ADMIN SEGMENTATION)
        # ==========================================
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        # ==========================================
        # EVENT BUFFER (REPLAY + AI TRAINING)
        # ==========================================
        self.event_buffer: List[Dict[str, Any]] = []

        # ==========================================
        # REAL-TIME SUBSCRIBER GROUPS (NEW UPGRADE)
        # ==========================================
        self.groups: Dict[str, List[WebSocket]] = {
            "admins": [],
            "traders": [],
            "all": []
        }

    # ==========================================
    # CONNECT
    # ==========================================

    async def connect(self, websocket: WebSocket, client_type: str = "general"):

        await websocket.accept()

        self.active_connections.append(websocket)

        # store metadata for dashboard routing
        self.connection_metadata[websocket] = {
            "client_type": client_type,
            "connected_at": datetime.utcnow().isoformat()
        }

        # assign to groups
        if client_type == "admin":
            self.groups["admins"].append(websocket)

        elif client_type == "trader":
            self.groups["traders"].append(websocket)

        self.groups["all"].append(websocket)

    # ==========================================
    # DISCONNECT
    # ==========================================

    def disconnect(self, websocket: WebSocket):

        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        # remove from groups safely
        for group in self.groups.values():
            if websocket in group:
                group.remove(websocket)

    # ==========================================
    # CORE BROADCAST (BACKWARD COMPATIBLE)
    # ==========================================

    async def broadcast(self, message: dict):

        enriched_message = {
            **message,
            "timestamp": message.get("timestamp") or datetime.utcnow().isoformat()
        }

        # store in buffer (for replay / AI training)
        self.event_buffer.append(enriched_message)

        # limit memory usage
        if len(self.event_buffer) > 5000:
            self.event_buffer = self.event_buffer[-5000:]

        dead_connections = []

        for connection in self.active_connections:
            try:
                await connection.send_json(enriched_message)
            except:
                dead_connections.append(connection)

        for conn in dead_connections:
            self.disconnect(conn)

    # ==========================================
    # ADMIN BROADCAST (REAL DASHBOARD MODE)
    # ==========================================

    async def broadcast_to_admins(self, message: dict):

        enriched_message = {
            **message,
            "timestamp": datetime.utcnow().isoformat()
        }

        for connection in list(self.groups["admins"]):
            try:
                await connection.send_json(enriched_message)
            except:
                self.disconnect(connection)

    # ==========================================
    # TRADER BROADCAST (EA CLIENTS ONLY)
    # ==========================================

    async def broadcast_to_traders(self, message: dict):

        enriched_message = {
            **message,
            "timestamp": datetime.utcnow().isoformat()
        }

        for connection in list(self.groups["traders"]):
            try:
                await connection.send_json(enriched_message)
            except:
                self.disconnect(connection)

    # ==========================================
    # EVENT STREAM EXPORT (FOR AI / REPLAY)
    # ==========================================

    def get_event_stream(self, limit: int = 100):

        return self.event_buffer[-limit:]

    # ==========================================
    # FILTERED STREAM (NEW - AI TRAINING MODE)
    # ==========================================

    def get_filtered_stream(self, event_type: str, limit: int = 100):

        return [
            e for e in self.event_buffer[-limit:]
            if e.get("type") == event_type
        ]


# ==========================================
# GLOBAL SINGLETON
# ==========================================

manager = ConnectionManager()