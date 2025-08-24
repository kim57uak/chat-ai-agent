#!/usr/bin/env python3
"""
빌드 문제 해결 스크립트
설정 파일 확인 및 재빌드
"""

import os
import sys
import shutil
import platform
from pathlib import Path

def check_config_files():
    """설정 파일들 존재 확인"""
    required_files = {
        'config.json': 'AI 모델 설정',
        'mcp.json': 'MCP 서버 설정', 
        'ai_model.json': 'AI 모델 정보'
    }
    
    missing = []
    for file, desc in required_files.items():
        if not os.path.exists(file):
            missing.append(f"{file} ({desc})")
            print(f"❌ Missing: {file}")
        else:
            print(f"✅ Found: {file}")
    
    return missing

def create_default_configs():
    """기본 설정 파일들 생성"""
    
    # config.json 생성
    if not os.path.exists('config.json'):
        config_content = """{
  "models": {
    "gpt-3.5-turbo": {
      "api_key": "your-openai-api-key",
      "provider": "openai"
    },
    "gpt-4": {
      "api_key": "your-openai-api-key", 
      "provider": "openai"
    },
    "gemini-2.0-flash": {
      "api_key": "your-google-api-key",
      "provider": "google"
    }
  },
  "conversation_settings": {
    "enable_history": true,
    "max_history_pairs": 5,
    "max_tokens_estimate": 20000
  },
  "response_settings": {
    "max_tokens": 4096,
    "enable_streaming": true,
    "streaming_chunk_size": 100
  }
}"""
        with open('config.json', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Created default config.json")
    
    # ai_model.json 생성
    if not os.path.exists('ai_model.json'):
        ai_model_content = """{
  "models": [
    {
      "name": "gpt-3.5-turbo",
      "display_name": "GPT-3.5 Turbo",
      "provider": "openai",
      "max_tokens": 4096
    },
    {
      "name": "gpt-4",
      "display_name": "GPT-4",
      "provider": "openai", 
      "max_tokens": 8192
    },
    {
      "name": "gemini-2.0-flash",
      "display_name": "Gemini 2.0 Flash",
      "provider": "google",
      "max_tokens": 8192
    }
  ]
}"""
        with open('ai_model.json', 'w', encoding='utf-8') as f:
            f.write(ai_model_content)
        print("✅ Created default ai_model.json")

def clean_build():
    """빌드 아티팩트 정리"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🧹 Cleaned: {dir_name}")
    
    import glob
    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            os.remove(file)
            print(f"🧹 Cleaned: {file}")

def rebuild():
    """재빌드 실행"""
    print("🔨 Starting rebuild...")
    
    # spec 파일 생성
    os.system("python3 pyinstaller_spec.py")
    
    # 빌드 실행
    import platform
    current_platform = platform.system().lower()
    
    if current_platform == "darwin":
        spec_file = "chat-ai-agent-mac.spec"
    elif current_platform == "windows":
        spec_file = "chat-ai-agent-windows.spec"
    else:
        spec_file = "chat-ai-agent-linux.spec"
    
    if os.path.exists(spec_file):
        os.system(f"python3 -m PyInstaller {spec_file} --clean --noconfirm")
        print("✅ Rebuild completed!")
    else:
        print("❌ Spec file not found!")

def main():
    """메인 함수"""
    print("🔧 Chat AI Agent Build Fix")
    print("=" * 40)
    
    # 1. 설정 파일 확인
    print("1. Checking configuration files...")
    missing = check_config_files()
    
    # 2. 누락된 파일 생성
    if missing:
        print(f"\n2. Creating missing files: {len(missing)}")
        create_default_configs()
    else:
        print("\n2. All configuration files found!")
    
    # 3. 빌드 정리
    print("\n3. Cleaning build artifacts...")
    clean_build()
    
    # 4. 재빌드
    print("\n4. Rebuilding application...")
    rebuild()
    
    print("\n🎉 Fix completed!")
    print("Now test the built application:")
    
    current_platform = platform.system().lower()
    if current_platform == "darwin":
        print("  ./build_output/darwin/ChatAIAgent.app/Contents/MacOS/ChatAIAgent")
    elif current_platform == "windows":
        print("  .\\build_output\\windows\\ChatAIAgent\\ChatAIAgent.exe")
    else:
        print("  ./build_output/linux/ChatAIAgent/ChatAIAgent")

if __name__ == "__main__":
    main()