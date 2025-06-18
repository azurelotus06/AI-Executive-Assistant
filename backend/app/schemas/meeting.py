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
    event: str = Field(..., description="Event type (bot.status_change, complete, failed)")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    api_key: Optional[str] = Field(None, description="API key from x-meeting-baas-api-key header")

class StatusChangeData(BaseModel):
    """Data model for bot status change events"""
    bot_id: str = Field(..., description="The identifier of the bot")
    status: Dict[str, Any] = Field(..., description="Status details")
    
    class StatusDetails(BaseModel):
        """Nested status details model"""
        code: str = Field(..., description="Status code (joining_call, in_waiting_room, etc.)")
        created_at: str = Field(..., description="ISO timestamp of event")
        start_time: Optional[str] = Field(None, description="Recording start time (for in_call_recording)")
        error_message: Optional[str] = Field(None, description="Error message (for meeting_error)")
        error_type: Optional[str] = Field(None, description="Error type (for meeting_error)")

class CompleteData(BaseModel):
    """Data model for complete events"""
    bot_id: str = Field(..., description="The identifier of the bot")
    mp4: Optional[str] = Field(None, description="Pre-signed S3 URL for recording")
    speakers: Optional[List[str]] = Field(None, description="List of speakers")
    transcript: Optional[List[Dict[str, Any]]] = Field(None, description="Meeting transcript")

class FailedData(BaseModel):
    """Data model for failed events"""
    bot_id: str = Field(..., description="The identifier of the bot")
    error: str = Field(..., description="Error type (CannotJoinMeeting, TimeoutWaitingToStart, etc.)")


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
