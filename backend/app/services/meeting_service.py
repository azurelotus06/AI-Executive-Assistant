"""MeetingBaaS service for joining and managing Zoom meetings"""
import os
import json
import asyncio
import aiohttp
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session

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
        bot_name: str = "AI Executive Assistant",
        db: Session = None
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
            
            # Configure webhook and WebSocket URLs
            webhook_url = f"https://{self.webhook_host}/api/meeting/webhook"
            websocket_url = f"wss://{self.webhook_host}/ws/meeting"
            
            # Prepare bot configuration
            data = {
                "meeting_url": meeting_url,
                "bot_name": bot_name,
                "bot_image": None,
                "entry_message": "AI Executive Assistant has joined to provide real-time insights",
                "recording_mode": "audio_only",
                "reserved": False,
                "speech_to_text": {
                    "provider": "Default"
                },
                "automatic_leave": {
                    "waiting_room_timeout": 900
                },
                "streaming": {
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
                    db.commit()
                
                logger.info(f"Bot {bot_id} joining meeting: {meeting_url}")
                
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
    
    async def process_webhook(self, webhook_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Process webhook events from MeetingBaaS"""
        try:
            event = webhook_data.get("event")
            event_data = webhook_data.get("data", {})
            bot_id = event_data.get("bot_id")
            
            if not event or not bot_id:
                return {
                    "status": "error",
                    "message": "Invalid webhook data"
                }
            
            logger.info(f"Processing webhook event: {event} for bot {bot_id}")
            
            # Update bot status
            if bot_id in self.active_bots:
                self.active_bots[bot_id]["status"] = event
            
            # Get meeting from database
            meeting = db.query(Meeting).filter_by(bot_id=bot_id).first()
            
            if event == "bot.status_change":
                status_code = event_data.get("status", {}).get("code")
                if meeting:
                    meeting.status = status_code
                    db.commit()
                
                return {
                    "status": "success",
                    "event": "status_change",
                    "new_status": status_code
                }
            
            elif event == "complete":
                # Meeting has ended, fetch final data
                meeting_data = await self.fetch_meeting_data(bot_id)
                
                if meeting and meeting_data:
                    bot_data = meeting_data.get("bot_data", {})
                    meeting.status = "completed"
                    meeting.ended_at = datetime.utcnow()
                    meeting.transcript = json.dumps(bot_data.get("transcripts", []))
                    meeting.duration = bot_data.get("duration", 0)
                    db.commit()
                
                # Remove from active bots
                if bot_id in self.active_bots:
                    del self.active_bots[bot_id]
                
                return {
                    "status": "success",
                    "event": "complete",
                    "message": "Meeting completed successfully"
                }
            
            elif event == "failed":
                error_code = event_data.get("error", "UnknownError")
                
                if meeting:
                    meeting.status = f"failed_{error_code}"
                    meeting.ended_at = datetime.utcnow()
                    db.commit()
                
                # Remove from active bots
                if bot_id in self.active_bots:
                    del self.active_bots[bot_id]
                
                return {
                    "status": "error",
                    "event": "failed",
                    "error_code": error_code
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
