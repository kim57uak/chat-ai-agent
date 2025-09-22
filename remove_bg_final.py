#!/usr/bin/env python3
from PIL import Image
import numpy as np

def remove_all_background(input_path):
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img)
    
    # 모든 배경색 제거 (임계값 150 이상)
    bg_mask = (data[:,:,0] > 150) & (data[:,:,1] > 150) & (data[:,:,2] > 150)
    data[bg_mask] = [0, 0, 0, 0]
    
    return Image.fromarray(data)

# 원본 처리
img = remove_all_background("agentic_ai_128X128.png")

# 크기별 생성
for size, path in [(48, "image/app_icon_48.png"), (64, "image/app_icon_64.png"), (128, "image/app_icon_128.png")]:
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(path, "PNG")
    print(f"생성: {path}")

# 원본도 투명 배경으로 저장
img.save("image/agentic_ai_transparent.png", "PNG")
print("완전 투명 배경 아이콘 생성 완료!")