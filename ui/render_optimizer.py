"""
Render Optimizer
렌더링을 배치 처리하여 성능 개선
"""

from PyQt6.QtCore import QObject, QTimer
from typing import List, Callable
from collections import deque
from core.logging import get_logger

logger = get_logger("render_optimizer")


class RenderBatch:
    """렌더링 배치"""
    
    def __init__(self, items: List, callback: Callable):
        self.items = items
        self.callback = callback


class RenderOptimizer(QObject):
    """렌더링 최적화 - 배치 처리"""
    
    def __init__(self, batch_size: int = 50, delay_ms: int = 16):
        super().__init__()
        self._batch_size = batch_size
        self._delay_ms = delay_ms
        
        self._queue = deque()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._process_batch)
        
        self._is_processing = False
    
    def schedule_render(self, items: List, callback: Callable):
        """렌더링 예약"""
        if not items:
            return
        
        self._queue.append(RenderBatch(items, callback))
        
        if not self._is_processing and not self._timer.isActive():
            self._timer.start(self._delay_ms)
    
    def _process_batch(self):
        """배치 처리"""
        if not self._queue or self._is_processing:
            return
        
        self._is_processing = True
        
        try:
            batch = self._queue.popleft()
            items_to_process = batch.items[:self._batch_size]
            remaining_items = batch.items[self._batch_size:]
            
            # 콜백 실행
            batch.callback(items_to_process)
            
            # 남은 아이템이 있으면 다시 큐에 추가
            if remaining_items:
                self._queue.appendleft(RenderBatch(remaining_items, batch.callback))
            
            # 큐에 더 있으면 계속 처리
            if self._queue:
                self._timer.start(self._delay_ms)
        
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
        
        finally:
            self._is_processing = False
    
    def clear(self):
        """큐 비우기"""
        self._queue.clear()
        self._timer.stop()
        self._is_processing = False
    
    def cleanup(self):
        """정리"""
        self.clear()


# 전역 인스턴스
_render_optimizer = None


def get_render_optimizer() -> RenderOptimizer:
    """렌더링 최적화 인스턴스 반환"""
    global _render_optimizer
    if _render_optimizer is None:
        from ui.performance_config import performance_config
        _render_optimizer = RenderOptimizer(
            batch_size=performance_config.RENDER_BATCH_SIZE,
            delay_ms=performance_config.RENDER_DELAY_MS
        )
    return _render_optimizer
