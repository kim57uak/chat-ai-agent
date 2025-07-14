#!/usr/bin/env python3
"""
스트림 출력과 마크다운 렌더링 테스트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    print("🚀 스트림 출력 및 마크다운 렌더링 테스트 시작")
    print("=" * 50)
    print("✅ 구현된 기능들:")
    print("1. Enter키로 메시지 전송 (Shift+Enter로 줄바꿈)")
    print("2. 스트림 방식 AI 응답 출력")
    print("3. 개선된 마크다운 렌더링:")
    print("   - 코드 블록 들여쓰기 자동 정리")
    print("   - 헤딩, 강조, 취소선, 체크박스 지원")
    print("   - 인용문, 수평선, 링크 지원")
    print("   - 개선된 테이블 스타일")
    print("4. 향상된 웹뷰 CSS")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    print("💡 테스트 방법:")
    print("1. 긴 텍스트를 입력하여 스트림 출력 확인")
    print("2. 마크다운 문법을 사용하여 렌더링 확인")
    print("3. Enter키와 Shift+Enter 동작 확인")
    
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())