"""
Application startup tasks
Initialize Authentik integration and ensure required groups exist
"""

import asyncio
import logging
from app.services.authentik_service import ensure_default_groups

logger = logging.getLogger(__name__)


async def startup_tasks():
    """Run startup tasks for the application"""
    logger.info("Running application startup tasks...")
    
    try:
        # Ensure Authentik default groups exist
        await ensure_default_groups()
        logger.info("✓ Authentik groups initialization completed")
        
    except Exception as e:
        logger.error(f"Startup tasks failed: {e}")
        # Don't fail the application startup if Authentik is unavailable
        logger.warning("Some startup tasks failed, but application will continue")


def run_startup_tasks():
    """Synchronous wrapper for startup tasks"""
    try:
        asyncio.run(startup_tasks())
    except Exception as e:
        logger.error(f"Failed to run startup tasks: {e}")
