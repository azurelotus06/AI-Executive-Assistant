import asyncio
import logging
import numpy as np
import base64
import io
import wave
from typing import Optional, List, Dict, Any
import openai
from openai import AsyncOpenAI
import webrtcvad
import librosa
import sounddevice as sd

from app.core.config import settings

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Handles audio processing, VAD, and speech-to-text conversion"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3
        self.sample_rate = settings.audio_sample_rate
        self.chunk_duration = settings.audio_chunk_duration
        self.silence_threshold = settings.audio_silence_threshold
        self.is_muted = False
        self.is_recording = False
        self.audio_buffer = []
        self.speech_buffer = []
        self.silence_counter = 0
        self.max_silence_chunks = 10  # Number of silent chunks before processing
        
    def set_muted(self, muted: bool):
        """Set mute status"""
        self.is_muted = muted
        logger.info(f"Audio processor {'muted' if muted else 'unmuted'}")
    
    def is_healthy(self) -> bool:
        """Check if the audio processor is healthy"""
        try:
            return bool(self.client.api_key)
        except Exception:
            return False
    
    def preprocess_audio(self, audio_data: bytes) -> np.ndarray:
        """Preprocess raw audio data"""
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float32 and normalize
            audio_float = audio_array.astype(np.float32) / 32768.0
            
            # Resample if necessary
            if len(audio_float) > 0:
                # Ensure we have the right sample rate
                target_length = int(self.sample_rate * self.chunk_duration)
                if len(audio_float) != target_length:
                    audio_float = librosa.resample(
                        audio_float, 
                        orig_sr=len(audio_float) / self.chunk_duration,
                        target_sr=self.sample_rate
                    )
            
            return audio_float
            
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            return np.array([])
    
    def detect_speech(self, audio_data: np.ndarray) -> bool:
        """Detect if audio contains speech using VAD"""
        try:
            # Convert to 16-bit PCM for VAD
            audio_int16 = (audio_data * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()
            
            # VAD requires specific frame sizes (10, 20, or 30ms)
            frame_duration = 30  # ms
            frame_size = int(self.sample_rate * frame_duration / 1000)
            
            speech_frames = 0
            total_frames = 0
            
            for i in range(0, len(audio_int16) - frame_size, frame_size):
                frame = audio_int16[i:i + frame_size].tobytes()
                if len(frame) == frame_size * 2:  # 2 bytes per sample
                    is_speech = self.vad.is_speech(frame, self.sample_rate)
                    if is_speech:
                        speech_frames += 1
                    total_frames += 1
            
            if total_frames == 0:
                return False
            
            speech_ratio = speech_frames / total_frames
            return speech_ratio > 0.3  # At least 30% of frames contain speech
            
        except Exception as e:
            logger.error(f"Error in speech detection: {e}")
            # Fallback to simple energy-based detection
            return np.mean(np.abs(audio_data)) > self.silence_threshold
    
    def audio_to_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        """Convert numpy array to WAV bytes for Whisper API"""
        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {e}")
            return b""
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper"""
        try:
            if len(audio_data) == 0:
                return None
            
            # Convert to WAV format
            wav_bytes = self.audio_to_wav_bytes(audio_data)
            if not wav_bytes:
                return None
            
            # Create a file-like object for the API
            audio_file = io.BytesIO(wav_bytes)
            audio_file.name = "audio.wav"
            
            # Call Whisper API
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en",  # Can be made configurable
                response_format="json"
            )
            
            transcript = response.text.strip()
            if transcript and len(transcript) > 3:  # Filter out very short transcripts
                logger.info(f"Transcribed: {transcript}")
                return transcript
            
            return None
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None
    
    async def process_audio_chunk(self, audio_data_b64: str) -> Optional[str]:
        """Process a single audio chunk from base64 encoded data"""
        try:
            if self.is_muted:
                return None
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data_b64)
            
            # Preprocess audio
            audio_array = self.preprocess_audio(audio_bytes)
            if len(audio_array) == 0:
                return None
            
            # Add to buffer
            self.audio_buffer.extend(audio_array)
            
            # Detect speech
            has_speech = self.detect_speech(audio_array)
            
            if has_speech:
                self.speech_buffer.extend(audio_array)
                self.silence_counter = 0
                self.is_recording = True
            else:
                if self.is_recording:
                    self.silence_counter += 1
                    # Add some silence to the buffer for natural pauses
                    self.speech_buffer.extend(audio_array)
            
            # Process accumulated speech if we have enough silence or buffer is full
            if (self.is_recording and 
                (self.silence_counter >= self.max_silence_chunks or 
                 len(self.speech_buffer) > self.sample_rate * 10)):  # Max 10 seconds
                
                speech_data = np.array(self.speech_buffer)
                self.speech_buffer = []
                self.silence_counter = 0
                self.is_recording = False
                
                # Transcribe the speech
                transcript = await self.transcribe_audio(speech_data)
                return transcript
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    async def start_recording(self) -> bool:
        """Start recording from microphone (for testing)"""
        try:
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                
                # Add audio data to buffer
                audio_data = indata[:, 0]  # Take first channel
                asyncio.create_task(self.process_audio_chunk(
                    base64.b64encode(audio_data.tobytes()).decode()
                ))
            
            # Start recording
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                callback=audio_callback,
                blocksize=int(self.sample_rate * self.chunk_duration)
            )
            
            self.stream.start()
            logger.info("Started microphone recording")
            return True
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop recording from microphone"""
        try:
            if hasattr(self, 'stream') and self.stream:
                self.stream.stop()
                self.stream.close()
                logger.info("Stopped microphone recording")
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
    
    def clear_buffers(self):
        """Clear audio buffers"""
        self.audio_buffer = []
        self.speech_buffer = []
        self.silence_counter = 0
        self.is_recording = False
        logger.info("Audio buffers cleared")
