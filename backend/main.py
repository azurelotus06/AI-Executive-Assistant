from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import logging
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

from app.core.config import settings
from app.api.routes import audio, ai, control, meeting
from app.services.audio_processor import AudioProcessor
from app.services.ai_service import AIService
from app.services.tts_service import TTSService
from app.services.realtime_audio_handler import audio_handler
from app.core.websocket_manager import WebSocketManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Zoom AI Assistant",
    description="Real-Time AI Executive Assistant for Zoom Meetings",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "https://magnetic-thrush-currently.ngrok-free.app", "https://bold-chow-trivially.ngrok-free.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
audio_processor = AudioProcessor()
ai_service = AIService()
tts_service = TTSService()
websocket_manager = WebSocketManager()

# Include API routes
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(control.router, prefix="/api/control", tags=["control"])
app.include_router(meeting.router, prefix="/api", tags=["meeting"])

@app.websocket("/ws/meeting/input")
async def meeting_audio_websocket_input(websocket: WebSocket):
    """WebSocket input endpoint for MeetingBaaS audio streams"""
    await audio_handler.handle_websocket_input(websocket)

@app.websocket("/ws/meeting/output")
async def meeting_audio_websocket_output(websocket: WebSocket):
    """WebSocket output endpoint for MeetingBaaS audio streams"""
    await audio_handler.handle_websocket_output(websocket)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio_chunk":
                # Process audio chunk
                audio_data = message["data"]
                
                # Convert speech to text
                transcript = await audio_processor.process_audio_chunk(audio_data)
                
                if transcript:
                    # Send transcript to AI for analysis
                    ai_response = await ai_service.analyze_conversation(transcript)
                    
                    if ai_response and ai_response.get("should_speak"):
                        # Generate TTS audio
                        tts_audio = await tts_service.generate_speech(ai_response["response"])
                        
                        # Send response back to client
                        await websocket_manager.send_message({
                            "type": "ai_response",
                            "transcript": transcript,
                            "ai_text": ai_response["response"],
                            "audio_data": tts_audio,
                            "confidence": ai_response.get("confidence", 0.8)
                        })
                    
                    # Send transcript update
                    await websocket_manager.send_message({
                        "type": "transcript_update",
                        "transcript": transcript,
                        "timestamp": message.get("timestamp")
                    })
            
            elif message["type"] == "control":
                # Handle control messages (mute, pause, etc.)
                control_type = message.get("action")
                if control_type == "mute":
                    audio_processor.set_muted(True)
                elif control_type == "unmute":
                    audio_processor.set_muted(False)
                elif control_type == "pause":
                    ai_service.set_paused(True)
                elif control_type == "resume":
                    ai_service.set_paused(False)
                
                await websocket_manager.send_message({
                    "type": "control_response",
                    "action": control_type,
                    "status": "success"
                })
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.send_message({
            "type": "error",
            "message": str(e)
        })

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Zoom AI Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "audio_processor": audio_processor.is_healthy(),
            "ai_service": ai_service.is_healthy(),
            "tts_service": tts_service.is_healthy()
        }
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    from scripts.init_services import initialize_services
    await initialize_services()

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up resources on shutdown"""
    from app.services.realtime_audio_handler import audio_handler
    await audio_handler.cleanup()
    logger.info("Application shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
