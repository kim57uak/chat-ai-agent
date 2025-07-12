#!/usr/bin/env python3
"""
이미지 텍스트 추출(OCR) 테스트 스크립트
Gemini 2.0 Flash 모델의 이미지 처리 성능을 테스트합니다.
"""

import sys
import os
import base64
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.ai_agent import AIAgent
from core.file_utils import load_model_api_key

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def encode_image_to_base64(image_path: str) -> str:
    """이미지 파일을 Base64로 인코딩"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"이미지 인코딩 오류: {e}")
        return None

def test_image_ocr(model_choice="gemini"):
    """이미지 OCR 테스트"""
    print("🔍 이미지 텍스트 추출(OCR) 테스트 시작")
    print("=" * 50)
    
    # 모델별 설정
    if model_choice == "gpt":
        model_name = "gpt-4-vision-preview"
        print(f"🤖 모델: {model_name}")
    else:
        model_name = "gemini-2.0-flash-exp"
        print(f"🤖 모델: {model_name}")
    
    # API 키 로드
    try:
        api_key = load_model_api_key(model_name)
        if not api_key:
            print(f"❌ {model_name} API 키를 찾을 수 없습니다.")
            print(f"config.json에서 {model_name} API 키를 설정해주세요.")
            return
    except Exception as e:
        print(f"❌ API 키 로드 오류: {e}")
        return
    
    # AI 에이전트 생성
    try:
        agent = AIAgent(api_key, model_name)
        print(f"✅ {model_name} 에이전트 생성 완료")
    except Exception as e:
        print(f"❌ 에이전트 생성 오류: {e}")
        return
    
    # 테스트 이미지 경로 (사용자가 제공해야 함)
    test_image_path = input("📁 테스트할 이미지 파일 경로를 입력하세요: ").strip()
    
    if not test_image_path or not os.path.exists(test_image_path):
        print("❌ 유효한 이미지 파일 경로를 입력해주세요.")
        return
    
    # 이미지를 Base64로 인코딩
    print("🔄 이미지 인코딩 중...")
    image_base64 = encode_image_to_base64(test_image_path)
    
    if not image_base64:
        print("❌ 이미지 인코딩 실패")
        return
    
    print(f"✅ 이미지 인코딩 완료 (크기: {len(image_base64)} 문자)")
    
    # 텍스트 추출 요청 생성
    user_input = f"[IMAGE_BASE64]{image_base64}[/IMAGE_BASE64]"
    
    print("🚀 텍스트 추출 시작...")
    print("-" * 30)
    
    try:
        # 이미지 텍스트 추출 실행
        response = agent.simple_chat(user_input)
        
        print("📄 추출 결과:")
        print("=" * 50)
        print(response)
        print("=" * 50)
        
        # 결과 분석
        if "추출된 텍스트" in response or "텍스트" in response:
            print("✅ 텍스트 추출 성공!")
        else:
            print("⚠️  텍스트 추출 결과를 확인해주세요.")
            
    except Exception as e:
        print(f"❌ 텍스트 추출 오류: {e}")
        logger.error(f"OCR 테스트 오류: {e}")

def create_sample_test():
    """샘플 테스트 이미지 생성 (텍스트가 포함된 간단한 이미지)"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 간단한 텍스트 이미지 생성
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # 텍스트 추가
        text_lines = [
            "안녕하세요! Hello World!",
            "이것은 OCR 테스트입니다.",
            "숫자: 12345",
            "특수문자: @#$%^&*()"
        ]
        
        y_position = 20
        for line in text_lines:
            draw.text((20, y_position), line, fill='black')
            y_position += 40
        
        # 이미지 저장
        sample_path = "sample_ocr_test.png"
        img.save(sample_path)
        print(f"✅ 샘플 테스트 이미지 생성: {sample_path}")
        return sample_path
        
    except ImportError:
        print("⚠️  PIL(Pillow) 라이브러리가 필요합니다: pip install Pillow")
        return None
    except Exception as e:
        print(f"❌ 샘플 이미지 생성 오류: {e}")
        return None

if __name__ == "__main__":
    print("🤖 Chat AI Agent - 이미지 OCR 테스트")
    print("다양한 AI 모델의 텍스트 추출 성능을 테스트합니다.")
    print()
    
    # 모델 선택
    model_choice = input("🤖 모델 선택:\n1. Gemini 2.0 Flash\n2. GPT-4 Vision\n선택 (1/2): ").strip()
    model_type = "gpt" if model_choice == "2" else "gemini"
    
    # 테스트 방식 선택
    test_choice = input("\n📁 테스트 방식:\n1. 기존 이미지 테스트\n2. 샘플 이미지 생성 후 테스트\n선택 (1/2): ").strip()
    
    if test_choice == "2":
        sample_path = create_sample_test()
        if sample_path:
            print(f"샘플 이미지로 테스트를 진행합니다: {sample_path}")
            test_image_ocr(model_type)
    else:
        test_image_ocr(model_type)