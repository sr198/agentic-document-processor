# app/utils/logger.py

import sys
from loguru import logger
from ..core.config import get_settings

settings = get_settings()

# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    level=settings.LOG_LEVEL
)

# Add file logging
logger.add(
    "logs/impact_analysis.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.LOG_LEVEL
)