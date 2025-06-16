import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """Handles AI-powered conversation analysis and response generation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.conversation_history: List[Dict[str, Any]] = []
        self.context_window = settings.ai_context_window
        self.is_paused = False
        self.last_response_time = None
        self.response_cooldown = 30  # Minimum seconds between responses
        
        # Executive assistant persona and prompts
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI assistant"""
        return """You are an AI Executive Assistant participating in a Zoom meeting. Your role is to:

1. **Listen Actively**: Analyze conversations in real-time and understand context, key points, and meeting dynamics.

2. **Provide Strategic Insights**: Offer valuable, executive-level insights that add genuine value to the discussion. Focus on:
   - Strategic implications of decisions being discussed
   - Risk assessment and mitigation strategies
   - Market opportunities and competitive advantages
   - Process improvements and efficiency gains
   - Key action items and follow-ups

3. **Speak Naturally**: Only contribute when you have something genuinely valuable to add. Avoid:
   - Interrupting active discussions
   - Repeating what others have said
   - Generic or obvious comments
   - Speaking too frequently

4. **Executive Communication Style**: 
   - Be concise and impactful (1-2 sentences max)
   - Use professional, confident language
   - Focus on outcomes and actionable insights
   - Speak with authority but remain collaborative

5. **Timing Guidelines**:
   - Wait for natural pauses in conversation
   - Don't speak if someone just finished making a similar point
   - Prioritize quality over quantity of contributions

6. **Response Format**: 
   Return JSON with:
   - "should_speak": boolean (true only if you have valuable input)
   - "response": string (your actual response, if should_speak is true)
   - "confidence": float (0.0-1.0, how confident you are in the value of your response)
   - "reasoning": string (brief explanation of why you chose to speak or not)

Remember: Your goal is to be a valuable team member, not a chatty AI. Quality and timing matter more than frequency."""

    def set_paused(self, paused: bool):
        """Set pause status"""
        self.is_paused = paused
        logger.info(f"AI service {'paused' if paused else 'resumed'}")
    
    def is_healthy(self) -> bool:
        """Check if the AI service is healthy"""
        try:
            return bool(self.client.api_key)
        except Exception:
            return False
    
    def _should_respond_based_on_timing(self) -> bool:
        """Check if enough time has passed since last response"""
        if self.last_response_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_response_time
        return time_since_last.total_seconds() >= self.response_cooldown
    
    def _add_to_conversation_history(self, speaker: str, text: str, timestamp: datetime = None):
        """Add a message to conversation history"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.conversation_history.append({
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp.isoformat()
        })
        
        # Keep only recent messages within context window
        if len(self.conversation_history) > self.context_window:
            self.conversation_history = self.conversation_history[-self.context_window:]
    
    def _build_conversation_context(self) -> str:
        """Build conversation context from history"""
        if not self.conversation_history:
            return "No previous conversation context."
        
        context_lines = []
        for msg in self.conversation_history[-10:]:  # Last 10 messages for context
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M")
            context_lines.append(f"[{timestamp}] {msg['speaker']}: {msg['text']}")
        
        return "\n".join(context_lines)
    
    def _extract_key_topics(self, transcript: str) -> List[str]:
        """Extract key topics from the transcript"""
        # Simple keyword extraction - could be enhanced with NLP
        business_keywords = [
            "strategy", "revenue", "growth", "market", "competition", "customer",
            "product", "launch", "budget", "roi", "kpi", "metrics", "target",
            "goal", "objective", "risk", "opportunity", "decision", "action",
            "timeline", "deadline", "priority", "resource", "team", "project"
        ]
        
        transcript_lower = transcript.lower()
        found_topics = [kw for kw in business_keywords if kw in transcript_lower]
        return found_topics
    
    async def analyze_conversation(
        self, 
        current_message: str = None,
        context: List[str] = None,
        mode: str = "executive_assistant",
        transcript: str = None,
        speaker: str = "Participant"
    ) -> Optional[Dict[str, Any]]:
        """Analyze conversation and determine if AI should respond
        
        Args:
            current_message: The current message to analyze
            context: List of previous messages for context
            mode: The mode of operation (executive_assistant, etc.)
            transcript: Legacy parameter for backward compatibility
            speaker: The speaker of the current message
        """
        try:
            if self.is_paused:
                return None
            
            # Handle both new and legacy parameter formats
            message_text = current_message or transcript
            if not message_text:
                return None
            
            # Add to conversation history
            self._add_to_conversation_history(speaker, message_text)
            
            # Check timing constraints
            if not self._should_respond_based_on_timing():
                logger.info("Skipping response due to timing constraints")
                return {
                    "should_speak": False,
                    "should_respond": False,
                    "reasoning": "Too soon since last response",
                    "confidence": 0.0
                }
            
            # Build context from provided context or history
            if context:
                conversation_context = "\n".join(context)
            else:
                conversation_context = self._build_conversation_context()
            
            key_topics = self._extract_key_topics(message_text)
            
            # Prepare the analysis prompt
            analysis_prompt = f"""
