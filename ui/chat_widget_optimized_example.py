"""
ChatWidget 최적화 예시
기존 chat_widget.py에 적용할 최적화 패턴
"""

from PyQt6.QtCore import QTimer
from ui.unified_timer import get_unified_timer
from ui.event_debouncer import get_event_debouncer
from ui.render_optimizer import get_render_optimizer
from ui.performance_config import performance_config


class ChatWidgetOptimized:
    """최적화된 ChatWidget 예시"""
    
    def __init__(self):
        # 기존: 여러 개의 타이머
        # self._theme_timer = QTimer()
        # self._scroll_timer = QTimer()
        # self._update_timer = QTimer()
        
        # 최적화: 통합 타이머 사용
        self._unified_timer = get_unified_timer()
        self._debouncer = get_event_debouncer()
        self._render_optimizer = get_render_optimizer()
        
        self._setup_optimized_timers()
    
    def _setup_optimized_timers(self):
        """최적화된 타이머 설정"""
        # 테마 업데이트 (필요할 때만 활성화)
        self._unified_timer.register(
            "theme_update",
            self._update_theme,
            enabled=False
        )
        
        # 스크롤 체크 (스크롤 중에만 활성화)
        self._unified_timer.register(
            "scroll_check",
            self._check_scroll_position,
            enabled=False
        )
    
    def _apply_theme(self):
        """테마 적용 - 디바운싱"""
        # 기존: 즉시 실행
        # self._update_theme()
        
        # 최적화: 디바운싱 적용
        self._debouncer.debounce(
            "theme_apply",
            self._update_theme,
            delay_ms=performance_config.THEME_APPLY_DELAY_MS
        )
    
    def _update_theme(self):
        """실제 테마 업데이트"""
        pass
    
    def on_scroll_event(self):
        """스크롤 이벤트 핸들러"""
        # 기존: 스크롤할 때마다 호출
        # self._load_more_messages()
        
        # 최적화: 디바운싱 + 타이머 활성화
        self._unified_timer.enable("scroll_check")
        self._debouncer.debounce(
            "scroll_end",
            lambda: self._unified_timer.disable("scroll_check"),
            delay_ms=performance_config.SCROLL_DEBOUNCE_MS
        )
    
    def _check_scroll_position(self):
        """스크롤 위치 체크"""
        # 스크롤 상단 근처면 메시지 로드
        pass
    
    def _render_messages(self, messages):
        """메시지 렌더링 - 배치 처리"""
        # 기존: 한 번에 모두 렌더링
        # for msg in messages:
        #     self._render_single_message(msg)
        
        # 최적화: 배치 단위로 렌더링
        self._render_optimizer.schedule_render(
            messages,
            self._render_messages_batch
        )
    
    def _render_messages_batch(self, batch):
        """배치 단위 메시지 렌더링"""
        for msg in batch:
            self._render_single_message(msg)
    
    def _render_single_message(self, msg):
        """단일 메시지 렌더링"""
        pass
    
    def cleanup(self):
        """정리 - 메모리 누수 방지"""
        # 타이머 정리
        self._unified_timer.cleanup()
        self._debouncer.cleanup()
        self._render_optimizer.cleanup()


# 사용 예시
def example_usage():
    """최적화 적용 예시"""
    
    # 1. 통합 타이머 사용
    timer = get_unified_timer()
    timer.register("my_task", lambda: print("Task executed"))
    
    # 2. 이벤트 디바운싱
    debouncer = get_event_debouncer()
    debouncer.debounce("resize", lambda: print("Resized"), 100)
    
    # 3. 렌더링 최적화
    optimizer = get_render_optimizer()
    messages = list(range(1000))
    optimizer.schedule_render(messages, lambda batch: print(f"Rendered {len(batch)} items"))


if __name__ == "__main__":
    example_usage()
