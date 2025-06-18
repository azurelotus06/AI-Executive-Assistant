"""Conversation models for storing meeting transcripts and AI interactions"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base

class Session(Base):
    """Meeting session model"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    meeting_id = Column(String(255), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active")
    
    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    ai_responses = relationship("AIResponse", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    """Conversation message model"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    speaker = Column(String(255))
    text = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    confidence = Column(Float, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="messages")

class AIResponse(Base):
    """AI response model"""
    __tablename__ = "ai_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    prompt = Column(Text)
    response = Column(Text)
    confidence = Column(Float)
    should_speak = Column(Boolean, default=False)
    reasoning = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    tts_generated = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("Session", back_populates="ai_responses")

class AudioChunk(Base):
    """Audio chunk storage model (optional, for debugging)"""
    __tablename__ = "audio_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    chunk_data = Column(Text)  # Base64 encoded audio
    duration = Column(Float)
    has_speech = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Meeting(Base):
    """Meeting model for MeetingBaaS integration"""
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(String(255), unique=True, index=True)
    meeting_url = Column(String(500))
    bot_name = Column(String(255))
    status = Column(String(50))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    transcript = Column(JSON, nullable=True)  # Store full transcript as JSON
    summary = Column(Text, nullable=True)
    attendees = Column(JSON, nullable=True)
    recording_url = Column(String(500), nullable=True)
    status_details = Column(JSON, nullable=True)  # Detailed status info
    speakers = Column(JSON, nullable=True)  # List of speakers
    error_details = Column(JSON, nullable=True)  # Error details if meeting failed
