"""Initialize all backend services at startup"""
import asyncio
import logging
from app.models.database import init_db
from app.services.realtime_audio_handler import audio_handler

logger = logging.getLogger(__name__)

async def initialize_services():
    """Initialize all application services"""
    try:
        logger.info("Initializing database...")
        await init_db()
        
        logger.info("Initializing audio handler...")
        await audio_handler.initialize()
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(initialize_services())
