"""Meeting schemas for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class JoinMeetingRequest(BaseModel):
    """Request model for joining a meeting"""
    meeting_url: str = Field(..., description="The meeting URL (Zoom, Teams, etc.)")
    bot_name: Optional[str] = Field(
        "AI Executive Assistant", 
        description="Name of the bot that will join the meeting"
    )


class JoinMeetingResponse(BaseModel):
    """Response model for joining a meeting"""
    bot_id: str = Field(..., description="Unique identifier for the bot")
    message: str = Field(..., description="Status message")
    status: str = Field(..., description="Current status of the bot")


class MeetingStatusResponse(BaseModel):
    """Response model for meeting status"""
    bot_id: str
    status: str
    meeting_url: str
    joined_at: Optional[str] = None
    duration: Optional[int] = None


class WebhookEvent(BaseModel):
    """Webhook event from MeetingBaaS"""
    event: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")


class TranscriptSegment(BaseModel):
    """Transcript segment model"""
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None


class MeetingTranscript(BaseModel):
    """Meeting transcript model"""
    bot_id: str
    segments: List[TranscriptSegment]
    total_duration: float


class MeetingSummary(BaseModel):
    """Meeting summary model"""
    bot_id: str
    meeting_name: str
    attendees: List[str]
    summary: str
    key_points: List[str]
    action_items: List[str]
    duration: int
    created_at: datetime


class AIInsight(BaseModel):
    """AI insight model"""
    text: str
    confidence: float
    timestamp: datetime
    should_speak: bool = False
    reasoning: Optional[str] = None
