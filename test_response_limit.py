#!/usr/bin/env python3
"""
응답 길이 제한 기능 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.chat_processor import SimpleChatProcessor
from core.file_utils import load_config

def test_response_limit():
    """응답 길이 제한 기능 테스트"""
    
    # 설정 확인
    config = load_config()
    response_settings = config.get('response_settings', {})
    print(f"현재 응답 설정: {response_settings}")
    
    # SimpleChatProcessor 인스턴스 생성
    processor = SimpleChatProcessor()
    
    # 긴 응답 시뮬레이션 (96,223자와 유사한 길이)
    long_response = "이것은 매우 긴 응답입니다. " * 5000  # 약 15,000자
    print(f"원본 응답 길이: {len(long_response)}자")
    
    # 길이 제한 적용
    limited_response = processor._limit_response_length(long_response)
    print(f"제한된 응답 길이: {len(limited_response)}자")
    
    # 결과 출력
    print("\n=== 제한된 응답 미리보기 ===")
    print(limited_response[:500] + "..." if len(limited_response) > 500 else limited_response)
    
    # 설정 변경 테스트
    print("\n=== 설정 변경 테스트 ===")
    
    # 길이 제한 비활성화
    test_config = config.copy()
    test_config['response_settings']['enable_length_limit'] = False
    
    # 임시로 설정 변경 (실제로는 파일을 수정하지 않음)
    original_load_config = processor._limit_response_length.__globals__['load_config']
    processor._limit_response_length.__globals__['load_config'] = lambda: test_config
    
    unlimited_response = processor._limit_response_length(long_response)
    print(f"길이 제한 비활성화 시 응답 길이: {len(unlimited_response)}자")
    
    # 원래 설정 복원
    processor._limit_response_length.__globals__['load_config'] = original_load_config
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    test_response_limit()