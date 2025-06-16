"""Real-time audio handler for processing MeetingBaaS audio streams"""
import asyncio
import json
import time
import wave
import tempfile
import os
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime
import numpy as np
import whisper

from app.core.websocket_manager import manager
from app.services.ai_service import ai_service
from app.services.tts_service import tts_service
from app.models.database import get_db
from app.models.conversation import Session, Message, AIResponse

logger = logging.getLogger(__name__)


class RealtimeAudioHandler:
    """Handles real-time audio processing from MeetingBaaS"""
    
    def __init__(self):
        self.whisper_model = None
        self.speakers: Dict[str, Dict[str, Any]] = {}
        self.current_speaker: Optional[str] = None
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Audio processing settings
        self.SILENCE_THRESHOLD = 0.5  # seconds
        self.PROCESSING_INTERVAL = 2.0  # seconds
        self.SAMPLE_RATE = 16000
        self.SAMPLE_WIDTH = 2
        self.CHANNELS = 1
        
    def _load_whisper_model(self):
        """Lazy load Whisper model"""
        if self.whisper_model is None:
            logger.info("Loading Whisper model...")
            self.whisper_model = whisper.load_model("small")
            logger.info("Whisper model loaded")
    
    def _write_pcm_to_wav(self, pcm_bytes: bytes, wav_path: str) -> None:
        """Convert PCM audio to WAV format"""
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.SAMPLE_WIDTH)
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(pcm_bytes)
    
    async def process_speech_segment(
        self, 
        speaker_id: str, 
        audio_segment: bytes,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Process a speech segment and return transcript"""
        start_time = time.monotonic()
        
        # Check if audio is WAV format
        is_wav = audio_segment[:4] == b'RIFF'
        
        # Create temporary file for audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            tmpfile_path = tmpfile.name
            if is_wav:
                tmpfile.write(audio_segment)
            else:
                self._write_pcm_to_wav(audio_segment, tmpfile_path)
        
        try:
            # Ensure Whisper model is loaded
            self._load_whisper_model()
            
            # Transcribe audio
            result = self.whisper_model.transcribe(tmpfile_path)
            transcript_text = result.get("text", "").strip()
            processing_time = time.monotonic() - start_time
            
            if transcript_text:
                logger.info(f"Speaker {speaker_id}: {transcript_text} (processed in {processing_time:.2f}s)")
                
                # Store transcript in speaker data
                current_time = time.monotonic()
                if 'transcripts' not in self.speakers[speaker_id]:
                    self.speakers[speaker_id]['transcripts'] = []
                
                transcript_data = {
                    'text': transcript_text,
                    'timestamp': current_time,
                    'processing_time': processing_time
                }
                
                self.speakers[speaker_id]['transcripts'].append(transcript_data)
                
                # Save to database
                await self._save_message_to_db(
                    session_id=session_id,
                    speaker=self.speakers[speaker_id].get('name', f"Speaker {speaker_id}"),
                    text=transcript_text,
                    confidence=result.get("confidence", 0.0)
                )
                
                # Process with AI for insights
                await self._process_with_ai(session_id, transcript_text)
                
                return transcript_data
            else:
                logger.debug(f"No transcription for Speaker {speaker_id}")
                
        except Exception as e:
            logger.error(f"Transcription error: {type(e).__name__}: {e}")
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(tmpfile_path):
                    os.remove(tmpfile_path)
            except Exception as cleanup_err:
                logger.error(f"Error cleaning up temporary file: {cleanup_err}")
        
        return None
    
    async def _save_message_to_db(
        self, 
        session_id: str, 
        speaker: str, 
        text: str,
        confidence: float = None
    ) -> None:
        """Save message to database"""
        try:
            db = next(get_db())
            
            # Get or create session
            session = db.query(Session).filter_by(session_id=session_id).first()
            if not session:
                session = Session(session_id=session_id, status="active")
                db.add(session)
                db.commit()
            
            # Create message
            message = Message(
                session_id=session.id,
                speaker=speaker,
                text=text,
                confidence=confidence
            )
            db.add(message)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving message to database: {e}")
        finally:
            db.close()
    
    async def _process_with_ai(self, session_id: str, transcript: str) -> None:
        """Process transcript with AI for insights"""
        try:
            # Get recent conversation context
            db = next(get_db())
            session = db.query(Session).filter_by(session_id=session_id).first()
            
            if not session:
                return
            
            # Get recent messages for context
            recent_messages = db.query(Message).filter_by(
                session_id=session.id
            ).order_by(Message.timestamp.desc()).limit(10).all()
            
            # Build context
            context = []
            for msg in reversed(recent_messages):
                context.append(f"{msg.speaker}: {msg.text}")
            
            # Analyze with AI
            analysis = await ai_service.analyze_conversation(
                current_message=transcript,
                context=context,
                mode="executive_assistant"
            )
            
            if analysis and analysis.get("should_respond"):
                # Save AI response
                ai_response = AIResponse(
                    session_id=session.id,
                    prompt=transcript,
                    response=analysis["response"],
                    confidence=analysis.get("confidence", 0.0),
                    should_speak=True,
                    reasoning=analysis.get("reasoning", "")
                )
                db.add(ai_response)
                db.commit()
                
                # Generate TTS if needed
                if analysis.get("should_speak", False):
                    await self._generate_and_play_tts(analysis["response"])
                
                # Send to WebSocket clients
                await manager.broadcast({
                    "type": "ai_insight",
                    "data": {
                        "response": analysis["response"],
                        "confidence": analysis.get("confidence", 0.0),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error processing with AI: {e}")
    
    async def _generate_and_play_tts(self, text: str) -> None:
        """Generate and play TTS audio"""
        try:
            # Generate TTS
            audio_data = await tts_service.generate_speech(text)
            
            if audio_data:
                # Send audio to WebSocket clients
                await manager.broadcast({
                    "type": "tts_audio",
                    "data": {
                        "audio": audio_data,
                        "text": text,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
                
        except Exception as e:
            logger.error(f"Error generating TTS: {e}")
    
    async def handle_websocket_audio(self, websocket, session_id: str) -> None:
        """Handle incoming WebSocket audio stream from MeetingBaaS"""
        logger.info(f"Starting audio handler for session {session_id}")
        
        # Initialize session
        self.active_sessions[session_id] = {
            "started_at": datetime.utcnow(),
            "websocket": websocket
        }
        
        try:
            while True:
                msg = await websocket.receive()
                
                if msg["type"] == "websocket.disconnect":
                    logger.info("WebSocket disconnected by client")
                    break
                
                # Handle text messages (speaker info)
                if msg.get("text"):
                    try:
                        data = json.loads(msg["text"])
                        
                        # Process speaker information
                        if isinstance(data, list) and data and 'id' in data[0]:
                            for speaker_info in data:
                                speaker_id = speaker_info['id']
                                is_speaking = speaker_info.get('isSpeaking', False)
                                
                                if speaker_id not in self.speakers:
                                    self.speakers[speaker_id] = {
                                        'name': speaker_info.get('name', f"Speaker {speaker_id}"),
                                        'buffer': bytearray(),
                                        'last_voice_time': time.monotonic(),
                                        'is_speaking': is_speaking,
                                        'last_processed_time': 0,
                                        'transcripts': []
                                    }
                                else:
                                    self.speakers[speaker_id]['name'] = speaker_info.get('name', self.speakers[speaker_id].get('name'))
                                    self.speakers[speaker_id]['is_speaking'] = is_speaking
                                
                                if is_speaking:
                                    self.current_speaker = speaker_id
                                    logger.debug(f"Current speaker: {self.speakers[speaker_id]['name']}")
                                    
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in text message: {msg['text']}")
                
                # Handle audio bytes
                elif "bytes" in msg and msg["bytes"] is not None and self.current_speaker is not None:
                    audio_bytes = msg["bytes"]
                    self.speakers[self.current_speaker]['buffer'].extend(audio_bytes)
                    self.speakers[self.current_speaker]['last_voice_time'] = time.monotonic()
                    self.speakers[self.current_speaker]['is_speaking'] = True
                
                # Process audio buffers
                current_time = time.monotonic()
                for speaker_id, data in self.speakers.items():
                    # Process on interval or silence
                    should_process = False
                    
                    if data['is_speaking']:
                        # Check if we should process based on interval
                        if current_time - data.get('last_processed_time', 0) > self.PROCESSING_INTERVAL and len(data['buffer']) > 0:
                            should_process = True
                    
                    # Check for silence
                    if current_time - data['last_voice_time'] > self.SILENCE_THRESHOLD:
                        if len(data['buffer']) > 0:
                            should_process = True
                            data['is_speaking'] = False
                    
                    if should_process:
                        segment = bytes(data['buffer'])
                        data['buffer'] = bytearray()
                        data['last_processed_time'] = current_time
                        
                        # Process segment asynchronously
                        asyncio.create_task(
                            self.process_speech_segment(speaker_id, segment, session_id)
                        )
                        
        except Exception as e:
            logger.error(f"WebSocket error: {type(e).__name__}: {e}")
        finally:
            # Clean up session
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Clear speakers for this session
            self.speakers.clear()
            self.current_speaker = None
            
            logger.info(f"Audio handler stopped for session {session_id}")


# Global instance
realtime_audio_handler = RealtimeAudioHandler()
