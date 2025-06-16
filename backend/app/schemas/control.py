"""Control-related schemas"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class SessionResponse(BaseModel):
    """Response schema for session operations"""
    success: bool
    message: str
    session_id: Optional[str] = None

class SystemStatusService(BaseModel):
    """Schema for individual service status"""
    healthy: bool
    muted: Optional[bool] = None
    paused: Optional[bool] = None
    recording: Optional[bool] = None
    sample_rate: Optional[int] = None
    conversation_length: Optional[int] = None
    last_response: Optional[str] = None
    voice_id: Optional[str] = None

class SystemStatusResponse(BaseModel):
    """Response schema for system status"""
    success: bool
    system_status: Dict[str, SystemStatusService]

class TestPipelineResult(BaseModel):
    """Schema for pipeline test results"""
    tts: Dict[str, Any]
    ai_analysis: Dict[str, Any]
    audio_processor: Dict[str, Any]

class TestPipelineResponse(BaseModel):
    """Response schema for pipeline testing"""
    success: bool
    message: str
    test_results: TestPipelineResult

class Voice(BaseModel):
    """Schema for voice information"""
    voice_id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None

class AvailableVoicesResponse(BaseModel):
    """Response schema for available voices"""
    success: bool
    voices: Optional[List[Voice]] = None
    current_voice: Optional[str] = None
    message: Optional[str] = None

class SetVoiceRequest(BaseModel):
    """Request schema for setting voice"""
    voice_id: str

class SetVoiceResponse(BaseModel):
    """Response schema for setting voice"""
    success: bool
    message: str

class ControlResponse(BaseModel):
    """Generic control response"""
    success: bool
    message: str
