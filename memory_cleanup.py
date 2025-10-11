#!/usr/bin/env python3
"""메모리 정리 유틸리티 - 자동 관리 모드"""

from core.logging import get_logger

logger = get_logger("memory_cleanup")

class MemoryCleanup:
    """메모리 자동 관리 (머신에 위임)"""
    
    def __init__(self):
        pass
    
    def start_auto_cleanup(self):
        """자동 메모리 정리 - 머신 자동 관리"""
        logger.debug("메모리 자동 관리 모드 (머신 위임)")
    
    def stop_auto_cleanup(self):
        """자동 메모리 정리 중지"""
        pass
    
    def cleanup(self):
        """메모리 정리 - 머신 자동 관리"""
        pass

# 전역 인스턴스
memory_cleanup = MemoryCleanup()
