"""
Memory Security Manager
메모리 보안 관리 클래스
"""

import gc
import sys
import ctypes
from core.logging import get_logger
from typing import Any, Optional

logger = get_logger("memory_security")


class MemorySecurityManager:
    """메모리 보안 관리자"""
    
    @staticmethod
    def secure_delete_variable(var_name: str, frame: Optional[Any] = None):
        """변수를 안전하게 삭제"""
        try:
            if frame is None:
                frame = sys._getframe(1)
            
            if var_name in frame.f_locals:
                # 메모리 덮어쓰기 시도
                if isinstance(frame.f_locals[var_name], (str, bytes)):
                    try:
                        # 문자열/바이트 데이터 덮어쓰기
                        original = frame.f_locals[var_name]
                        if isinstance(original, str):
                            frame.f_locals[var_name] = '\x00' * len(original)
                        else:
                            frame.f_locals[var_name] = b'\x00' * len(original)
                    except:
                        pass
                
                # 변수 삭제
                del frame.f_locals[var_name]
                
        except Exception as e:
            logger.debug(f"변수 안전 삭제 실패: {e}")
    
    @staticmethod
    def force_garbage_collection():
        """강제 가비지 컬렉션 실행"""
        try:
            # 3번 실행하여 순환 참조까지 정리
            for _ in range(3):
                collected = gc.collect()
            
            logger.debug(f"가비지 컬렉션 완료: {collected}개 객체 정리")
            return collected
        except Exception as e:
            logger.error(f"가비지 컬렉션 실패: {e}")
            return 0
    
    @staticmethod
    def clear_sensitive_data(*variables):
        """민감한 데이터 메모리에서 즉시 제거"""
        frame = sys._getframe(1)
        
        for var in variables:
            if isinstance(var, str):
                # 변수명으로 전달된 경우
                MemorySecurityManager.secure_delete_variable(var, frame)
            else:
                # 실제 객체로 전달된 경우
                try:
                    if hasattr(var, '__dict__'):
                        var.__dict__.clear()
                    del var
                except:
                    pass
        
        # 강제 가비지 컬렉션
        MemorySecurityManager.force_garbage_collection()
    
    @staticmethod
    def get_memory_usage() -> dict:
        """현재 메모리 사용량 반환"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': round(process.memory_percent(), 2)
            }
        except ImportError:
            # psutil이 없는 경우 기본 정보만
            return {
                'objects': len(gc.get_objects()),
                'garbage': len(gc.garbage)
            }
        except Exception as e:
            logger.error(f"메모리 사용량 조회 실패: {e}")
            return {}


# 전역 메모리 보안 매니저
memory_security = MemorySecurityManager()