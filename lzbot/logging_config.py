"""
Structured logging configuration for LZBot-5000
Provides consistent logging setup across all modules with proper formatting and levels.
"""

import logging
import sys
from typing import Optional, Dict, Any
from pathlib import Path
import json
from datetime import datetime


class LZBotFormatter(logging.Formatter):
    """Custom formatter for LZBot logging with structured output."""
    
    def __init__(self, include_timestamp: bool = True, json_format: bool = False):
        self.include_timestamp = include_timestamp
        self.json_format = json_format
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with consistent structure."""
        if self.json_format:
            return self._format_json(record)
        else:
            return self._format_text(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format as JSON for structured logging."""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Format as human-readable text."""
        timestamp = ""
        if self.include_timestamp:
            timestamp = f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')} | "
        
        # Color coding for different log levels
        level_colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        reset_color = '\033[0m'
        
        level_color = level_colors.get(record.levelname, '')
        level_name = f"{level_color}{record.levelname:8}{reset_color}"
        
        base_format = f"{timestamp}{level_name} | {record.name:20} | {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            base_format += f"\n{self.formatException(record.exc_info)}"
        
        return base_format


class LZBotLogger:
    """Centralized logger configuration for LZBot-5000."""
    
    _configured = False
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def setup_logging(
        cls,
        level: str = "INFO",
        log_file: Optional[Path] = None,
        json_format: bool = False,
        include_timestamp: bool = True
    ) -> None:
        """
        Setup structured logging for the entire application.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
            json_format: Use JSON format for structured logging
            include_timestamp: Include timestamps in log output
        """
        if cls._configured:
            return
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Clear any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))
        console_formatter = LZBotFormatter(
            include_timestamp=include_timestamp,
            json_format=json_format
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Setup file handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_formatter = LZBotFormatter(
                include_timestamp=True,
                json_format=json_format
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        # Configure third-party loggers
        cls._configure_third_party_loggers(level)
        
        cls._configured = True
        
        # Log configuration success
        logger = cls.get_logger("lzbot.logging")
        logger.info(f"Logging configured: level={level}, file={log_file}, json={json_format}")
    
    @classmethod
    def _configure_third_party_loggers(cls, level: str) -> None:
        """Configure logging levels for third-party libraries."""
        # Reduce noise from third-party libraries
        logging.getLogger("strands").setLevel(logging.INFO)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        
        # Set specific loggers based on application level
        if level.upper() == "DEBUG":
            logging.getLogger("lzbot").setLevel(logging.DEBUG)
        else:
            logging.getLogger("lzbot").setLevel(logging.INFO)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with consistent configuration.
        
        Args:
            name: Logger name (typically module name)
            
        Returns:
            Configured logger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        
        return cls._loggers[name]
    
    @classmethod
    def log_function_entry(cls, logger: logging.Logger, func_name: str, **kwargs) -> None:
        """Log function entry with parameters."""
        params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        logger.debug(f"Entering {func_name}({params})")
    
    @classmethod
    def log_function_exit(cls, logger: logging.Logger, func_name: str, result: Any = None) -> None:
        """Log function exit with result."""
        if result is not None:
            logger.debug(f"Exiting {func_name} with result: {type(result).__name__}")
        else:
            logger.debug(f"Exiting {func_name}")
    
    @classmethod
    def log_performance(cls, logger: logging.Logger, operation: str, duration: float) -> None:
        """Log performance metrics."""
        logger.info(f"Performance: {operation} took {duration:.3f}s")
    
    @classmethod
    def log_error_context(
        cls, 
        logger: logging.Logger, 
        error: Exception, 
        operation: str,
        context: Dict[str, Any] = None
    ) -> None:
        """Log error with context information."""
        context_str = ""
        if context:
            context_str = f" | Context: {context}"
        
        logger.error(f"Error in {operation}: {str(error)}{context_str}", exc_info=True)


# Convenience functions for common operations
def setup_logging(**kwargs) -> None:
    """Setup logging with default configuration."""
    LZBotLogger.setup_logging(**kwargs)


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger for the calling module."""
    if name is None:
        # Auto-detect module name from caller
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return LZBotLogger.get_logger(name)


def log_function(func):
    """Decorator to automatically log function entry and exit."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Log entry
        LZBotLogger.log_function_entry(logger, func_name, **kwargs)
        
        try:
            result = func(*args, **kwargs)
            LZBotLogger.log_function_exit(logger, func_name, result)
            return result
        except Exception as e:
            LZBotLogger.log_error_context(logger, e, func_name)
            raise
    
    return wrapper