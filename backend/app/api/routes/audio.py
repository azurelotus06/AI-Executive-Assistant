from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, Optional
import base64
import logging

from app.services.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize audio processor (will be replaced by dependency injection)
audio_processor = AudioProcessor()

@router.post("/process-chunk")
async def process_audio_chunk(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single audio chunk"""
    try:
        audio_data = data.get("audio_data")
        if not audio_data:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        # Process the audio chunk
        transcript = await audio_processor.process_audio_chunk(audio_data)
        
        return {
            "success": True,
            "transcript": transcript,
            "has_speech": transcript is not None
        }
        
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-audio")
async def upload_audio_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload and process an audio file"""
    try:
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read file content
        audio_content = await file.read()
        
        # Convert to base64 for processing
        audio_b64 = base64.b64encode(audio_content).decode()
        
        # Process the audio
        transcript = await audio_processor.process_audio_chunk(audio_b64)
        
        return {
            "success": True,
            "filename": file.filename,
            "transcript": transcript,
            "file_size": len(audio_content)
        }
        
    except Exception as e:
        logger.error(f"Error processing uploaded audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-recording")
async def start_recording() -> Dict[str, Any]:
    """Start microphone recording"""
    try:
        success = await audio_processor.start_recording()
        
        if success:
            return {"success": True, "message": "Recording started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start recording")
            
    except Exception as e:
        logger.error(f"Error starting recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-recording")
async def stop_recording() -> Dict[str, Any]:
    """Stop microphone recording"""
    try:
        audio_processor.stop_recording()
        return {"success": True, "message": "Recording stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mute")
async def mute_audio() -> Dict[str, Any]:
    """Mute audio processing"""
    try:
        audio_processor.set_muted(True)
        return {"success": True, "message": "Audio muted"}
        
    except Exception as e:
        logger.error(f"Error muting audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unmute")
async def unmute_audio() -> Dict[str, Any]:
    """Unmute audio processing"""
    try:
        audio_processor.set_muted(False)
        return {"success": True, "message": "Audio unmuted"}
        
    except Exception as e:
        logger.error(f"Error unmuting audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-buffers")
async def clear_audio_buffers() -> Dict[str, Any]:
    """Clear audio buffers"""
    try:
        audio_processor.clear_buffers()
        return {"success": True, "message": "Audio buffers cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing buffers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_audio_status() -> Dict[str, Any]:
    """Get audio processor status"""
    try:
        return {
            "success": True,
            "is_healthy": audio_processor.is_healthy(),
            "is_muted": audio_processor.is_muted,
            "is_recording": audio_processor.is_recording,
            "sample_rate": audio_processor.sample_rate,
            "chunk_duration": audio_processor.chunk_duration
        }
        
    except Exception as e:
        logger.error(f"Error getting audio status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
