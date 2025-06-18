"""Script to initialize the real-time audio handler at startup"""
import asyncio
import logging
from app.services.realtime_audio_handler import audio_handler

logger = logging.getLogger(__name__)

async def initialize():
    """Initialize the audio handler"""
    try:
        logger.info("Initializing real-time audio handler...")
        await audio_handler.initialize()
        logger.info("Real-time audio handler initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing audio handler: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(initialize())
