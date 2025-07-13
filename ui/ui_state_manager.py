from abc import ABC, abstractmethod
from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal


class UIState(ABC):
    """UI 상태를 나타내는 추상 클래스 (State 패턴)"""
    
    @abstractmethod
    def handle_send_request(self, context) -> None:
        pass
    
    @abstractmethod
    def handle_cancel_request(self, context) -> None:
        pass
    
    @abstractmethod
    def is_processing(self) -> bool:
        pass


class IdleState(UIState):
    """대기 상태"""
    
    def handle_send_request(self, context) -> None:
        context.set_state(ProcessingState())
        context.set_ui_enabled(False)
        context.show_loading(True)
    
    def handle_cancel_request(self, context) -> None:
        # 대기 상태에서는 취소할 것이 없음
        pass
    
    def is_processing(self) -> bool:
        return False


class ProcessingState(UIState):
    """처리 중 상태"""
    
    def handle_send_request(self, context) -> None:
        # 처리 중에는 새로운 요청 무시
        pass
    
    def handle_cancel_request(self, context) -> None:
        context.set_state(IdleState())
        context.set_ui_enabled(True)
        context.show_loading(False)
        context.cancel_ai_request()
    
    def is_processing(self) -> bool:
        return True


class UIStateManager(QObject):
    """UI 상태 관리자 (State 패턴 + Observer 패턴)"""
    
    state_changed = pyqtSignal(str)  # 상태 변경 시그널
    
    def __init__(self):
        super().__init__()
        self._state = IdleState()
        self._ui_context = None
    
    def set_ui_context(self, ui_context):
        """UI 컨텍스트 설정"""
        self._ui_context = ui_context
    
    def set_state(self, state: UIState):
        """상태 변경"""
        self._state = state
        state_name = state.__class__.__name__
        self.state_changed.emit(state_name)
    
    def handle_send_request(self):
        """전송 요청 처리"""
        self._state.handle_send_request(self)
    
    def handle_cancel_request(self):
        """취소 요청 처리"""
        self._state.handle_cancel_request(self)
    
    def is_processing(self) -> bool:
        """처리 중 여부 확인"""
        return self._state.is_processing()
    
    def set_ui_enabled(self, enabled: bool):
        """UI 활성화/비활성화"""
        if self._ui_context:
            self._ui_context.set_ui_enabled(enabled)
    
    def show_loading(self, show: bool):
        """로딩 표시/숨김"""
        if self._ui_context:
            self._ui_context.show_loading(show)
    
    def cancel_ai_request(self):
        """AI 요청 취소"""
        if self._ui_context:
            self._ui_context.cancel_ai_request()


class ToolEmojiMapper:
    """도구 이모티콘 매핑 클래스 (Single Responsibility Principle)"""
    
    EMOJI_MAP = {
        'search': '🔍',
        'web': '🌐', 
        'url': '🌐',
        'fetch': '📄',
        'database': '🗄️',
        'mysql': '🗄️',
        'sql': '🗄️',
        'travel': '✈️',
        'tour': '✈️',
        'hotel': '🏨',
        'flight': '✈️',
        'map': '🗺️',
        'location': '📍',
        'geocode': '📍',
        'weather': '🌤️',
        'email': '📧',
        'file': '📁',
        'excel': '📊',
        'chart': '📈',
        'image': '🖼️',
        'translate': '🌐',
        'api': '🔧'
    }
    
    @classmethod
    def get_tool_emoji(cls, used_tools: List[str]) -> str:
        """사용된 도구에 따라 이모티콘 반환"""
        if not used_tools:
            return ""
        
        # 첫 번째 도구의 이름에서 키워드 찾기
        tool_name = str(used_tools[0]).lower() if used_tools else ""
        
        for keyword, emoji in cls.EMOJI_MAP.items():
            if keyword in tool_name:
                return emoji
        
        # 매핑되지 않은 도구의 기본 이모티콘
        return "⚡"