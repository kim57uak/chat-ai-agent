"""
메모리 관리 모듈 - 자동 메모리 정리 및 모니터링
"""
import gc
import threading
import time
from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from ui.performance_optimizer import performance_optimizer


class MemoryManager(QObject):
    """메모리 자동 관리 클래스"""
    
    memory_warning = pyqtSignal(float)  # 메모리 사용률 경고
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.auto_cleanup)
        self.monitoring_enabled = True
        
    def start_monitoring(self, interval_ms=30000):  # 30초마다
        """메모리 모니터링 시작"""
        self.cleanup_timer.start(interval_ms)
        
    def stop_monitoring(self):
        """메모리 모니터링 중지"""
        self.cleanup_timer.stop()
        
    def auto_cleanup(self):
        """자동 메모리 정리"""
        try:
            # 메모리 사용률 확인
            memory_info = performance_optimizer.get_memory_usage()
            
            if memory_info:
                memory_percent = memory_info.get('memory_percent', 0)
                
                # 메모리 사용률이 80% 이상이면 정리
                if memory_percent > 80:
                    self.force_cleanup()
                    self.memory_warning.emit(memory_percent)
                # 60% 이상이면 가벼운 정리
                elif memory_percent > 60:
                    self.light_cleanup()
                    
        except Exception as e:
            print(f"자동 메모리 정리 오류: {e}")
            
    def light_cleanup(self):
        """가벼운 메모리 정리"""
        try:
            # Python 가비지 컬렉션
            gc.collect()
            
        except Exception as e:
            print(f"가벼운 메모리 정리 오류: {e}")
            
    def force_cleanup(self):
        """강제 메모리 정리"""
        try:
            # 강제 가비지 컬렉션
            for _ in range(3):
                gc.collect()
                
            # 플랫폼별 메모리 정리
            performance_optimizer.cleanup_memory()
            
            print("강제 메모리 정리 완료")
            
        except Exception as e:
            print(f"강제 메모리 정리 오류: {e}")
            
    def get_memory_status(self):
        """현재 메모리 상태 반환"""
        return performance_optimizer.get_memory_usage()


# 전역 메모리 매니저
memory_manager = MemoryManager()