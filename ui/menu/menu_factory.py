"""Menu factory for creating application menus."""

from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction
from typing import Protocol


class MenuActionHandler(Protocol):
    """Protocol for menu action handlers."""
    
    def open_settings(self) -> None: ...
    def open_mcp(self) -> None: ...
    def open_mcp_manager(self) -> None: ...
    def clear_conversation_history(self) -> None: ...
    def open_user_prompt(self) -> None: ...


class MenuFactory:
    """Factory for creating application menus."""
    
    def __init__(self, handler: MenuActionHandler):
        self._handler = handler
    
    def create_menu_bar(self, parent) -> QMenuBar:
        """Create the main menu bar."""
        menubar = parent.menuBar()
        self._create_settings_menu(menubar)
        return menubar
    
    def _create_settings_menu(self, menubar: QMenuBar) -> None:
        """Create settings menu with all actions."""
        settings_menu = menubar.addMenu('설정')
        
        # Environment settings
        settings_action = QAction('환경설정', menubar)
        settings_action.triggered.connect(self._handler.open_settings)
        settings_menu.addAction(settings_action)
        
        # MCP actions
        mcp_action = QAction('MCP 확장 임포트', menubar)
        mcp_action.triggered.connect(self._handler.open_mcp)
        settings_menu.addAction(mcp_action)
        
        mcp_manager_action = QAction('MCP 서버 관리', menubar)
        mcp_manager_action.triggered.connect(self._handler.open_mcp_manager)
        settings_menu.addAction(mcp_manager_action)
        
        settings_menu.addSeparator()
        
        # History and prompt actions
        clear_history_action = QAction('대화 기록 초기화', menubar)
        clear_history_action.triggered.connect(self._handler.clear_conversation_history)
        settings_menu.addAction(clear_history_action)
        
        user_prompt_action = QAction('유저 프롬프트 설정', menubar)
        user_prompt_action.triggered.connect(self._handler.open_user_prompt)
        settings_menu.addAction(user_prompt_action)