CURRENT MESSAGE: "{message_text}"

RECENT CONVERSATION CONTEXT:
{conversation_context}

KEY TOPICS DETECTED: {', '.join(key_topics) if key_topics else 'None'}

ANALYSIS TASK:
Based on the current message and conversation context, determine if you should contribute to this meeting as an AI Executive Assistant. Consider:

1. Is there a strategic insight you can provide?
2. Are there risks or opportunities worth highlighting?
3. Can you suggest actionable next steps?
4. Is this a natural pause where input would be welcome?
5. Would your contribution add genuine value or just be noise?

Respond with JSON only, no additional text.
"""

            # Call GPT-4 for analysis
            response = await self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            ai_response = json.loads(response.choices[0].message.content)
            
            # Validate response structure
            required_keys = ["should_speak", "confidence"]
            if not all(key in ai_response for key in required_keys):
                logger.error("Invalid AI response structure")
                return None
            
            # Add should_respond for compatibility
            ai_response["should_respond"] = ai_response.get("should_speak", False)
            
            # If AI decides to speak, update timing
            if ai_response.get("should_speak", False):
                self.last_response_time = datetime.now()
                self._add_to_conversation_history("AI Assistant", ai_response.get("response", ""))
                logger.info(f"AI decided to speak: {ai_response.get('response', '')}")
            else:
                logger.info(f"AI decided not to speak: {ai_response.get('reasoning', 'No reason provided')}")
            
            return ai_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return None
    
    async def generate_manual_response(self, user_prompt: str) -> Optional[str]:
        """Generate a response to a manual user prompt"""
        try:
            conversation_context = self._build_conversation_context()
            
            prompt = f"""
CONVERSATION CONTEXT:
{conversation_context}

USER REQUEST: "{user_prompt}"

As an AI Executive Assistant, provide a helpful response to the user's request. Keep it professional, concise, and actionable. Focus on executive-level insights and strategic thinking.
"""
            
            response = await self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.ai_temperature,
                max_tokens=200
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Add to conversation history
            self._add_to_conversation_history("User", user_prompt)
            self._add_to_conversation_history("AI Assistant", ai_response)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating manual response: {e}")
            return None
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return {"summary": "No conversation history", "key_points": [], "action_items": []}
        
        total_messages = len(self.conversation_history)
        ai_responses = len([msg for msg in self.conversation_history if msg["speaker"] == "AI Assistant"])
        
        # Extract recent key points (simplified)
        recent_messages = self.conversation_history[-5:]
        key_points = [msg["text"][:100] + "..." if len(msg["text"]) > 100 else msg["text"] 
                     for msg in recent_messages]
        
        return {
            "total_messages": total_messages,
            "ai_responses": ai_responses,
            "recent_key_points": key_points,
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.last_response_time = None
        logger.info("Conversation history cleared")
    
    def export_conversation(self) -> List[Dict[str, Any]]:
        """Export conversation history"""
        return self.conversation_history.copy()


# Create global instance
ai_service = AIService()
