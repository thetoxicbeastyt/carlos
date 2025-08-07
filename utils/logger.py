"""
Logger utility for Carlos Assistant with rotation and colored console output.
"""

import logging
import logging.handlers
import os
import sys
import codecs
from typing import Optional
import colorlog


class CarlosLogger:
    """Logger class with file rotation and colored console output."""
    
    def __init__(self, name: str, config: dict):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            config: Configuration dictionary containing logging settings
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config['general']['log_level']))
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        self._setup_file_handler()
        self._setup_console_handler()
    
    def _setup_file_handler(self) -> None:
        """Setup file handler with rotation."""
        log_file = self.config['logging']['log_file']
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Parse max_log_size (e.g., "10MB" -> 10485760 bytes)
        max_size_str = self.config['logging']['max_log_size']
        if max_size_str.endswith('MB'):
            max_bytes = int(max_size_str[:-2]) * 1024 * 1024
        elif max_size_str.endswith('KB'):
            max_bytes = int(max_size_str[:-2]) * 1024
        else:
            max_bytes = int(max_size_str)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=self.config['logging']['backup_count'],
            encoding='utf-8'  # CRITICAL: UTF-8 encoding for file
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self) -> None:
        """Setup colored console handler with Windows Unicode support fix."""
        console_handler = colorlog.StreamHandler()
        
        # CRITICAL FIX: Windows console encoding
        if sys.platform == "win32":
            try:
                # Try to set console to UTF-8
                console_handler.stream = codecs.getwriter('utf-8')(
                    sys.stdout.buffer, errors='replace'
                )
            except (AttributeError, OSError):
                # Fallback: replace problematic characters
                console_handler.addFilter(UnicodeFilter())
        
        color_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(color_formatter)
        self.logger.addHandler(console_handler)
    
    def _safe_log_message(self, message: str) -> str:
        """Replace emoji with Windows-safe symbols if encoding fails"""
        if sys.platform != "win32":
            return message
            
        replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]', 
            '⚠️': '[WARNING]',
            '🔊': '[AUDIO]',
            '🚀': '[START]',
            '📦': '[INSTALL]',
            '🧠': '[AI]',
            '🔍': '[CHECK]',
            '🎉': '[SUCCESS]'
        }
        
        safe_message = message
        for emoji, replacement in replacements.items():
            safe_message = safe_message.replace(emoji, replacement)
        
        return safe_message
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        try:
            self.logger.debug(message)
        except UnicodeEncodeError:
            self.logger.debug(self._safe_log_message(message))
    
    def info(self, message: str) -> None:
        """Log info message."""
        try:
            self.logger.info(message)
        except UnicodeEncodeError:
            self.logger.info(self._safe_log_message(message))
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        try:
            self.logger.warning(message)
        except UnicodeEncodeError:
            self.logger.warning(self._safe_log_message(message))
    
    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error message."""
        try:
            self.logger.error(message, exc_info=exc_info)
        except UnicodeEncodeError:
            self.logger.error(self._safe_log_message(message), exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False) -> None:
        """Log critical message."""
        try:
            self.logger.critical(message, exc_info=exc_info)
        except UnicodeEncodeError:
            self.logger.critical(self._safe_log_message(message), exc_info=exc_info)


class UnicodeFilter(logging.Filter):
    """Filter to replace Unicode characters that cause Windows console issues"""
    
    def filter(self, record):
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Replace problematic Unicode characters
            replacements = {
                '✅': '[OK]',
                '❌': '[ERROR]', 
                '⚠️': '[WARNING]',
                '🔊': '[AUDIO]',
                '🚀': '[START]',
                '📦': '[INSTALL]',
                '🧠': '[AI]',
                '🔍': '[CHECK]',
                '🎉': '[SUCCESS]',
                '📝': '[CREATED]',
                '🔄': '[RETRY]'
            }
            
            for emoji, replacement in replacements.items():
                record.msg = record.msg.replace(emoji, replacement)
        
        return True


def get_logger(name: str, config: dict) -> CarlosLogger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        config: Configuration dictionary
        
    Returns:
        CarlosLogger instance
    """
    return CarlosLogger(name, config)