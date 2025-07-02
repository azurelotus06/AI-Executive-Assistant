import asyncio
import logging
import httpx
import base64
from typing import Optional, Dict, Any, List
from fastapi import WebSocket
import io
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    """Handles text-to-speech conversion using ElevenLabs API"""
    
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.tts_voice_id
        self.stability = settings.tts_stability
        self.similarity_boost = settings.tts_similarity_boost
        self.base_url = "https://api.elevenlabs.io/v1"
        self.is_muted = False
        
        # HTTP client for async requests
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
        )
    
    def set_muted(self, muted: bool):
        """Set mute status for TTS"""
        self.is_muted = muted
        logger.info(f"TTS service {'muted' if muted else 'unmuted'}")
    
    def is_healthy(self) -> bool:
        """Check if the TTS service is healthy"""
        try:
            return bool(self.api_key and self.voice_id)
        except Exception:
            return False
    
    async def get_available_voices(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of available voices from ElevenLabs"""
        try:
            response = await self.client.get(f"{self.base_url}/voices")
            response.raise_for_status()
            
            voices_data = response.json()
            voices = []
            
            for voice in voices_data.get("voices", []):
                voices.append({
                    "voice_id": voice.get("voice_id"),
                    "name": voice.get("name"),
                    "category": voice.get("category"),
                    "description": voice.get("description", ""),
                    "preview_url": voice.get("preview_url")
                })
            
            logger.info(f"Retrieved {len(voices)} available voices")
            return voices
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return None
    
    async def generate_speech(self, text: str, voice_id: str = None) -> Optional[bytes]:
        """Generate speech from text using ElevenLabs API"""
        try:
            if self.is_muted:
                logger.info("TTS is muted, skipping speech generation")
                return None
            
            if not text or not text.strip():
                logger.warning("Empty text provided for TTS")
                return None
            
            # Use provided voice_id or default
            voice_id = voice_id or self.voice_id
            
            # Prepare request payload
            payload = {
                "text": text.strip(),
                "model_id": "eleven_monolingual_v1",  # Can be made configurable
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                    "style": 0.0,  # More neutral style for professional settings
                    "use_speaker_boost": True
                }
            }
            
            # Make API request
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            # Return audio data
            audio_data = response.content
            logger.info(f"Generated speech for text: '{text[:50]}...' ({len(audio_data)} bytes)")
            return audio_data
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in TTS generation: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
    
    async def generate_speech_stream(self, text: str, voice_id: str = None) -> Optional[bytes]:
        """Generate speech with streaming for faster response"""
        try:
            if self.is_muted:
                return None
            
            voice_id = voice_id or self.voice_id
            
            payload = {
                "text": text.strip(),
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
            
            audio_chunks = []
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    audio_chunks.append(chunk)
            
            audio_data = b"".join(audio_chunks)
            logger.info(f"Generated streaming speech: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error in streaming TTS: {e}")
            # Fallback to regular generation
            return await self.generate_speech(text, voice_id)
    
    def preprocess_text_for_speech(self, text: str) -> str:
        """Preprocess text to make it more suitable for speech synthesis"""
        if not text:
            return ""
        
        # Remove excessive punctuation
        text = text.replace("...", ".")
        text = text.replace("!!", "!")
        text = text.replace("??", "?")
        
        # Add pauses for better speech flow
        text = text.replace(". ", ". ")  # Ensure space after periods
        text = text.replace(", ", ", ")  # Ensure space after commas
        
        # Handle common abbreviations
        abbreviations = {
            "AI": "A I",
            "API": "A P I",
            "ROI": "R O I",
            "KPI": "K P I",
            "CEO": "C E O",
            "CTO": "C T O",
            "CFO": "C F O",
            "Q1": "Q one",
            "Q2": "Q two",
            "Q3": "Q three",
            "Q4": "Q four"
        }
        
        for abbr, replacement in abbreviations.items():
            text = text.replace(abbr, replacement)
        
        return text.strip()
    
    async def generate_executive_speech(self, text: str, voice_id: str, urgency: str = "urgent") -> Optional[bytes]:
        """Generate speech optimized for executive communication"""
        try:
            # Preprocess text for better speech
            processed_text = self.preprocess_text_for_speech(text)
            
            # Adjust voice settings based on urgency
            voice_settings = {
                "stability": self.stability,
                "similarity_boost": self.similarity_boost,
                "style": 0.0,
                "use_speaker_boost": True
            }
            
            if urgency == "urgent":
                voice_settings["stability"] = min(self.stability + 0.1, 1.0)
                voice_settings["style"] = 0.2  # Slightly more expressive
            elif urgency == "calm":
                voice_settings["stability"] = max(self.stability - 0.1, 0.0)
                voice_settings["style"] = -0.1  # More neutral
            
            payload = {
                "text": processed_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": voice_settings
            }
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating executive speech: {e}")
            return None
    
    async def test_voice_quality(self, test_text: str = None) -> Dict[str, Any]:
        """Test voice quality with a sample text"""
        test_text = test_text or "This is a test of the AI executive assistant voice quality."
        
        try:
            audio_data = await self.generate_speech(test_text)
            
            if audio_data:
                return {
                    "success": True,
                    "audio_size": len(audio_data),
                    "test_text": test_text,
                    "voice_id": self.voice_id
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate audio"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def queue_tts(self, text: str, voice_id: str, websockets: List[WebSocket]) -> bool:
        """Queue text for TTS processing and send to WebSockets"""
        try:
            print("Start: Queue text for TTS processing and send to WebSockets")
            if not text or not websockets:
                logger.error(f"Error text: {text}, websockets: {websockets}")
                return False
            
            voice_id = voice_id or self.voice_id
            # Generate speech audio
            audio_data = await self.generate_executive_speech(text, voice_id)
            print(f"len(audio_data): {len(audio_data)}, len(text): {len(text)}")
            if not audio_data:
                return False
                
            # Send to all connected WebSockets
            for ws in websockets:
                try:
                    if ws.client_state != "disconnected":
                        await ws.send(audio_data)
                except Exception as e:
                    logger.error(f"Error sending TTS audio to WebSocket: {e}")
                    continue
                    
            return True
            
        except Exception as e:
            logger.error(f"Error in TTS queue: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        try:
            await self.client.aclose()
            logger.info("TTS service client closed")
        except Exception as e:
            logger.error(f"Error closing TTS client: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            if hasattr(self, 'client') and self.client and not self.client.is_closed:
                # Try to get the current event loop
                try:
                    loop = asyncio.get_running_loop()
                    # Schedule the coroutine to run in the existing loop
                    loop.create_task(self.client.aclose())
                except RuntimeError:
                    # No running event loop, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.client.aclose())
                    loop.close()
        except Exception:
            # Silently ignore any errors during cleanup
            pass


# Create global instance
tts_service = TTSService()
