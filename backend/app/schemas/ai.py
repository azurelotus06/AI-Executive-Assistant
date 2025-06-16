"""AI-related schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AnalyzeRequest(BaseModel):
    """Request schema for conversation analysis"""
    transcript: str
    speaker: str = "Participant"

class AIResponseData(BaseModel):
    """AI response data structure"""
    should_speak: bool
    response: Optional[str] = None
    confidence: float
    reasoning: str

class AnalyzeResponse(BaseModel):
    """Response schema for conversation analysis"""
    success: bool
    ai_response: Optional[AIResponseData] = None

class ManualPromptRequest(BaseModel):
    """Request schema for manual prompts"""
    prompt: str

class ManualPromptResponse(BaseModel):
    """Response schema for manual prompts"""
    success: bool
    response: str

class ConversationMessage(BaseModel):
    """Schema for conversation history messages"""
    speaker: str
    text: str
    timestamp: str

class ConversationSummary(BaseModel):
    """Schema for conversation summary"""
    total_messages: int
    ai_responses: int
    recent_key_points: List[str]
    last_activity: Optional[str] = None

class ConversationHistoryResponse(BaseModel):
    """Response schema for conversation history"""
    success: bool
    history: List[ConversationMessage]
    total_messages: int

class AIStatusResponse(BaseModel):
    """Response schema for AI service status"""
    success: bool
    is_healthy: bool
    is_paused: bool
    conversation_length: int
    context_window: int
    last_response_time: Optional[str] = None

class TestAnalysisRequest(BaseModel):
    """Request schema for test analysis"""
    test_transcript: Optional[str] = "Let's discuss our Q4 strategy and revenue targets."

class TestAnalysisResponse(BaseModel):
    """Response schema for test analysis"""
    success: bool
    test_transcript: str
    ai_response: Optional[AIResponseData] = None
