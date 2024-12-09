"""Structured logging configuration for the application."""

import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger

def setup_logging(
    service_name: str = "srt-model-quantizing",
    log_level: str = "INFO",
    json_format: bool = True
) -> logging.Logger:
    """Configure structured logging for the application.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON format for logs
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            json_ensure_ascii=False
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (defaults to root logger name)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name) 