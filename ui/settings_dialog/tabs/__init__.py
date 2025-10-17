"""
Settings Dialog Tabs
설정 다이얼로그 탭 모듈
"""

from .ai_settings_tab import AISettingsTab
from .security_settings_tab import SecuritySettingsTab
from .length_limit_tab import LengthLimitTab
from .history_settings_tab import HistorySettingsTab
from .language_detection_tab import LanguageDetectionTab
from .news_settings_tab import NewsSettingsTab

__all__ = [
    'AISettingsTab',
    'SecuritySettingsTab',
    'LengthLimitTab',
    'HistorySettingsTab',
    'LanguageDetectionTab',
    'NewsSettingsTab',
]
