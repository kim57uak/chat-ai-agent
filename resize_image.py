#!/usr/bin/env python3
"""
고품질 이미지 리사이징 스크립트
"""

from PIL import Image, ImageFilter
import os

def resize_high_quality(input_path, output_path, size):
    """
    고품질 이미지 리사이징
    """
    try:
        with Image.open(input_path) as img:
            # RGBA 모드로 변환
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 고품질 리샘플링으로 크기 조정
            resized = img.resize(size, Image.Resampling.LANCZOS)
            
            # 약간의 샤프닝 적용
            resized = resized.filter(ImageFilter.UnsharpMask(radius=0.5, percent=150, threshold=3))
            
            # 저장
            resized.save(output_path, 'PNG', optimize=True)
            print(f"고품질 리사이징 완료: {output_path} ({size[0]}x{size[1]})")
            
    except Exception as e:
        print(f"리사이징 오류: {e}")

if __name__ == "__main__":
    # 다양한 크기로 고품질 아이콘 생성
    input_file = "image/Agentic_AI_transparent.png"
    
    if os.path.exists(input_file):
        # 세션 패널용 (48x48)
        resize_high_quality(input_file, "image/app_icon_48.png", (48, 48))
        
        # 애플리케이션 아이콘용 (64x64)
        resize_high_quality(input_file, "image/app_icon_64.png", (64, 64))
        
        # 고해상도용 (128x128)
        resize_high_quality(input_file, "image/app_icon_128.png", (128, 128))
    else:
        print(f"파일을 찾을 수 없습니다: {input_file}")