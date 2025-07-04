from typing import List, Dict, Any
from fastapi import WebSocket
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "connected_at": asyncio.get_event_loop().time(),
            "user_id": None,
            "session_id": None
        }
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_data:
                del self.connection_data[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
            logger.info(f"Sent personal message: {message}")
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def send_message(self, message: Dict[str, Any], websocket: WebSocket = None):
        """Send a message to a specific connection or all connections"""
        if websocket:
            await self.send_personal_message(message, websocket)
        else:
            await self.broadcast(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_audio_response(self, audio_data: bytes, ai_text: str, websocket: WebSocket = None):
        """Send audio response with metadata"""
        import base64
        
        message = {
            "type": "audio_response",
            "audio_data": base64.b64encode(audio_data).decode('utf-8'),
            "text": ai_text,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.send_message(message, websocket)
    
    async def send_transcript_update(self, transcript: str, confidence: float = 1.0, websocket: WebSocket = None):
        """Send transcript update"""
        message = {
            "type": "transcript",
            "text": transcript,
            "confidence": confidence,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.send_message(message, websocket)
    
    async def send_status_update(self, status: str, details: Dict[str, Any] = None, websocket: WebSocket = None):
        """Send status update"""
        message = {
            "type": "status",
            "status": status,
            "details": details or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.send_message(message, websocket)
    
    async def send_error(self, error_message: str, error_code: str = None, websocket: WebSocket = None):
        """Send error message"""
        message = {
            "type": "error",
            "message": error_message,
            "code": error_code,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await self.send_message(message, websocket)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self, websocket: WebSocket) -> Dict[str, Any]:
        """Get information about a specific connection"""
        return self.connection_data.get(websocket, {})
    
    def set_connection_data(self, websocket: WebSocket, key: str, value: Any):
        """Set data for a specific connection"""
        if websocket in self.connection_data:
            self.connection_data[websocket][key] = value


# Create a global instance
manager = WebSocketManager()
