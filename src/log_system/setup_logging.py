"""
Logging Setup - Story 4.2

Configures logging system based on config.yaml settings with support for:
- Console and file handlers
- Rotating file logs
- JSON or text format
- Multiple log levels
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .json_formatter import JSONFormatter, CompactJSONFormatter

# Module-level logger cache
_loggers = {}
_logging_configured = False


def setup_logging(
    logger_name: str = 'reachy_recognizer',
    config: Optional[object] = None
) -> logging.Logger:
    """
    Configure logging system based on configuration.
    
    Sets up both console and file handlers with appropriate formatters.
    Console uses human-readable format, file can use JSON for analysis.
    
    Args:
        logger_name: Name for the logger (default: 'reachy_recognizer')
        config: Config object (loads from get_config() if None)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = setup_logging()
        >>> logger.info("System started")
        >>> logger.error("Error occurred", extra={'event': 'error', 'data': {...}})
    """
    global _logging_configured
    
    # Only configure once
    if _logging_configured and logger_name in _loggers:
        return _loggers[logger_name]
    
    # Load config if not provided
    if config is None:
        try:
            from ..config import get_config
            config = get_config()
        except Exception as e:
            print(f"Warning: Could not load config, using defaults: {e}")
            config = None
    
    # Create logger
    logger = logging.getLogger(logger_name)
    
    # Set log level
    if config and hasattr(config, 'logging'):
        log_level = getattr(logging, config.logging.level, logging.INFO)
    else:
        log_level = logging.INFO
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler (human-readable format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    if config and hasattr(config, 'logging'):
        console_format = config.logging.format
    else:
        console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    console_handler.setFormatter(logging.Formatter(console_format))
    logger.addHandler(console_handler)
    
    # File handler (JSON format for analysis)
    if config and hasattr(config, 'logging') and config.logging.file_path:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(config.logging.file_path)
            log_dir = log_path.parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                str(log_path),
                maxBytes=config.logging.max_bytes,
                backupCount=config.logging.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            
            # Use JSON formatter for file logs
            if config.logging.json_format:
                file_handler.setFormatter(CompactJSONFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(console_format))
            
            logger.addHandler(file_handler)
            
            logger.info(f"Logging to file: {log_path}")
            
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    _loggers[logger_name] = logger
    _logging_configured = True
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance.
    
    If logging hasn't been configured yet, sets it up with defaults.
    
    Args:
        name: Logger name (uses module name if None)
        
    Returns:
        Logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module started")
    """
    if name is None:
        name = 'reachy_recognizer'
    
    # If not configured, configure now
    if not _logging_configured:
        return setup_logging(name)
    
    # Return existing or create child logger
    if name in _loggers:
        return _loggers[name]
    else:
        # Create child logger
        logger = logging.getLogger(name)
        _loggers[name] = logger
        return logger


def log_event(
    logger: logging.Logger,
    level: str,
    message: str,
    event: Optional[str] = None,
    data: Optional[dict] = None,
    metrics: Optional[dict] = None
):
    """
    Log an event with structured data.
    
    Convenience function for logging events with consistent structure.
    
    Args:
        logger: Logger instance
        level: Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        message: Log message
        event: Event type for categorization
        data: Structured event data
        metrics: Performance metrics
        
    Example:
        >>> log_event(
        ...     logger, 'INFO', 'Person recognized',
        ...     event='person_recognized',
        ...     data={'name': 'Michelle', 'confidence': 0.85},
        ...     metrics={'recognition_time_ms': 45.2}
        ... )
    """
    extra = {}
    if event:
        extra['event'] = event
    if data:
        extra['data'] = data
    if metrics:
        extra['metrics'] = metrics
    
    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra)
