#!/usr/bin/env python3
"""
안전한 빌드 스크립트 - 설정 파일 백업/복원 포함
삭제하지 말것.
"""

import os
import sys
import shutil
import subprocess
import platform
import json
from pathlib import Path

# 외부 경로에서 인식할 설정 파일들 (개인키 포함)
EXTERNAL_CONFIG_FILES = ["config.json", "mcp.json", "news_config.json", "prompt_config.json"]

# 패키징에 포함할 JSON 파일들 (개인키 없음)
INCLUDE_JSON_FILES = [
    "ai_model.json", "templates.json", "theme.json", 
    "mcp_server_state.json", "splitter_state.json", "user_config_path.json"
]


def backup_configs():
    """기존 설정 파일들 백업"""
    for file in EXTERNAL_CONFIG_FILES:
        if os.path.exists(file):
            shutil.copy(file, f"{file}.backup")
            print(f"✓ {file} 백업 완료")


def restore_configs():
    """백업된 설정 파일들 복원"""
    for file in EXTERNAL_CONFIG_FILES:
        backup_file = f"{file}.backup"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, file)
            os.remove(backup_file)
            print(f"✓ {file} 복원 완료")


def create_sample_configs():
    """빌드용 샘플 설정 파일들 생성"""
    
    # 샘플 config.json (개인키 제거)
    config = {
        "current_model": "gemini-2.0-flash",
        "models": {
            "gemini-2.0-flash": {
                "api_key": "YOUR_GOOGLE_API_KEY",
                "provider": "google"
            },
            "gpt-3.5-turbo": {
                "api_key": "YOUR_OPENAI_API_KEY",
                "provider": "openai"
            }
        },
        "conversation_settings": {
            "enable_history": True,
            "max_history_pairs": 5,
            "max_tokens_estimate": 20000
        },
        "response_settings": {
            "max_tokens": 4096,
            "enable_streaming": True,
            "streaming_chunk_size": 100
        },
        "current_theme": "material_dark"
    }

    # 샘플 mcp.json
    mcp = {
        "mcpServers": {
            "example-server": {
                "command": "node",
                "args": ["path/to/server.js"],
                "env": {},
                "description": "Example MCP Server"
            }
        }
    }

    # 샘플 news_config.json
    news = {
        "news_sources": {
            "domestic": [],
            "international": [],
            "earthquake": []
        },
        "update_interval": 300,
        "max_articles": 10
    }

    # 샘플 prompt_config.json
    prompt = {
        "openai": {
            "system_enhancement": "You are a helpful AI assistant.",
            "tool_calling": "Use tools when necessary to provide accurate information."
        },
        "google": {
            "react_pattern": "Think step by step and use available tools."
        },
        "common": {
            "system_base": "Always be helpful, harmless, and honest."
        }
    }

    # 파일 생성
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    with open("mcp.json", "w", encoding="utf-8") as f:
        json.dump(mcp, f, indent=2, ensure_ascii=False)

    with open("news_config.json", "w", encoding="utf-8") as f:
        json.dump(news, f, indent=2, ensure_ascii=False)

    with open("prompt_config.json", "w", encoding="utf-8") as f:
        json.dump(prompt, f, indent=2, ensure_ascii=False)

    print("✓ 샘플 설정 파일들 생성 완료")


def clean_build():
    """빌드 디렉토리 정리"""
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ {dir_name} 디렉토리 정리 완료")
    
    # __pycache__ 재귀적으로 정리
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"✓ {pycache_path} 정리 완료")


