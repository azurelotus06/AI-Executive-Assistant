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
from app.services.ai_service import ai_service
from app.services.tts_service import tts_service
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
        self.gladia_client = None
        self.is_gladia_ready = False
        self.output_websockets: List[WebSocket] = []
        self.sample_rate = 16000  # Default sample rate for audio processing
        self._gladia_initialization_lock = asyncio.Lock()
        
    async def initialize_gladia(self) -> bool:
        """Initialize Gladia client when webhook status is 'in_call_recording'"""
        async with self._gladia_initialization_lock:
            if self.is_gladia_ready:
                return True

            try:
                from app.core.config import settings
                from app.services.gladia_client import GladiaClient

                if not self.gladia_client:
                    self.gladia_client = GladiaClient(settings.GLADIA_API_KEY)
                    self.gladia_client.on_transcription(self._handle_transcription)

                if await self.gladia_client.init_session():
                    self.is_gladia_ready = True
                    logger.info("Gladia initialized successfully")
                    return True
                else:
                    logger.error("Failed to initialize Gladia session")
                    return False

            except Exception as e:
                logger.error(f"Error initializing Gladia: {e}")
                return False

    async def handle_websocket_input(self, websocket: WebSocket):
        """Handle incoming WebSocket connection from MeetingBaaS"""
        await websocket.accept()
        logger.info("WebSocket input connection accepted for real-time audio")
        
        try:
            # No Gladia initialization here - moved to webhook handler
            if not self.is_gladia_ready:
                logger.info("Gladia not initialized - waiting for webhook trigger")

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
                
                # Clean up Gladia session if no more active connections
                if self.gladia_client and len(self.output_websockets) == 0:
                    await self.gladia_client.end_session()
                    self.is_gladia_ready = False
                    logger.info("Gladia session cleaned up")
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
                
    async def handle_websocket_output(self, websocket: WebSocket):
        """Handle incoming WebSocket connection from MeetingBaaS"""
        await websocket.accept()
        logger.info("WebSocket output connection accepted for real-time audio")
        self.output_websockets.append(websocket)
        
        try:
            # Ensure Gladia is initialized before processing audio
            if not self.is_gladia_ready:
                logger.info("Waiting for Gladia initialization...")
                if not await self.initialize_gladia():
                    logger.error("Failed to initialize Gladia, closing connection")
                    await websocket.close()
                    return

            while True:
                message = await websocket.receive()
                print("Websocket output message: ", list(message.keys()))
                print("self.current_speaker: ", self.current_speaker)
                print("self.is_gladia_ready: ", self.is_gladia_ready)
                
                if message.get("type") == "websocket.disconnect":
                    logger.info("WebSocket disconnected by client")
                    break
                    
                if message.get("text"):
                    await self._handle_text_message(message["text"])
                elif message.get("bytes") and self.is_gladia_ready:
                    await self._handle_audio_data(
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

    async def _handle_audio_data(self, audio_bytes: bytes):
        """Handle incoming audio data for a speaker"""
        try:
            print("audio_bytes length: ", len(audio_bytes))
            if 'Unknown' not in self.speakers:
                self.speakers['Unknown'] = {
                    'buffer': bytearray(),
                    'last_voice_time': datetime.now().timestamp(),
                    'is_speaking': False,
                    'transcripts': []
                }
            speaker = self.speakers['Unknown']
            speaker['buffer'].extend(audio_bytes)
            speaker['last_voice_time'] = datetime.now().timestamp()
            
            # Process if we have enough silence or max interval reached
            current_time = datetime.now().timestamp()
            time_since_last = current_time - speaker['last_voice_time']
            print("time_since_last: ", time_since_last)
            print("len(speaker['buffer']): ", len(speaker['buffer']))
            
            if (len(speaker['buffer']) > 0 and 
                (time_since_last > self.silence_threshold or 
                 len(speaker['buffer']) > self.sample_rate * 2)):  # Max 2 sec - 32000
                
                segment = bytes(speaker['buffer'])
                speaker['buffer'] = bytearray()
                
                transcript = await self._process_audio_segment(segment)
                print("transcript: ", transcript)
                if transcript:
                    speaker['transcripts'].append({
                        'text': transcript,
                        'timestamp': current_time
                    })
                    print("speaker['transcripts']: ", speaker['transcripts'])
                    
                    # Analyze with AI service
                    ai_response = await ai_service.analyze_conversation(
                        transcript=transcript,
                        speaker='Unknown'
                    )
                    
                    if ai_response and ai_response.get('should_speak'):
                        # Queue TTS response
                        await tts_service.queue_tts(
                            text=ai_response['response'],
                            voice_id=settings.tts_voice_id,
                            websockets=self.output_websockets
                        )

        except Exception as e:
            logger.error(f"Error handling audio data: {e}")

    async def _process_audio_segment(self, audio_data: bytes) -> Optional[str]:
        """Process an audio segment using Gladia and return transcription"""
        try:
            if not self.is_gladia_ready or not self.gladia_client:
                logger.warning("Gladia not ready, skipping audio processing")
                return None
                
            # # Convert to WAV if needed
            # if audio_data[:4] != b'RIFF':
            #     temp_path = None
            #     try:
            #         # Create temp file with explicit close
            #         tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            #         temp_path = tmpfile.name
            #         tmpfile.close()  # Close immediately after creation
                    
            #         # Write WAV data
            #         self._write_pcm_to_wav(audio_data, temp_path)
                    
            #         # Read with retry logic
            #         max_retries = 3
            #         for attempt in range(max_retries):
            #             try:
            #                 with open(temp_path, 'rb') as f:
            #                     audio_data = f.read()
            #                 break
            #             except PermissionError as pe:
            #                 if attempt == max_retries - 1:
            #                     raise
            #                 await asyncio.sleep(0.1 * (attempt + 1))
                    
            #     finally:
            #         # Ensure cleanup
            #         if temp_path and os.path.exists(temp_path):
            #             try:
            #                 os.remove(temp_path)
            #             except PermissionError as pe:
            #                 logger.warning(f"Could not delete temp file {temp_path}: {pe}")
            #                 # Schedule delayed cleanup
            #                 asyncio.create_task(self._delayed_file_cleanup(temp_path))
            
            # # Create event to wait for transcription
            # transcription_event = asyncio.Event()
            # transcription_result = None
            
            # # Temporary handler to capture result
            # def temp_handler(text: str, is_final: bool):
            #     nonlocal transcription_result
            #     if is_final and text:
            #         transcription_result = text
            #         transcription_event.set()
            
            # # Add temporary handler
            # original_handler = self.gladia_client.on_transcription
            # self.gladia_client.on_transcription = temp_handler
            
            # Send to Gladia
            success = await self.gladia_client.send_audio_chunk(audio_data)
            print("Sent to Gladia")
            if not success:
                logger.error("Failed to send audio to Gladia")
                return None
            
        except Exception as e:
            logger.error(f"Error processing audio segment: {e}")
            return None
            
    async def _handle_transcription(self, text: str, is_final: bool):
        """Handle transcription results from Gladia"""
        try:
            print("_handle_transcription text: ", text)
            if not text:
                return
                
            # speaker = self.speakers.get(self.current_speaker, {})
            # speaker_name = speaker.get('name', 'Unknown')
            speaker_name = 'Unknown'
            
            logger.info(f"Transcription from {speaker_name} ({'final' if is_final else 'partial'}): {text}")
            print(f"[TRANSCRIPTION] {speaker_name}: {text}")  # Print to console
            
            # Broadcast to all output WebSockets
            message = {
                "type": "transcription",
                "speaker_id": self.current_speaker,
                "speaker_name": speaker_name,
                "text": text,
                "is_final": is_final,
                "timestamp": datetime.now().isoformat()
            }
            
            for ws in self.output_websockets:
                try:
                    if ws.client_state != "disconnected":
                        await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending transcription to WebSocket: {e}")
                    if ws in self.output_websockets:  # Check if still exists
                        self.output_websockets.remove(ws)
                    
        except Exception as e:
            logger.error(f"Error handling transcription: {e}")

    def _write_pcm_to_wav(self, pcm_bytes: bytes, wav_path: str, 
                         sample_rate: int = 16000, sample_width: int = 2, 
                         channels: int = 1):
        """Convert PCM audio to WAV format"""
        try:
            with wave.open(wav_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_bytes)
        except Exception as e:
            logger.error(f"Error writing WAV file {wav_path}: {e}")
            raise

    async def _delayed_file_cleanup(self, file_path: str, delay: float = 1.0):
        """Attempt file cleanup after a delay"""
        await asyncio.sleep(delay)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed delayed cleanup of {file_path}: {e}")

    async def cleanup(self):
        """Clean up resources and close Gladia session"""
        try:
            if self.gladia_client:
                await self.gladia_client.end_session()
                logger.info("Gladia session ended")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

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
