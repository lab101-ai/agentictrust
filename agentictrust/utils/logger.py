"""
Logging utility for the AgenticTrust application.
This module configures Loguru to provide structured logging based on YAML configuration.
"""
import os
import sys
from pathlib import Path
import logging

from loguru import logger

from agentictrust.config import Config

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Load logging configuration
try:
    log_config = Config.load_yaml("logging")
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
env = os.getenv("APP_ENV", "development")

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
        return level_map.get(level.upper(), logging.INFO)  # Default to INFO (20) if not found
    return level

# Get environment-specific configuration
if env in log_config.get("environments", {}):
    env_config = log_config["environments"][env]
    
    # Update the configuration with environment-specific settings
    for key, value in env_config.items():
        if key != "sinks":
            log_config[key] = value
    
    # Handle environment-specific sinks
    if "sinks" in env_config:
        if "sinks" not in log_config:
            log_config["sinks"] = {}
        for sink_name, sink_config in env_config["sinks"].items():
            if sink_name not in log_config["sinks"]:
                log_config["sinks"][sink_name] = {}
            log_config["sinks"][sink_name].update(sink_config)

# Define a color map for more vibrant log levels when colorize is enabled
color_map = log_config.get("colors", {
    "DEBUG": "<blue>",
    "INFO": "<green>",
    "WARNING": "<yellow>",
    "ERROR": "<red>",
    "CRITICAL": "<bold><red>"
})

# Create a colorized format string
color_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - {message}"

# --- Intercept standard logging --- START
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

# Remove existing handlers from root logger
logging.root.handlers = [InterceptHandler()]

# Set the root logger level (read from config or default)
root_log_level = parse_level(log_config.get("level", "INFO"))
logging.root.setLevel(root_log_level)

# Configure loguru to handle levels specified for standard loggers
for name in logging.root.manager.loggerDict.keys():
    logging.getLogger(name).handlers = []
    logging.getLogger(name).propagate = True
# --- Intercept standard logging --- END

# Add console logger with proper colorization
console_config = log_config.get("sinks", {}).get("console", {})
colorize_enabled = console_config.get("colorize", True)

logger.add(
    sys.stderr,
    level=parse_level(console_config.get("level", log_config.get("level", "INFO"))),
    format=color_format if colorize_enabled else log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"),
    colorize=colorize_enabled,
)

# Add file logger
file_config = log_config.get("sinks", {}).get("file", {})
file_colorize = file_config.get("colorize", False)  # Default to no color for file logs
file_format = color_format if file_colorize else log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")

logger.add(
    file_config.get("path", logs_dir / "agentictrust.log"),
    rotation=file_config.get("rotation", log_config.get("rotation", "10 MB")),
    retention=file_config.get("retention", log_config.get("retention", "1 week")),
    level=parse_level(file_config.get("level", log_config.get("level", "INFO"))),
    format=file_format,
    compression=log_config.get("compression", "zip"),
    colorize=file_colorize,  # Usually false for files, but configurable
)

# Add security event logger
security_config = log_config.get("sinks", {}).get("security", {})
security_colorize = security_config.get("colorize", False)  # Default to no color for security logs
security_format = color_format if security_colorize else log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")

logger.add(
    security_config.get("path", logs_dir / "security.log"),
    rotation=security_config.get("rotation", log_config.get("rotation", "10 MB")),
    retention=security_config.get("retention", log_config.get("retention", "1 month")),
    level=parse_level(security_config.get("level", "INFO")),
    format=security_format,
    filter=lambda record: record["message"].startswith("SECURITY_EVENT:") if "message" in record else False,
    compression=log_config.get("compression", "zip"),
    colorize=security_colorize,
)

# Add error file logger if configured
error_file_config = log_config.get("sinks", {}).get("error_file", {})
if error_file_config:
    error_colorize = error_file_config.get("colorize", False)  # Default to no color for error logs
    error_format = color_format if error_colorize else log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
    
    logger.add(
        error_file_config.get("path", logs_dir / "error.log"),
        rotation=error_file_config.get("rotation", log_config.get("rotation", "10 MB")),
        retention=error_file_config.get("retention", log_config.get("retention", "1 week")),
        level=parse_level(error_file_config.get("level", "ERROR")),
        format=error_format,
        compression=log_config.get("compression", "zip"),
        colorize=error_colorize,
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
                    sink_colorize = sink_config.get("colorize", log_config.get("colorize", True))
                    sink_format = color_format if sink_colorize else log_config.get("format", "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")
                    
                    logger.add(
                        sink_config["path"],
                        rotation=sink_config.get("rotation", log_config.get("rotation", "10 MB")),
                        retention=sink_config.get("retention", log_config.get("retention", "1 week")),
                        level=parse_level(sink_config.get("level", logger_config.get("level", log_config.get("level", "INFO")))),
                        format=sink_format,
                        filter=lambda record, module=logger_name: record["name"].startswith(module),
                        colorize=sink_colorize,
                        compression=log_config.get("compression", "zip"),
                    )

def format_request_log(method: str, path: str, status: int, duration_ms: float) -> str:
    """Formats the request completion log message."""
    return (
        f"Request completed: {method} {path} "
        f"{status} in {duration_ms:.1f}ms"
    )

# Export logger instance
__all__ = ["logger", "format_request_log"]