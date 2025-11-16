"""
JSON Formatter - Story 4.2

Custom logging formatter that outputs structured JSON logs for easy parsing
and analysis.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON for structured logging.
    
    Produces JSON log entries with consistent structure:
    - timestamp: ISO 8601 UTC timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - module: Module name where log originated
    - message: Log message
    - event: Optional event type for categorization
    - data: Optional structured data dictionary
    - metrics: Optional performance metrics dictionary
    - error: Exception details if present
    
    Example output:
    {
      "timestamp": "2025-10-24T14:32:15.123Z",
      "level": "INFO",
      "module": "recognition_pipeline",
      "message": "Person recognized",
      "event": "person_recognized",
      "data": {
        "person_name": "Michelle",
        "confidence": 0.85
      },
      "metrics": {
        "recognition_time_ms": 45.2
      }
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record: LogRecord to format
            
        Returns:
            JSON string representation of log record
        """
        # Base log data
        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'module': record.module,
            'message': record.getMessage(),
        }
        
        # Add function and line number for DEBUG level
        if record.levelno == logging.DEBUG:
            log_data['function'] = record.funcName
            log_data['line'] = record.lineno
        
        # Add optional event type
        if hasattr(record, 'event'):
            log_data['event'] = record.event
        
        # Add optional structured data
        if hasattr(record, 'data'):
            log_data['data'] = record.data
        
        # Add optional metrics
        if hasattr(record, 'metrics'):
            log_data['metrics'] = record.metrics
        
        # Add exception info if present
        if record.exc_info:
            log_data['error'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error',
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add stack info if present (for debugging)
        if record.stack_info:
            log_data['stack'] = record.stack_info
        
        return json.dumps(log_data, default=str)
    
    def formatException(self, exc_info) -> str:
        """
        Format exception information as string.
        
        Args:
            exc_info: Exception info tuple
            
        Returns:
            Formatted exception traceback
        """
        return ''.join(traceback.format_exception(*exc_info))


class CompactJSONFormatter(JSONFormatter):
    """
    Compact JSON formatter that omits null/empty fields.
    
    Produces smaller log files by excluding fields with no data.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format record and remove empty fields."""
        json_str = super().format(record)
        log_data = json.loads(json_str)
        
        # Remove null or empty values
        compact_data = {
            k: v for k, v in log_data.items() 
            if v is not None and v != {} and v != []
        }
        
        return json.dumps(compact_data, default=str)
