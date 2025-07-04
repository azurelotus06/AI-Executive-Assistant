import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    elevenlabs_api_key: str = Field(..., env="ELEVENLABS_API_KEY")
    
    # Zoom Configuration
    zoom_meeting_id: Optional[str] = Field(None, env="ZOOM_MEETING_ID")
    zoom_passcode: Optional[str] = Field(None, env="ZOOM_PASSCODE")
    
    # MeetingBaaS Configuration
    meetingbaas_api_key: Optional[str] = Field(None, env="MEETINGBAAS_API_KEY")
    devtunnel_host: Optional[str] = Field(None, env="DEVTUNNEL_HOST")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    async_database_url: str = Field(..., env="ASYNC_DATABASE_URL")
    
    # Audio Settings
    audio_sample_rate: int = Field(32000, env="AUDIO_SAMPLE_RATE")
    audio_chunk_duration: float = Field(1.0, env="AUDIO_CHUNK_DURATION")  # seconds
    audio_silence_threshold: float = Field(0.01, env="AUDIO_SILENCE_THRESHOLD")
    
    # AI Settings
    ai_model: str = Field("gpt-4o-mini", env="AI_MODEL")
    ai_temperature: float = Field(0.7, env="AI_TEMPERATURE")
    ai_max_tokens: int = Field(150, env="AI_MAX_TOKENS")
    ai_context_window: int = Field(10, env="AI_CONTEXT_WINDOW")  # Number of previous messages to keep
    
    # TTS Settings
    tts_voice_id: str = Field("21m00Tcm4TlvDq8ikWAM", env="TTS_VOICE_ID")  # Default ElevenLabs voice
    tts_stability: float = Field(0.75, env="TTS_STABILITY")
    tts_similarity_boost: float = Field(0.75, env="TTS_SIMILARITY_BOOST")
    
    # Application Settings
    app_host: str = Field("0.0.0.0", env="APP_HOST")
    app_port: int = Field(8000, env="APP_PORT")
    debug: bool = Field(False, env="DEBUG")
    
    # Security
    secret_key: str = Field("your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Speech-to-Text Configuration
    speech_to_text: dict = Field(
        default={"provider": "Default"},
        env="SPEECH_TO_TEXT_CONFIG"
    )
    GLADIA_API_KEY: str = Field(..., env="GLADIA_API_KEY")
    
    # Development Settings
    SKIP_GLADIA_INIT: bool = Field(False, env="SKIP_GLADIA_INIT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
