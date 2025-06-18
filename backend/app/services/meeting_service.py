"""MeetingBaaS service for joining and managing Zoom meetings"""
import os
import json
import asyncio
import aiohttp
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import get_db
from app.models.conversation import Meeting

logger = logging.getLogger(__name__)


class MeetingBaaSService:
    """Service for managing meetings via MeetingBaaS API"""
    
    def __init__(self):
        self.api_key = settings.meetingbaas_api_key
        self.webhook_host = settings.devtunnel_host
        self.base_url = "https://api.meetingbaas.com"
        self.active_bots: Dict[str, Dict[str, Any]] = {}
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for MeetingBaaS API requests"""
        return {
            "Content-Type": "application/json",
            "x-meeting-baas-api-key": self.api_key
        }
    
    async def join_meeting(
        self, 
        meeting_url: str,
        bot_name: str = "Jarvis",
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Join a meeting with a bot"""
        try:
            if not self.api_key:
                return {
                    "status": "error",
                    "message": "MeetingBaaS API key not configured"
                }
            
            if not self.webhook_host:
                return {
                    "status": "error",
                    "message": "DEVTUNNEL_HOST not configured. Please set up devtunnel."
                }

            # Clean and validate meeting URL
            meeting_url = meeting_url.strip()
            if "http" not in meeting_url.lower():
                meeting_url = f"https://{meeting_url}"
            
            # Remove any duplicate protocol prefixes
            if meeting_url.count("http") > 1:
                meeting_url = meeting_url[meeting_url.rfind("http"):]
            
            # Basic validation
            if "zoom.us/j/" not in meeting_url:
                return {
                    "status": "error",
                    "message": "Invalid Zoom meeting URL format"
                }
            
            # Configure webhook and WebSocket URLs
            webhook_url = f"https://{self.webhook_host}/api/meeting/webhook"
            websocket_url = f"wss://{self.webhook_host}/ws/meeting"
            
            # Prepare bot configuration
            data = {
                "meeting_url": meeting_url,
                "bot_name": bot_name,
                "bot_image": None,
                "entry_message": "Jarvis has joined to provide real-time insights",
                "recording_mode": "speaker_view",
                "reserved": False,
                "speech_to_text": {
                    "provider": "Default"
                },
                "automatic_leave": {
                    "waiting_room_timeout": 600
                },
                "streaming": {
                    "audio_frequency": "16khz",
                    "output": websocket_url
                },
                "webhook_url": webhook_url
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/bots",
                headers=self._get_headers(),
                json=data
            )
            
            if response.status_code == 200:
                meeting_data = response.json()
                bot_id = meeting_data["bot_id"]
                
                # Store bot info
                self.active_bots[bot_id] = {
                    "meeting_url": meeting_url,
                    "bot_name": bot_name,
                    "status": "joining_call",
                    "created_at": datetime.utcnow()
                }
                
                # Save to database if session provided
                if db:
                    meeting = Meeting(
                        bot_id=bot_id,
                        meeting_url=meeting_url,
                        bot_name=bot_name,
                        status="joining_call",
                        started_at=datetime.utcnow()
                    )
                    db.add(meeting)
                    await db.commit()
                
                logger.info(f"Bot {bot_id} joining meeting: {meeting_url}")
                
                # Send websocket status update
                from app.core.websocket_manager import manager
                await manager.send_status_update("joining_call", {
                    "bot_id": bot_id,
                    "meeting_url": meeting_url,
                    "message": "Bot is joining the meeting"
                })
                
                return {
                    "status": "success",
                    "bot_id": bot_id,
                    "message": f"Bot is joining the meeting. Bot ID: {bot_id}"
                }
            else:
                error_msg = f"Failed to join meeting: {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg
                }
                
        except Exception as e:
            error_msg = f"Error joining meeting: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def leave_meeting(self, bot_id: str) -> Dict[str, Any]:
        """Leave a meeting"""
        try:
            response = requests.delete(
                f"{self.base_url}/bots/{bot_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                if bot_id in self.active_bots:
                    del self.active_bots[bot_id]
                
                logger.info(f"Bot {bot_id} left meeting")
                return {
                    "status": "success",
                    "message": "Bot has left the meeting"
                }
            else:
                error_msg = f"Failed to leave meeting: {response.text}"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg
                }
                
        except Exception as e:
            error_msg = f"Error leaving meeting: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        """Get the status of a bot"""
        try:
            response = requests.get(
                f"{self.base_url}/bots/{bot_id}",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                bot_data = response.json()
                return {
                    "status": "success",
                    "bot_data": bot_data
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to get bot status: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error getting bot status: {str(e)}"
            }
    
    async def fetch_meeting_data(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """Fetch meeting data including transcripts"""
        try:
            url = f"{self.base_url}/bots/meeting_data"
            params = {"bot_id": bot_id}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=self._get_headers(), 
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch meeting data: {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching meeting data: {str(e)}")
            return None
    
    async def process_webhook(self, webhook_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Process webhook events from MeetingBaaS"""
        try:
            # Validate API key if present
            api_key = webhook_data.get("api_key")
            if api_key and api_key != self.api_key:
                return {
                    "status": "error",
                    "message": "Invalid API key"
                }

            event = webhook_data.get("event")
            event_data = webhook_data.get("data", {})
            bot_id = event_data.get("bot_id")
            
            if not event or not bot_id:
                return {
                    "status": "error",
                    "message": "Invalid webhook data"
                }
            
            logger.info(f"Processing webhook event: {event} for bot {bot_id}")
            
            # Get meeting from database
            meeting = await db.get(Meeting, bot_id)
            
            # Handle different event types
            if event == "bot.status_change":
                status_code = event_data.get("status", {}).get("code")
                status_details = {
                    "code": status_code,
                    "created_at": event_data.get("status", {}).get("created_at"),
                    "start_time": event_data.get("status", {}).get("start_time"),
                    "error_message": event_data.get("status", {}).get("error_message"),
                    "error_type": event_data.get("status", {}).get("error_type")
                }
                
                # Update active bots
                if bot_id in self.active_bots:
                    self.active_bots[bot_id].update({
                        "status": status_code,
                        "status_details": status_details
                    })
                
                # Update database
                if meeting:
                    meeting.status = status_code
                    meeting.status_details = json.dumps(status_details)
                    await db.commit()
                
                # Send websocket status update
                from app.core.websocket_manager import manager
                await manager.send_status_update(status_code, {
                    "bot_id": bot_id,
                    "meeting_url": meeting.meeting_url if meeting else None,
                    "status_details": status_details,
                    "message": f"Status changed to {status_code}"
                })
                
                return {
                    "status": "success",
                    "event": "status_change",
                    "new_status": status_code
                }
            
            elif event == "complete":
                # Store complete meeting data
                mp4_url = event_data.get("mp4")
                speakers = event_data.get("speakers", [])
                transcript = event_data.get("transcript", [])
                
                if meeting:
                    meeting.status = "completed"
                    meeting.ended_at = datetime.utcnow()
                    meeting.recording_url = mp4_url
                    meeting.speakers = json.dumps(speakers)
                    meeting.transcript = json.dumps(transcript)
                    await db.commit()
                
                # Update active bots with final data
                if bot_id in self.active_bots:
                    self.active_bots[bot_id].update({
                        "status": "completed",
                        "mp4_url": mp4_url,
                        "speakers": speakers,
                        "transcript": transcript
                    })
                
                # Send websocket completion
                from app.core.websocket_manager import manager
                await manager.send_status_update("complete", {
                    "bot_id": bot_id,
                    "meeting_url": meeting.meeting_url if meeting else None,
                    "mp4_url": mp4_url,
                    "speakers": speakers,
                    "message": "Meeting completed successfully"
                })
                
                return {
                    "status": "success",
                    "event": "complete",
                    "mp4_url": mp4_url,
                    "speakers": speakers
                }
            
            elif event == "failed":
                error_code = event_data.get("error", "UnknownError")
                error_details = {
                    "code": error_code,
                    "message": event_data.get("error_message", ""),
                    "type": event_data.get("error_type", "")
                }
                
                if meeting:
                    meeting.status = f"failed_{error_code}"
                    meeting.ended_at = datetime.utcnow()
                    meeting.error_details = json.dumps(error_details)
                    await db.commit()
                
                # Update active bots
                if bot_id in self.active_bots:
                    self.active_bots[bot_id].update({
                        "status": f"failed_{error_code}",
                        "error_details": error_details
                    })
                
                # Send websocket failure
                from app.core.websocket_manager import manager
                await manager.send_status_update("failed", {
                    "bot_id": bot_id,
                    "meeting_url": meeting.meeting_url if meeting else None,
                    "error_code": error_code,
                    "error_details": error_details,
                    "message": f"Meeting failed: {error_code}"
                })
                
                return {
                    "status": "error",
                    "event": "failed",
                    "error_code": error_code,
                    "error_details": error_details
                }
            
            return {
                "status": "success",
                "message": "Webhook processed"
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return {
                "status": "error",
                "message": f"Error processing webhook: {str(e)}"
            }


# Global instance
meeting_service = MeetingBaaSService()
