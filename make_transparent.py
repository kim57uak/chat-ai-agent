#!/usr/bin/env python3
"""
이미지 배경을 투명하게 만드는 스크립트
"""

from PIL import Image
import numpy as np

def make_background_transparent(input_path, output_path, threshold=240):
    """
    이미지의 흰색 배경을 투명하게 만듭니다.
    
    Args:
        input_path: 입력 이미지 경로
        output_path: 출력 이미지 경로
        threshold: 투명화할 밝기 임계값 (0-255)
    """
    try:
        # 이미지 열기
        img = Image.open(input_path)
        
        # RGBA 모드로 변환 (투명도 채널 추가)
        img = img.convert("RGBA")
        
        # numpy 배열로 변환
        data = np.array(img)
        
        # RGB 채널 분리
        red, green, blue, alpha = data.T
        
        # 흰색에 가까운 픽셀 찾기 (모든 RGB 값이 threshold 이상)
        white_areas = (red >= threshold) & (green >= threshold) & (blue >= threshold)
        
        # 흰색 영역을 투명하게 만들기
        data[..., 3][white_areas.T] = 0
        
        # 이미지로 다시 변환
        result_img = Image.fromarray(data)
        
        # 저장
        result_img.save(output_path, "PNG")
        print(f"투명 배경 이미지 생성 완료: {output_path}")
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    # Agentic_AI.png의 배경을 투명하게 만들기
    make_background_transparent("Agentic_AI.png", "Agentic_AI_transparent.png", threshold=240)