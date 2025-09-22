#!/usr/bin/env python3
"""
새로운 아이콘으로 기존 이미지들을 대체하는 스크립트
"""

from PIL import Image, ImageFilter
import numpy as np
import os

def make_background_transparent(input_path, threshold=240):
    """이미지의 흰색 배경을 투명하게 만들고 반환"""
    try:
        img = Image.open(input_path)
        img = img.convert("RGBA")
        data = np.array(img)
        
        red, green, blue, alpha = data.T
        white_areas = (red >= threshold) & (green >= threshold) & (blue >= threshold)
        data[..., 3][white_areas.T] = 0
        
        return Image.fromarray(data)
    except Exception as e:
        print(f"투명화 오류: {e}")
        return None

def resize_high_quality(img, size):
    """고품질 이미지 리사이징"""
    try:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        resized = resized.filter(ImageFilter.UnsharpMask(radius=0.5, percent=150, threshold=3))
        return resized
    except Exception as e:
        print(f"리사이징 오류: {e}")
        return None

if __name__ == "__main__":
    input_file = "agentic_ai_128X128.png"
    
    if not os.path.exists(input_file):
        print(f"파일을 찾을 수 없습니다: {input_file}")
        exit(1)
    
    # 투명 배경으로 변환 (더 낮은 임계값 사용)
    print("배경을 투명하게 변환 중...")
    transparent_img = make_background_transparent(input_file, threshold=200)
    
    if transparent_img is None:
        print("투명화 실패")
        exit(1)
    
    # 다양한 크기로 생성하여 기존 파일 대체
    sizes = [
        (48, 48, "image/app_icon_48.png"),
        (64, 64, "image/app_icon_64.png"), 
        (128, 128, "image/app_icon_128.png")
    ]
    
    for width, height, output_path in sizes:
        resized_img = resize_high_quality(transparent_img, (width, height))
        if resized_img:
            resized_img.save(output_path, "PNG", optimize=True)
            print(f"생성 완료: {output_path} ({width}x{height})")
        else:
            print(f"생성 실패: {output_path}")
    
    print("모든 아이콘 업데이트 완료!")