"""
Logging utility for the AgenticTrust application.
This module configures Loguru to provide structured logging.
"""
import os
import sys
from pathlib import Path

from loguru import logger

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Remove default logger
logger.remove()

# Add console logger
logger.add(
    sys.stderr,
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True,
)

# Add file logger for all logs
logger.add(
    logs_dir / "app.log",
    rotation="10 MB",
    retention="30 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# Add file logger for errors only
logger.add(
    logs_dir / "error.log",
    rotation="10 MB",
    retention="30 days",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# Add specialized logger for OAuth operations with sensitive data redacted
logger.add(
    logs_dir / "oauth.log",
    rotation="10 MB", 
    retention="30 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[request_id]} | {name}:{function}:{line} - {message}",
    filter=lambda record: "oauth" in record["name"]
)

# Add specialized logger for agent actions
logger.add(
    logs_dir / "agent_actions.log",
    rotation="10 MB",
    retention="30 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[agent_id]}-{extra[task_id]} | {name}:{function}:{line} - {message}",
    filter=lambda record: "agent" in record["name"] or record["extra"].get("agent_id") is not None
)

# Export logger instance
__all__ = ["logger"] 