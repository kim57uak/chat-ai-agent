"""메모리 관리 모듈 - 모니터링 전용"""
from core.logging import get_logger
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from ui.performance_optimizer import performance_optimizer

logger = get_logger("memory_manager")


class MemoryManager(QObject):
    """메모리 모니터링 전용 (자동 정리 제거)"""
    
    memory_warning = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_memory)
        
    def start_monitoring(self, interval_ms=60000):
        """메모리 모니터링 시작 (1분마다)"""
        self.monitor_timer.start(interval_ms)
        
    def stop_monitoring(self):
        """메모리 모니터링 중지"""
        if self.monitor_timer:
            self.monitor_timer.stop()
        
    def check_memory(self):
        """메모리 사용률 확인 (경고만)"""
        try:
            memory_info = performance_optimizer.get_memory_usage()
            if memory_info:
                memory_percent = memory_info.get('memory_percent', 0)
                if memory_percent > 85:
                    self.memory_warning.emit(memory_percent)
        except Exception as e:
            logger.warning(f"메모리 모니터링 오류: {e}")
            
    def light_cleanup(self):
        """가벼운 정리 - 머신 자동 관리"""
        pass
            
    def force_cleanup(self):
        """강제 정리 - 머신 자동 관리"""
        pass
            
    def get_memory_status(self):
        """현재 메모리 상태 반환"""
        return performance_optimizer.get_memory_usage()


memory_manager = MemoryManager()