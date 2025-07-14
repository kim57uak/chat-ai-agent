#!/usr/bin/env python3
"""
Markdown table rendering test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.chat_widget import ChatWidget
from PyQt6.QtWidgets import QApplication

def test_markdown_table():
    """Test markdown table rendering"""
    
    # Create test table
    test_table = """
| 종 🌿 | 특징 ✨ | 맛과 향 👃 | 재배 조건 🌍 | 카페인 함량 ⚡ | 시장 점유율 📊 |
|-------|--------|-----------|-------------|---------------|---------------|
| **아라비카 (Arabica)** | • 전 세계 생산량의 약 60-70% 차지<br>- 섬세하고 복합적인 향미<br>- 높은 고도에서 재배<br>- 병충해에 취약 | • 산미가 풍부하고 부드러움<br>- 꽃, 과일, 캐러멜, 초콜릿 등 다양한 아로마<br>- 균형 잡힌 바디감 | • 해발 800m 이상 고지대<br>- 연평균 15-24°C<br>- 충분한 강수량 | • 낮음 (1.5% 내외) | • 가장 높음 (고급 커피 시장) |
| **로부스타 (Robusta)** | • 전 세계 생산량의 약 30-40% 차지<br>- 강한 생명력과 병충해 저항성<br>- 낮은 고도에서도 재배 가능<br>- 주로 인스턴트 커피, 블렌딩용 | • 쓴맛이 강하고 바디감이 무거움<br>- 고무, 흙, 견과류 향<br>- 크레마가 풍부 | • 해발 0-800m 저지대<br>- 연평균 22-26°C<br>- 고온다습한 기후 | • 높음 (2.5-4.5% 내외) | • 높음 (대량 생산 및 상업용) |
"""
    
    app = QApplication(sys.argv)
    
    # Create chat widget
    chat_widget = ChatWidget()
    
    # Test the markdown formatting
    formatted_html = chat_widget._format_markdown(test_table)
    
    print("=== Original Markdown ===")
    print(test_table)
    print("\n=== Formatted HTML ===")
    print(formatted_html)
    
    # Show in GUI
    chat_widget.append_chat('테스트', test_table)
    chat_widget.show()
    
    return app.exec()

if __name__ == '__main__':
    test_markdown_table()