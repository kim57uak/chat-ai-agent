"""
Loguru-based logging setup
Simple, powerful, and production-ready logging
"""

import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Setup flag to prevent duplicate initialization
_loguru_initialized = False

# Detect if running in PyInstaller bundle
def _is_frozen():
    """Check if running in PyInstaller bundle"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def setup_loguru():
    """Setup loguru with optimized configuration"""
    global _loguru_initialized
    
    # Prevent duplicate initialization
    if _loguru_initialized:
        return logger
    
    _loguru_initialized = True
    
    # Get log directory
    log_dir = _get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Disable async logging in frozen (PyInstaller) environment
    # to prevent multiprocessing conflicts
    use_async = not _is_frozen()
    
    # Console handler with colors (development)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Main app log file
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=use_async,  # Async only in dev mode
        backtrace=True,
        diagnose=True
    )
    
    # AI interactions log (separate file)
    logger.add(
        log_dir / "ai_interactions.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=use_async,
        filter=lambda record: "ai" in record["extra"].get("category", "")
    )
    
    # Security log (separate file)
    logger.add(
        log_dir / "security.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="90 days",  # Keep security logs longer
        compression="zip",
        enqueue=use_async,
        filter=lambda record: "security" in record["extra"].get("category", "")
    )
    
    # Token usage log (separate file)
    logger.add(
        log_dir / "token_usage.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=use_async,
        filter=lambda record: "token" in record["extra"].get("category", "")
    )
    
    return logger

def _get_log_dir() -> Path:
    """Get log directory with fallback"""
    try:
        from utils.config_path import config_path_manager
        user_path = config_path_manager.get_user_config_path()
        if user_path:
            return user_path / "logs"
    except:
        pass
    
    try:
        return Path.home() / ".chat-ai-agent" / "logs"
    except:
        import tempfile
        return Path(tempfile.gettempdir()) / "chat-ai-agent" / "logs"

# Global logger instance
app_logger = setup_loguru()
