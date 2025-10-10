#!/usr/bin/env python3
"""메모리 정리 유틸리티"""

import gc
from PyQt6.QtCore import QTimer
from core.logging import get_logger

logger = get_logger("memory_cleanup")

class MemoryCleanup:
    """메모리 정리 관리자"""
    
    def __init__(self):
        self.cleanup_timer = None
        self.cleanup_interval = 60000  # 1분마다
    
    def start_auto_cleanup(self):
        """자동 메모리 정리 시작"""
        if self.cleanup_timer is None:
            self.cleanup_timer = QTimer()
            self.cleanup_timer.timeout.connect(self.cleanup)
            self.cleanup_timer.start(self.cleanup_interval)
            logger.debug("자동 메모리 정리 시작")
    
    def stop_auto_cleanup(self):
        """자동 메모리 정리 중지"""
        if self.cleanup_timer:
            self.cleanup_timer.stop()
            self.cleanup_timer.deleteLater()
            self.cleanup_timer = None
            logger.debug("자동 메모리 정리 중지")
    
    def cleanup(self):
        """메모리 정리 실행"""
        try:
            # Python 가비지 컬렉션 강제 실행
            collected = gc.collect()
            logger.debug(f"메모리 정리 완료: {collected}개 객체 수집")
        except Exception as e:
            logger.debug(f"메모리 정리 오류: {e}")

# 전역 인스턴스
memory_cleanup = MemoryCleanup()
