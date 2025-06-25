"""Real-time audio handler for MeetingBaaS WebSocket streams"""
import asyncio
import json
import logging
import wave
import tempfile
import os
from datetime import datetime
from typing import Dict, Optional, List
from fastapi import WebSocket

from app.services.audio_processor import AudioProcessor
from app.services.meeting_service import MeetingBaaSService
from app.core.config import settings
from app.models.conversation import Meeting

logger = logging.getLogger(__name__)

class RealTimeAudioHandler:
    """Handles real-time audio streams from MeetingBaaS"""
    
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.meeting_service = MeetingBaaSService()
        self.active_sessions: Dict[str, Dict] = {}
        self.speakers: Dict[str, Dict] = {}
        self.current_speaker: Optional[str] = None
        self.silence_threshold = 0.5  # seconds of silence to trigger processing
        self.processing_interval = 2.0  # max time between processing chunks
        self.whisper_model = None
        
    async def initialize(self):
        """Initialize the handler and load models"""
        try:
            import whisper
            self.whisper_model = whisper.load_model("small")
            logger.info("Loaded Whisper model for local transcription")
        except ImportError:
            logger.warning("Whisper not available, will use API only")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")

    async def handle_websocket_input(self, websocket: WebSocket):
        """Handle incoming WebSocket connection from MeetingBaaS"""
        await websocket.accept()
        logger.info("WebSocket input connection accepted for real-time audio")
        
        try:
            while True:
                message = await websocket.receive()
                print("Websocket input message: ", list(message.keys()))
                print("Websocket message: ", message)
                
                # if message.get("type") == "websocket.disconnect":
                #     logger.info("WebSocket disconnected by client")
                #     break
                    
                # if message.get("text"):
                #     await self._handle_text_message(message["text"])
                # elif message.get("bytes") and self.current_speaker:
                #     await self._handle_audio_data(
                #         self.current_speaker, 
                #         message["bytes"]
                #     )

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            try:
                if websocket.client_state != "disconnected":
                    await websocket.close()
                    logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
                
    async def handle_websocket_output(self, websocket: WebSocket):
        """Handle incoming WebSocket connection from MeetingBaaS"""
        await websocket.accept()
        logger.info("WebSocket connection accepted for real-time audio")
        
        try:
            while True:
                message = await websocket.receive()
                print("Websocket output message: ", list(message.keys()))
                
                if message.get("type") == "websocket.disconnect":
                    logger.info("WebSocket disconnected by client")
                    break
                    
                if message.get("text"):
                    await self._handle_text_message(message["text"])
                elif message.get("bytes") and self.current_speaker:
                    await self._handle_audio_data(
                        self.current_speaker, 
                        message["bytes"]
                    )

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            try:
                if websocket.client_state != "disconnected":
                    await websocket.close()
                    logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

    async def _handle_text_message(self, message_text: str):
        """Handle text messages containing speaker metadata"""
        try:
            data = json.loads(message_text)
            if isinstance(data, list) and data and 'id' in data[0]:
                for speaker_info in data:
                    speaker_id = speaker_info['id']
                    is_speaking = speaker_info.get('isSpeaking', False)
                    
                    if speaker_id not in self.speakers:
                        self.speakers[speaker_id] = {
                            'name': speaker_info.get('name'),
                            'buffer': bytearray(),
                            'last_voice_time': datetime.now().timestamp(),
                            'is_speaking': is_speaking,
                            'transcripts': []
                        }
                    else:
                        self.speakers[speaker_id]['is_speaking'] = is_speaking
                        self.speakers[speaker_id]['name'] = speaker_info.get(
                            'name', 
                            self.speakers[speaker_id].get('name')
                        )
                    
                    if is_speaking:
                        self.current_speaker = speaker_id
                        logger.info(f"Current speaker: {self.speakers[speaker_id]['name']}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in message: {message_text}")
        except Exception as e:
            logger.error(f"Error processing text message: {e}")

    async def _handle_audio_data(self, speaker_id: str, audio_bytes: bytes):
        """Handle incoming audio data for a speaker"""
        try:
            if speaker_id not in self.speakers:
                logger.warning(f"Received audio for unknown speaker: {speaker_id}")
                return
                
            speaker = self.speakers[speaker_id]
            speaker['buffer'].extend(audio_bytes)
            speaker['last_voice_time'] = datetime.now().timestamp()
            
            # Process if we have enough silence or max interval reached
            current_time = datetime.now().timestamp()
            time_since_last = current_time - speaker['last_voice_time']
            
            if (len(speaker['buffer']) > 0 and 
                (time_since_last > self.silence_threshold or 
                 len(speaker['buffer']) > self.sample_rate * 10)):  # Max 10 sec
                
                segment = bytes(speaker['buffer'])
                speaker['buffer'] = bytearray()
                
                transcript = await self._process_audio_segment(speaker_id, segment)
                if transcript:
                    speaker['transcripts'].append({
                        'text': transcript,
                        'timestamp': current_time
                    })
                    
                    # TODO: Send to GPT for analysis
                    # TODO: Queue TTS response if needed

        except Exception as e:
            logger.error(f"Error handling audio data: {e}")

    async def _process_audio_segment(self, speaker_id: str, audio_data: bytes) -> Optional[str]:
        """Process an audio segment and return transcription"""
        try:
            is_wav = audio_data[:4] == b'RIFF'
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
                tmp_path = tmpfile.name
                if is_wav:
                    tmpfile.write(audio_data)
                else:
                    self._write_pcm_to_wav(audio_data, tmp_path)
            
            try:
                if self.whisper_model:
                    result = self.whisper_model.transcribe(tmp_path)
                    transcript = result.get("text", "").strip()
                else:
                    # Fallback to API
                    transcript = await self.audio_processor.transcribe_audio(tmp_path)
                
                if transcript:
                    logger.info(f"Speaker {speaker_id}: {transcript}")
                    return transcript
                    
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except Exception as e:
            logger.error(f"Error processing audio segment: {e}")
            return None

    def _write_pcm_to_wav(self, pcm_bytes: bytes, wav_path: str, 
                         sample_rate: int = 16000, sample_width: int = 2, 
                         channels: int = 1):
        """Convert PCM audio to WAV format"""
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)

    async def generate_ai_response(self, transcript: str, context: Dict) -> str:
        """Generate AI response using GPT-4"""
        # TODO: Implement with proper prompt engineering
        return "AI response placeholder"

    async def send_tts_response(self, text: str):
        """Send text to TTS service"""
        # TODO: Implement ElevenLabs integration
        pass

# Global instance
audio_handler = RealTimeAudioHandler()
