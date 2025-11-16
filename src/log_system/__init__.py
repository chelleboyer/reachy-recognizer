"""
Logging Module - Story 4.2

Provides structured JSON logging, performance tracking, and log analysis
capabilities for the Reachy Recognizer system.
"""

from .json_formatter import JSONFormatter
from .setup_logging import setup_logging, get_logger

__all__ = ['JSONFormatter', 'setup_logging', 'get_logger']
