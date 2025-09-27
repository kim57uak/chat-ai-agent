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


def backup_configs():
    """기존 설정 파일들 백업"""
    files = ["config.json", "mcp.json", "news_config.json", "prompt_config.json"]
    for file in files:
        if os.path.exists(file):
            shutil.copy(file, f"{file}.backup")
            print(f"✓ {file} 백업 완료")


def restore_configs():
    """백업된 설정 파일들 복원"""
    files = ["config.json", "mcp.json", "news_config.json", "prompt_config.json"]
    for file in files:
        backup_file = f"{file}.backup"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, file)
            os.remove(backup_file)
            print(f"✓ {file} 복원 완료")


def create_empty_configs():
    """빌드용 빈 설정 파일들 생성"""

    # 빈 config.json
    config = {
        "models": {},
        "conversation_settings": {"enable_history": True},
        "response_settings": {"max_tokens": 4096},
    }

    # 빈 mcp.json
    mcp = {"mcpServers": {}}

    # 빈 news_config.json
    news = {"news_sources": {"domestic": [], "international": [], "earthquake": []}}

    # 빈 prompt_config.json
    prompt = {"openai": {}, "google": {}, "common": {}}

    # 파일 생성
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)

    with open("mcp.json", "w") as f:
        json.dump(mcp, f, indent=2)

    with open("news_config.json", "w") as f:
        json.dump(news, f, indent=2)

    with open("prompt_config.json", "w") as f:
        json.dump(prompt, f, indent=2)

    print("✓ 빈 설정 파일들 생성 완료")


def clean_build():
    """빌드 디렉토리 정리"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ {dir_name} 디렉토리 정리 완료")


def build_executable():
    """실행 파일 빌드"""
    system = platform.system()
    print(f"🔨 {system}용 빌드 시작...")

    try:
        cmd = ["pyinstaller", "--clean", "--noconfirm", "chat_ai_agent.spec"]

        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ PyInstaller 빌드 완료")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        print(f"stderr: {e.stderr}")
        return False


def create_distribution():
    """배포용 패키지 생성"""
    system = platform.system()
    dist_dir = Path("dist")

    if system == "Darwin":  # macOS
        app_path = dist_dir / "ChatAIAgent.app"
        if app_path.exists():
            print(f"✓ macOS 앱 번들 생성: {app_path}")

            try:
                subprocess.run(
                    [
                        "hdiutil",
                        "create",
                        "-volname",
                        "ChatAIAgent",
                        "-srcfolder",
                        str(app_path),
                        "-ov",
                        "-format",
                        "UDZO",
                        str(dist_dir / "ChatAIAgent-macOS.dmg"),
                    ],
                    check=True,
                )
                print("✓ DMG 파일 생성 완료")
            except:
                print("⚠️ DMG 생성 실패 (선택사항)")

    elif system == "Windows":
        exe_path = dist_dir / "ChatAIAgent.exe"
        if exe_path.exists():
            print(f"✓ Windows 실행 파일 생성: {exe_path}")


def main():
    """메인 빌드 프로세스"""
    print("🚀 안전한 ChatAI Agent 빌드 시작")
    print("=" * 50)

    try:
        # 1. 설정 파일 백업
        print("📦 설정 파일 백업 중...")
        backup_configs()

        # 2. 빈 설정 파일 생성
        print("📝 빌드용 빈 설정 파일 생성 중...")
        create_empty_configs()

        # 3. 빌드 디렉토리 정리
        print("🧹 빌드 디렉토리 정리 중...")
        clean_build()

        # 4. 실행 파일 빌드
        print("🔨 실행 파일 빌드 중...")
        if not build_executable():
            raise Exception("빌드 실패")

        # 5. 배포 패키지 생성
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
