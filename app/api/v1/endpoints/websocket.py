# app/api/v1/endpoints/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        # Dictionary to hold active connections per product_id
        # structure: { product_id: [websocket, websocket] }
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, product_id: str):
        await websocket.accept()
        if product_id not in self.active_connections:
            self.active_connections[product_id] = []
        self.active_connections[product_id].append(websocket)

    def disconnect(self, websocket: WebSocket, product_id: str):
        if product_id in self.active_connections:
            self.active_connections[product_id].remove(websocket)
            if not self.active_connections[product_id]:
                del self.active_connections[product_id]

    async def broadcast(self, product_id: str, message: dict):
        if product_id in self.active_connections:
            for connection in self.active_connections[product_id]:
                try:
                    await connection.send_json(message)
                except:
                    # Handle broken pipe if connection closed abruptly
                    pass

manager = ConnectionManager()