def build_executable():
    """실행 파일 빌드"""
    system = platform.system()
    print(f"🔨 {system}용 빌드 시작...")

    try:
        # PyInstaller 명령어 실행
        cmd = ["pyinstaller", "--clean", "--noconfirm", "chat_ai_agent.spec"]
        
        print(f"실행 명령어: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            print("빌드 출력:")
            print(result.stdout)
        
        print("✓ PyInstaller 빌드 완료")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller가 설치되지 않았습니다. 'pip install pyinstaller' 실행하세요.")
        return False


def verify_build_contents():
    """빌드된 앱의 내용 확인"""
    system = platform.system()
    dist_dir = Path("dist")
    
    if system == "Darwin":  # macOS
        app_path = dist_dir / "ChatAIAgent.app"
        resources_path = app_path / "Contents" / "Resources"
        
        if resources_path.exists():
            print("\n📋 앱 번들 내용 확인:")
            json_files = list(resources_path.glob("*.json"))
            print(f"Resources 디렉토리에 {len(json_files)}개 JSON 파일 포함됨")
            
            required_files = ["theme.json", "templates.json", "ai_model.json"]
            missing_files = []
            
            for required_file in required_files:
                file_path = resources_path / required_file
                if file_path.exists():
                    print(f"✓ {required_file}")
                else:
                    print(f"❌ {required_file} 누락")
                    missing_files.append(required_file)
            
            if missing_files:
                print(f"\n⚠️ 누락된 필수 파일들: {', '.join(missing_files)}")
                print("PyInstaller spec 파일을 확인하세요.")
                return False
            else:
                print("✅ 모든 필수 파일이 포함되었습니다.")
                return True
        else:
            print("❌ Resources 디렉토리를 찾을 수 없습니다.")
            return False
    
    return True

def create_distribution():
    """배포용 패키지 생성"""
    system = platform.system()
    dist_dir = Path("dist")

    if system == "Darwin":  # macOS
        app_path = dist_dir / "ChatAIAgent.app"
        if app_path.exists():
            print(f"✓ macOS 앱 번들 생성: {app_path}")
            
            # DMG 생성 시도
            try:
                dmg_path = dist_dir / "ChatAIAgent-macOS.dmg"
                if dmg_path.exists():
                    dmg_path.unlink()
                
                subprocess.run([
                    "hdiutil", "create",
                    "-volname", "ChatAIAgent",
                    "-srcfolder", str(app_path),
                    "-ov", "-format", "UDZO",
                    str(dmg_path)
                ], check=True)
                print(f"✓ DMG 파일 생성: {dmg_path}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ DMG 생성 실패: {e}")
            except FileNotFoundError:
                print("⚠️ hdiutil을 찾을 수 없습니다 (macOS 전용)")

    elif system == "Windows":
        exe_path = dist_dir / "ChatAIAgent.exe"
        if exe_path.exists():
            print(f"✓ Windows 실행 파일 생성: {exe_path}")
            
            # ZIP 패키지 생성
            try:
                import zipfile
                zip_path = dist_dir / "ChatAIAgent-Windows.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(exe_path, exe_path.name)
                print(f"✓ ZIP 패키지 생성: {zip_path}")
            except Exception as e:
                print(f"⚠️ ZIP 생성 실패: {e}")
    
    elif system == "Linux":
        exe_path = dist_dir / "ChatAIAgent"
        if exe_path.exists():
            print(f"✓ Linux 실행 파일 생성: {exe_path}")
            
            # TAR.GZ 패키지 생성
            try:
                import tarfile
                tar_path = dist_dir / "ChatAIAgent-Linux.tar.gz"
                with tarfile.open(tar_path, 'w:gz') as tar:
                    tar.add(exe_path, exe_path.name)
                print(f"✓ TAR.GZ 패키지 생성: {tar_path}")
            except Exception as e:
                print(f"⚠️ TAR.GZ 생성 실패: {e}")


def main():
    """메인 빌드 프로세스"""
    print("🚀 안전한 ChatAI Agent 빌드 시작")
    print("=" * 50)

    try:
        # 1. 설정 파일 백업
        print("📦 설정 파일 백업 중...")
        backup_configs()

        # 2. 샘플 설정 파일 생성
        print("📝 빌드용 샘플 설정 파일 생성 중...")
        create_sample_configs()

        # 3. 빌드 디렉토리 정리
        print("🧹 빌드 디렉토리 정리 중...")
        clean_build()

        # 4. 실행 파일 빌드
        print("🔨 실행 파일 빌드 중...")
        if not build_executable():
            raise Exception("빌드 실패")

        # 5. 빌드 내용 확인
        print("🔍 빌드 내용 확인 중...")
        if not verify_build_contents():
            print("⚠️ 빌드에 문제가 있지만 계속 진행합니다.")
        
        # 6. 배포 패키지 생성
        print("📦 배포 패키지 생성 중...")
        create_distribution()

        print("=" * 50)
        print("✅ 빌드 완료!")

        # 빌드 결과 표시
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("\n📁 생성된 파일들:")
            for item in dist_dir.iterdir():
                size = ""
                if item.is_file():
                    size_mb = item.stat().st_size / (1024 * 1024)
                    size = f" ({size_mb:.1f}MB)"
                print(f"   - {item.name}{size}")

    except Exception as e:
        print(f"❌ 빌드 중 오류 발생: {e}")

    finally:
        # 6. 설정 파일 복원 (항상 실행)
        print("\n🔄 설정 파일 복원 중...")
        restore_configs()
        print("✅ 설정 파일 복원 완료")


if __name__ == "__main__":
    main()
