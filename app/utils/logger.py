import sys
from pathlib import Path
from loguru import logger
from app.utils.config import settings

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger output format
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# Reset handlers
logger.remove()

# Console logger
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format=log_format,
    colorize=True,
)

# File logger
logger.add(
    LOGS_DIR / "bot.log",
    rotation="10 MB",
    retention="1 week",
    level=settings.LOG_LEVEL,
    format=log_format,
    encoding="utf-8",
    enqueue=True,
)

__all__ = ["logger"]
