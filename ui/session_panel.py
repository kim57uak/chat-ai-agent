"""
Session Panel - Compatibility Layer
기존 import 경로 호환성 유지

from ui.session_panel import SessionPanel
위 코드가 계속 작동하도록 보장
"""

from ui.session_panel.panel import SessionPanel
from ui.session_panel.session_dialog import NewSessionDialog
from ui.session_panel.session_list_item import SessionListItem

__all__ = ['SessionPanel', 'NewSessionDialog', 'SessionListItem']
