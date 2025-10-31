"""Cross-platform path helper utilities."""

import os
import sys
from pathlib import Path
from typing import Optional


def get_app_data_dir() -> Path:
    """
    Get application data directory with cross-platform support.
    
    Returns:
        Path: Application data directory
        
    Priority:
        1. Windows: %APPDATA%/chat-ai-agent
        2. macOS: ~/Library/Application Support/chat-ai-agent
        3. Linux: ~/.chat-ai-agent
        4. Fallback: ~/.chat-ai-agent
        5. Last resort: ./data
    """
    try:
        if sys.platform == "win32":
            # Windows: Use APPDATA
            appdata = os.getenv("APPDATA")
            if appdata:
                app_dir = Path(appdata) / "chat-ai-agent"
                app_dir.mkdir(parents=True, exist_ok=True)
                return app_dir
        
        elif sys.platform == "darwin":
            # macOS: Use Application Support
            app_support = Path.home() / "Library" / "Application Support" / "chat-ai-agent"
            app_support.mkdir(parents=True, exist_ok=True)
            return app_support
        
        # Linux and fallback
        home_dir = Path.home() / ".chat-ai-agent"
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir
        
    except Exception:
        # Last resort: current directory
        fallback = Path("data")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_log_dir() -> Path:
    """Get log directory."""
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_db_dir() -> Path:
    """Get database directory."""
    db_dir = get_app_data_dir() / "db"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir


def get_config_dir() -> Path:
    """Get configuration directory."""
    return get_app_data_dir()
