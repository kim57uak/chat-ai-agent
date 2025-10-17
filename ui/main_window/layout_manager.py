"""
Layout Manager
레이아웃 관리 전담 클래스
"""

import json
from core.logging import get_logger

logger = get_logger("layout_manager")


class LayoutManager:
    """레이아웃 관리 전담 클래스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def toggle_session_panel(self):
        """세션 패널 표시 토글"""
        is_visible = self.main_window.session_panel.isVisible()
        self.main_window.session_panel.setVisible(not is_visible)
        self.main_window.session_panel_action.setChecked(not is_visible)
        
        current_sizes = self.main_window.splitter.sizes()
        total_width = sum(current_sizes)
        
        if not is_visible:
            token_width = current_sizes[2] if self.main_window.token_display.isVisible() else 0
            self.main_window.splitter.setSizes([250, total_width - 250 - token_width, token_width])
        else:
            token_width = current_sizes[2] if self.main_window.token_display.isVisible() else 0
            self.main_window.splitter.setSizes([0, total_width - token_width, token_width])
        
        self.save_splitter_state()
    
    def toggle_token_display(self):
        """토큰 사용량 표시 토글"""
        is_visible = self.main_window.token_display.isVisible()
        self.main_window.token_display.setVisible(not is_visible)
        self.main_window.token_usage_action.setChecked(not is_visible)
        
        current_sizes = self.main_window.splitter.sizes()
        total_width = sum(current_sizes)
        
        if not is_visible:
            self.main_window.token_display.refresh_display()
            session_width = current_sizes[0] if self.main_window.session_panel.isVisible() else 0
            token_width = 300
            self.main_window.splitter.setSizes([session_width, total_width - session_width - token_width, token_width])
        else:
            session_width = current_sizes[0] if self.main_window.session_panel.isVisible() else 0
            self.main_window.splitter.setSizes([session_width, total_width - session_width, 0])
        
        self.save_splitter_state()
    
    def reset_layout(self):
        """레이아웃 초기화"""
        self.main_window.splitter.setSizes([250, 950, 0])
        self.main_window.session_panel.setVisible(True)
        self.main_window.session_panel_action.setChecked(True)
        self.main_window.token_display.setVisible(False)
        self.main_window.token_usage_action.setChecked(False)
        self.save_splitter_state()
        logger.debug("레이아웃이 초기화되었습니다.")
    
    def load_splitter_state(self):
        """스플리터 상태 로드"""
        try:
            from utils.config_path import config_path_manager
            config_path = config_path_manager.get_config_path('splitter_state.json')
            if config_path.exists():
                with open(config_path, 'r') as f:
                    state = json.load(f)
                    sizes = state.get('sizes', [250, 950, 0])
                    token_visible = state.get('token_visible', False)
                    session_visible = state.get('session_visible', True)
                    
                    self.main_window.splitter.setSizes(sizes)
                    self.main_window.token_display.setVisible(token_visible)
                    self.main_window.token_usage_action.setChecked(token_visible)
                    self.main_window.session_panel.setVisible(session_visible)
                    self.main_window.session_panel_action.setChecked(session_visible)
        except Exception as e:
            logger.debug(f"스플리터 상태 로드 오류: {e}")
    
    def save_splitter_state(self):
        """스플리터 상태 저장"""
        try:
            from utils.config_path import config_path_manager
            state = {
                'sizes': self.main_window.splitter.sizes(),
                'token_visible': self.main_window.token_display.isVisible(),
                'session_visible': self.main_window.session_panel.isVisible()
            }
            config_path = config_path_manager.get_config_path('splitter_state.json')
            with open(config_path, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            logger.debug(f"스플리터 상태 저장 오류: {e}")
