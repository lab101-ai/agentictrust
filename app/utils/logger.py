"""
Logging utility for the AgenticTrust application.
This module configures Loguru to provide structured logging based on YAML configuration.
"""
import os
import sys
from pathlib import Path

from loguru import logger

from app.utils.config import load_config

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Load logging configuration
try:
    log_config = load_config("logging")
except FileNotFoundError:
    # Fallback configuration if the config file is not found
    log_config = {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        "rotation": "10 MB",
        "retention": "1 week",
        "compression": "zip"
    }

# Remove default logger
logger.remove()

# Configure environment-specific sinks
env = os.getenv("FLASK_ENV", "development")

# Helper function to convert level string to integer if needed
def parse_level(level):
    """Convert level string to integer if needed, or return level if already an integer."""
    level_map = {
        "TRACE": 5,
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    
    if isinstance(level, str):
        return level_map.get(level.upper(), 20)  # Default to INFO (20) if not found
    return level

# Add console logger
console_config = log_config.get("sinks", {}).get("console", {})
logger.add(
    sys.stderr,
    level=parse_level(console_config.get("level", log_config.get("level", "INFO"))),
    format=log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
    colorize=console_config.get("colorize", True),
)

# Add file logger
file_config = log_config.get("sinks", {}).get("file", {})
logger.add(
    file_config.get("path", logs_dir / "app.log"),
    rotation=file_config.get("rotation", log_config.get("rotation", "10 MB")),
    retention=file_config.get("retention", log_config.get("retention", "1 week")),
    level=parse_level(file_config.get("level", log_config.get("level", "INFO"))),
    format=log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
    compression=log_config.get("compression", "zip"),
)

# Add security event logger
security_config = log_config.get("sinks", {}).get("security", {})
logger.add(
    security_config.get("path", logs_dir / "security.log"),
    rotation=security_config.get("rotation", log_config.get("rotation", "10 MB")),
    retention=security_config.get("retention", log_config.get("retention", "1 month")),
    level=parse_level(security_config.get("level", "INFO")),
    format=log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
    filter=lambda record: record["message"].startswith("SECURITY_EVENT:") if "message" in record else False,
    compression=log_config.get("compression", "zip"),
)

# Add error file logger if configured
error_file_config = log_config.get("sinks", {}).get("error_file", {})
if error_file_config:
    logger.add(
        error_file_config.get("path", logs_dir / "error.log"),
        rotation=error_file_config.get("rotation", log_config.get("rotation", "10 MB")),
        retention=error_file_config.get("retention", log_config.get("retention", "1 week")),
        level=parse_level(error_file_config.get("level", "ERROR")),
        format=log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
        compression=log_config.get("compression", "zip"),
    )

# Configure module-specific loggers from configuration
if "loggers" in log_config:
    for logger_name, logger_config in log_config["loggers"].items():
        # Skip if no configuration
        if not logger_config:
            continue
        
        # Set logger level
        if "level" in logger_config:
            logger.level(logger_name, parse_level(logger_config["level"]))
        
        # Configure custom sinks
        if "sinks" in logger_config:
            for sink_name, sink_config in logger_config["sinks"].items():
                if sink_name == "file" and "path" in sink_config:
                    logger.add(
                        sink_config["path"],
                        rotation=sink_config.get("rotation", log_config.get("rotation", "10 MB")),
                        retention=sink_config.get("retention", log_config.get("retention", "1 week")),
                        level=parse_level(sink_config.get("level", logger_config.get("level", log_config.get("level", "INFO")))),
                        format=log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
                        filter=lambda record, module=logger_name: record["name"].startswith(module),
                        compression=log_config.get("compression", "zip"),
                    )

# Export logger instance
__all__ = ["logger"] 