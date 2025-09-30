#!/usr/bin/env python3
"""
Emergency config restoration script
Use this if build process fails and configs are not restored automatically
"""

import shutil
from pathlib import Path

def restore_configs():
    """Emergency restore of config files"""
    project_root = Path.cwd()
    backup_dir = project_root / "backup_configs"
    
    if not backup_dir.exists():
        print("❌ 백업 디렉토리를 찾을 수 없습니다.")
        print("   백업이 생성되지 않았거나 이미 복구되었을 수 있습니다.")
        return False
    
    config_files = ["config.json", "mcp.json", "news_config.json", "prompt_config.json"]
    restored_count = 0
    
    print("🔄 긴급 설정 파일 복구 시작...")
    
    for file in config_files:
        backup_file = backup_dir / file
        target_file = project_root / file
        
        if backup_file.exists():
            try:
                shutil.copy(backup_file, target_file)
                print(f"✓ {file} 복구 완료")
                restored_count += 1
            except Exception as e:
                print(f"❌ {file} 복구 실패: {e}")
        else:
            print(f"⚠️ {file} 백업을 찾을 수 없습니다")
    
    if restored_count > 0:
        try:
            shutil.rmtree(backup_dir)
            print(f"✓ 백업 디렉토리 정리 완료 ({restored_count}개 파일 복구됨)")
        except Exception as e:
            print(f"⚠️ 백업 디렉토리 정리 실패: {e}")
        
        print("✅ 설정 파일 복구 완료! 이제 정상적으로 테스트할 수 있습니다.")
        return True
    else:
        print("❌ 복구된 파일이 없습니다.")
        return False

if __name__ == "__main__":
    restore_configs()