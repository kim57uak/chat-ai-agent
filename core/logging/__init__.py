"""
Loguru-based centralized logging system
Simple, powerful, and production-ready
"""

from loguru import logger
from .loguru_setup import setup_loguru, app_logger
from .unified_logger import unified_logger

# Setup loguru on import
setup_loguru()

def get_logger(name=None):
    """Get logger instance (for backward compatibility)"""
    if name:
        return logger.bind(module=name)
    return logger

__all__ = ['logger', 'app_logger', 'unified_logger', 'setup_loguru', 'get_logger']
