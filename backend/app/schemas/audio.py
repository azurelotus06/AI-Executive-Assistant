"""Audio-related schemas"""
from pydantic import BaseModel
from typing import Optional

class AudioChunkRequest(BaseModel):
    """Request schema for audio chunk processing"""
    audio_data: str  # Base64 encoded audio data
    timestamp: Optional[float] = None

class AudioChunkResponse(BaseModel):
    """Response schema for audio chunk processing"""
    success: bool
    transcript: Optional[str] = None
    has_speech: bool

class AudioStatusResponse(BaseModel):
    """Response schema for audio status"""
    success: bool
    is_healthy: bool
    is_muted: bool
    is_recording: bool
    sample_rate: int
    chunk_duration: float

class AudioUploadResponse(BaseModel):
    """Response schema for audio file upload"""
    success: bool
    filename: str
    transcript: Optional[str] = None
    file_size: int
