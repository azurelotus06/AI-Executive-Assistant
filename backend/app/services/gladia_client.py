"""Gladia API client for real-time transcription"""
import json
import base64
import asyncio
import logging
from typing import Optional, Callable, Awaitable, Union, Any
import aiohttp
import websockets
from websockets.legacy.client import WebSocketClientProtocol

logger = logging.getLogger(__name__)

class GladiaClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.gladia.io"
        self.ws: Optional[WebSocketClientProtocol] = None  # WebSocket connection
        self.session_id: Optional[str] = None
        self.on_transcription_callback: Optional[Callable[[str, bool], Awaitable[None]]] = None
        
    async def cleanup_existing_sessions(self) -> bool:
        """Attempt to cleanup any existing sessions"""
        try:
            headers = {
                "x-gladia-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            cleanup_success = False
            
            # First try to list and cleanup all existing sessions (if API supports it)
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.api_url}/v2/live/sessions",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            sessions = await response.json()
                            logger.info(f"Found {len(sessions)} active sessions")
                            
                            # Try to close each session
                            for session_info in sessions:
                                session_id = session_info.get('id')
                                if session_id:
                                    try:
                                        async with session.delete(
                                            f"{self.api_url}/v2/live/{session_id}",
                                            headers=headers
                                        ) as delete_response:
                                            if delete_response.status == 200:
                                                logger.info(f"Cleaned up session: {session_id}")
                                                cleanup_success = True
                                            else:
                                                logger.warning(f"Failed to cleanup session {session_id}: {delete_response.status}")
                                    except Exception as e:
                                        logger.warning(f"Error cleaning up session {session_id}: {e}")
                        else:
                            logger.info("Could not retrieve active sessions list")
            except Exception as e:
                logger.warning(f"Error during session listing: {e}")
            
            # If we couldn't list sessions, at least try to cleanup our own session if it exists
            if not cleanup_success and self.session_id:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.delete(
                            f"{self.api_url}/v2/live/{self.session_id}",
                            headers=headers
                        ) as response:
                            if response.status == 200:
                                logger.info(f"Cleaned up our session: {self.session_id}")
                                cleanup_success = True
                            else:
                                logger.warning(f"Failed to cleanup our session {self.session_id}: {response.status}")
                except Exception as e:
                    logger.warning(f"Error cleaning up our session: {e}")
            
            return cleanup_success
                        
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            return False
        
    async def init_session(self) -> bool:
        """Initialize a streaming session with Gladia"""
        try:
            headers = {
                "x-gladia-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "encoding": "wav/pcm",
                "bit_depth": 16,
                "sample_rate": 16000,
                "channels": 1,
                "model": "accurate",
                "language_config": {
                    "languages": ["en"],
                    "code_switching": False
                },
                "messages_config": {
                    "receive_partial_transcripts": True,
                    "receive_final_transcripts": True
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/v2/live",
                    headers=headers,
                    json=payload
                ) as response:
                    response_text = await response.text()
                    
                    if response.status in [200, 201]:  # Accept both 200 and 201 as success
                        try:
                            data = json.loads(response_text)
                            self.session_id = data["id"]
                            ws_url = data["url"]
                            
                            logger.info(f"Gladia session initialized successfully: {self.session_id}")
                            logger.info(f"WebSocket URL: {ws_url}")
                            
                            # Connect to WebSocket
                            success = await self.connect_websocket(ws_url)
                            return success
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.error(f"Failed to parse successful response: {e}")
                            logger.error(f"Response text: {response_text}")
                            return False
                    else:
                        logger.error(f"Failed to initialize session (HTTP {response.status}): {response_text}")
                        
                        # Log detailed error info if available
                        try:
                            error_data = json.loads(response_text)
                            logger.error(f"Gladia API error details: {error_data}")
                        except json.JSONDecodeError:
                            logger.error(f"Could not parse error response as JSON")
                            
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to initialize Gladia session: {e}")
            return False
    
    async def connect_websocket(self, url: str) -> bool:
        """Connect to Gladia's WebSocket for real-time transcription"""
        try:
            logger.info(f"Connecting to Gladia WebSocket at: {url}")
            self.ws = await websockets.connect(url)
            logger.info(f"Successfully connected to Gladia WebSocket: {self.ws}")
            
            # Start listening for messages
            asyncio.create_task(self._listen_to_websocket())
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False
            
    async def _listen_to_websocket(self):
        """Listen for messages from Gladia WebSocket"""
        try:
            if self.ws is None:
                logger.error("WebSocket is None, cannot listen")
                return
                
            logger.info("Starting WebSocket message listener")
            async for message in self.ws:
                try:
                    logger.info("Received WebSocket message")
                    logger.debug(f"Received WebSocket message: {message[:200]}...")  # Log first 200 chars
                    data = json.loads(message)
                    
                    if data.get("type") == "transcript":
                        transcript_data = data.get("data", {})
                        utterance = transcript_data.get("utterance", {})
                        is_final = transcript_data.get("is_final", False)
                        text = utterance.get("text", "")
                        
                        if text:
                            logger.info(f"Received transcription (is_final={is_final}): {text}")
                            
                            if self.on_transcription_callback:
                                await self.on_transcription_callback(text, is_final)
                        else:
                            logger.warning("Received empty transcription")
                    else:
                        logger.info(f"Received non-transcript message: {data.get('type')}")
                                
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message: {message[:200]}...")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed: {e}")
            logger.error(f"Close code: {e.code}, reason: {e.reason}")
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
            if hasattr(e, 'code'):
                logger.error(f"Error code: {e.code}")
            if hasattr(e, 'reason'):
                logger.error(f"Error reason: {e.reason}")
            
    async def send_audio_chunk(self, audio_data: bytes) -> bool:
        """Send audio chunk to Gladia for transcription"""
        if not self.ws:
            logger.warning("WebSocket not connected, ignoring audio chunk")
            return False
            
        try:
            # Convert audio data to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            chunk_size = len(audio_data)
            print("chunk_size: ", chunk_size)
            
            # Send audio chunk message
            message = {
                "type": "audio_chunk",
                "data": {
                    "chunk": audio_base64
                }
            }
            
            logger.info(f"Sending audio chunk (size: {chunk_size} bytes)")
            await self.ws.send(json.dumps(message))
            logger.debug("Audio chunk sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending audio chunk to Gladia: {e}")
            if hasattr(e, 'code'):
                logger.error(f"Error code: {e.code}")
            if hasattr(e, 'reason'):
                logger.error(f"Error reason: {e.reason}")
            return False
            
    def on_transcription(self, callback: Callable[[str, bool], Awaitable[None]]):
        """Set callback for transcription results"""
        self.on_transcription_callback = callback
        
    async def end_session(self) -> bool:
        """End transcription session and wait for confirmation"""
        try:
            if self.ws and not self.ws.closed:
                # Send stop recording message
                await self.ws.send(json.dumps({"type": "stop_recording"}))
                # Wait for graceful closure
                await asyncio.wait_for(self.ws.close(), timeout=2.0)
                logger.info("Gladia session ended successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False
        finally:
            self.ws = None
            self.session_id = None
