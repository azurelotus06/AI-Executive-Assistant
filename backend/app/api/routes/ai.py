from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import logging

from app.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize AI service (will be replaced by dependency injection)
ai_service = AIService()

@router.post("/analyze")
async def analyze_conversation(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze conversation and get AI response"""
    try:
        transcript = data.get("transcript")
        speaker = data.get("speaker", "Participant")
        
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript provided")
        
        # Analyze the conversation
        ai_response = await ai_service.analyze_conversation(transcript, speaker)
        
        return {
            "success": True,
            "ai_response": ai_response
        }
        
    except Exception as e:
        logger.error(f"Error analyzing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manual-prompt")
async def manual_prompt(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a manual user prompt"""
    try:
        prompt = data.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        # Generate response to manual prompt
        response = await ai_service.generate_manual_response(prompt)
        
        if response:
            return {
                "success": True,
                "response": response
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate response")
            
    except Exception as e:
        logger.error(f"Error processing manual prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pause")
async def pause_ai() -> Dict[str, Any]:
    """Pause AI analysis"""
    try:
        ai_service.set_paused(True)
        return {"success": True, "message": "AI analysis paused"}
        
    except Exception as e:
        logger.error(f"Error pausing AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/resume")
async def resume_ai() -> Dict[str, Any]:
    """Resume AI analysis"""
    try:
        ai_service.set_paused(False)
        return {"success": True, "message": "AI analysis resumed"}
        
    except Exception as e:
        logger.error(f"Error resuming AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation-summary")
async def get_conversation_summary() -> Dict[str, Any]:
    """Get conversation summary"""
    try:
        summary = ai_service.get_conversation_summary()
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation-history")
async def get_conversation_history() -> Dict[str, Any]:
    """Get full conversation history"""
    try:
        history = ai_service.export_conversation()
        return {
            "success": True,
            "history": history,
            "total_messages": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-history")
async def clear_conversation_history() -> Dict[str, Any]:
    """Clear conversation history"""
    try:
        ai_service.clear_conversation_history()
        return {"success": True, "message": "Conversation history cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_ai_status() -> Dict[str, Any]:
    """Get AI service status"""
    try:
        return {
            "success": True,
            "is_healthy": ai_service.is_healthy(),
            "is_paused": ai_service.is_paused,
            "conversation_length": len(ai_service.conversation_history),
            "context_window": ai_service.context_window,
            "last_response_time": ai_service.last_response_time.isoformat() if ai_service.last_response_time else None
        }
        
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-analysis")
async def test_ai_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Test AI analysis with sample data"""
    try:
        test_transcript = data.get("test_transcript", "Let's discuss our Q4 strategy and revenue targets.")
        
        # Analyze the test transcript
        ai_response = await ai_service.analyze_conversation(test_transcript, "Test Speaker")
        
        return {
            "success": True,
            "test_transcript": test_transcript,
            "ai_response": ai_response
        }
        
    except Exception as e:
        logger.error(f"Error in test analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
