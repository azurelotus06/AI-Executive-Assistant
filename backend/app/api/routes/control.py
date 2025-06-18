from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import logging

from app.services.audio_processor import AudioProcessor
from app.services.ai_service import AIService
from app.services.tts_service import TTSService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services (will be replaced by dependency injection)
audio_processor = AudioProcessor()
ai_service = AIService()
tts_service = TTSService()

@router.post("/start-session")
async def start_session() -> Dict[str, Any]:
    """Start a new AI assistant session"""
    try:
        # Clear any existing state
        audio_processor.clear_buffers()
        ai_service.clear_conversation_history()
        
        # Unmute services
        audio_processor.set_muted(False)
        ai_service.set_paused(False)
        tts_service.set_muted(False)
        
        return {
            "success": True,
            "message": "AI assistant session started",
            "session_id": "default"  # Could be enhanced with actual session management
        }
        
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-session")
async def stop_session() -> Dict[str, Any]:
    """Stop the current AI assistant session"""
    try:
        # Stop recording if active
        audio_processor.stop_recording()
        
        # Mute all services
        audio_processor.set_muted(True)
        ai_service.set_paused(True)
        tts_service.set_muted(True)
        
        return {
            "success": True,
            "message": "AI assistant session stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mute-all")
async def mute_all() -> Dict[str, Any]:
    """Mute all AI assistant functions"""
    try:
        audio_processor.set_muted(True)
        ai_service.set_paused(True)
        tts_service.set_muted(True)
        
        return {
            "success": True,
            "message": "All AI assistant functions muted"
        }
        
    except Exception as e:
        logger.error(f"Error muting all: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unmute-all")
async def unmute_all() -> Dict[str, Any]:
    """Unmute all AI assistant functions"""
    try:
        audio_processor.set_muted(False)
        ai_service.set_paused(False)
        tts_service.set_muted(False)
        
        return {
            "success": True,
            "message": "All AI assistant functions unmuted"
        }
        
    except Exception as e:
        logger.error(f"Error unmuting all: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-stop")
async def emergency_stop() -> Dict[str, Any]:
    """Emergency stop - immediately halt all AI functions"""
    try:
        # Stop recording
        audio_processor.stop_recording()
        
        # Mute everything
        audio_processor.set_muted(True)
        ai_service.set_paused(True)
        tts_service.set_muted(True)
        
        # Clear buffers
        audio_processor.clear_buffers()
        
        return {
            "success": True,
            "message": "Emergency stop executed - all AI functions halted"
        }
        
    except Exception as e:
        logger.error(f"Error in emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-status")
async def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    try:
        return {
            "success": True,
            "system_status": {
                "audio_processor": {
                    "healthy": audio_processor.is_healthy(),
                    "muted": audio_processor.is_muted,
                    "recording": audio_processor.is_recording,
                    "sample_rate": audio_processor.sample_rate
                },
                "ai_service": {
                    "healthy": ai_service.is_healthy(),
                    "paused": ai_service.is_paused,
                    "conversation_length": len(ai_service.conversation_history),
                    "last_response": ai_service.last_response_time.isoformat() if ai_service.last_response_time else None
                },
                "tts_service": {
                    "healthy": tts_service.is_healthy(),
                    "muted": tts_service.is_muted,
                    "voice_id": tts_service.voice_id
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-pipeline")
async def test_pipeline() -> Dict[str, Any]:
    """Test the complete AI pipeline with sample data"""
    try:
        test_results = {}
        
        # Test TTS
        tts_test = await tts_service.test_voice_quality("Testing AI assistant pipeline")
        test_results["tts"] = tts_test
        
        # Test AI analysis
        ai_response = await ai_service.analyze_conversation(
            "Let's test our AI assistant pipeline functionality", 
            "Test User"
        )
        test_results["ai_analysis"] = {
            "success": ai_response is not None,
            "response": ai_response
        }
        
        # Test audio processor health
        test_results["audio_processor"] = {
            "healthy": audio_processor.is_healthy(),
            "ready": not audio_processor.is_muted
        }
        
        return {
            "success": True,
            "message": "Pipeline test completed",
            "test_results": test_results
        }
        
    except Exception as e:
        logger.error(f"Error testing pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-system")
async def reset_system() -> Dict[str, Any]:
    """Reset the entire system to initial state"""
    try:
        # Stop all active processes
        audio_processor.stop_recording()
        
        # Clear all data
        audio_processor.clear_buffers()
        ai_service.clear_conversation_history()
        
        # Reset to default states
        audio_processor.set_muted(False)
        ai_service.set_paused(False)
        tts_service.set_muted(False)
        
        return {
            "success": True,
            "message": "System reset to initial state"
        }
        
    except Exception as e:
        logger.error(f"Error resetting system: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meeting-status/{bot_id}")
async def get_meeting_status(bot_id: str) -> Dict[str, Any]:
    """Get current meeting status for a bot"""
    try:
        from app.services.meeting_service import meeting_service
        status = await meeting_service.get_bot_status(bot_id)
        
        if status["status"] == "success":
            return {
                "success": True,
                "bot_status": status["bot_data"]
            }
        else:
            return {
                "success": False,
                "message": status["message"]
            }
            
    except Exception as e:
        logger.error(f"Error getting meeting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-voices")
async def get_available_voices() -> Dict[str, Any]:
    """Get available TTS voices"""
    try:
        voices = await tts_service.get_available_voices()
        
        if voices:
            return {
                "success": True,
                "voices": voices,
                "current_voice": tts_service.voice_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to retrieve voices"
            }
            
    except Exception as e:
        logger.error(f"Error getting available voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set-voice")
async def set_voice(data: Dict[str, Any]) -> Dict[str, Any]:
    """Set the TTS voice"""
    try:
        voice_id = data.get("voice_id")
        if not voice_id:
            raise HTTPException(status_code=400, detail="No voice_id provided")
        
        tts_service.voice_id = voice_id
        
        return {
            "success": True,
            "message": f"Voice set to {voice_id}"
        }
        
    except Exception as e:
        logger.error(f"Error setting voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))
