#!/usr/bin/env python3
"""
패키징 환경 시뮬레이션 테스트 (크로스 플랫폼)
패키징된 앱에서 npx 실행이 되는지 테스트
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path

def simulate_packaged_environment():
    """패키징된 앱 환경 시뮬레이션 (크로스 플랫폼)"""
    print(f"🔧 패키징 환경 시뮬레이션 시작... ({platform.system()})")
    
    # 기존 환경변수 백업
    original_env = dict(os.environ)
    
    # OS별 최소 환경변수 설정
    if platform.system() == 'Windows':
        minimal_env = {
            'USERPROFILE': os.environ.get('USERPROFILE', ''),
            'USERNAME': os.environ.get('USERNAME', ''),
            'TEMP': os.environ.get('TEMP', 'C:\\temp'),
            'TMP': os.environ.get('TMP', 'C:\\temp'),
            'PATH': 'C:\\Windows\\System32;C:\\Windows',
            'PATHEXT': '.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC'
        }
    else:
        minimal_env = {
            'HOME': os.environ.get('HOME', ''),
            'USER': os.environ.get('USER', ''),
            'TMPDIR': os.environ.get('TMPDIR', '/tmp'),
            'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'
        }
    
    # 환경변수 초기화
    os.environ.clear()
    os.environ.update(minimal_env)
    
    print(f"📋 시뮬레이션된 PATH: {os.environ['PATH']}")
    return original_env

def restore_environment(original_env):
    """원본 환경 복구"""
    os.environ.clear()
    os.environ.update(original_env)
    print("✅ 원본 환경 복구 완료")

def test_command_execution(command, args=None, env_vars=None):
    """명령어 실행 테스트"""
    if args is None:
        args = []
    if env_vars is None:
        env_vars = {}
    
    # 환경변수 추가
    test_env = dict(os.environ)
    test_env.update(env_vars)
    
    try:
        print(f"🧪 테스트: {command} {' '.join(args)}")
        result = subprocess.run(
            [command] + args, 
            capture_output=True, 
            text=True, 
            timeout=10,
            env=test_env
        )
        
        if result.returncode == 0:
            print(f"✅ 성공: {command}")
            if result.stdout.strip():
                print(f"   출력: {result.stdout.strip()[:100]}...")
        else:
            print(f"❌ 실패: {command}")
            print(f"   오류: {result.stderr.strip()[:100]}...")
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print(f"❌ 명령어 없음: {command}")
        return False
    except subprocess.TimeoutExpired:
        print(f"⏰ 타임아웃: {command}")
        return False
    except Exception as e:
        print(f"❌ 예외: {command} - {e}")
        return False

def test_npm_environment():
    """npm 환경 테스트 (크로스 플랫폼)"""
    print("\n📦 npm 환경 테스트")
    
    # 1. 기본 명령어들 테스트
    commands = [
        ('node', ['--version']),
        ('npm', ['--version']),
        ('npx', ['--version']),
    ]
    
    results = {}
    for cmd, args in commands:
        results[cmd] = test_command_execution(cmd, args)
    
    # 2. OS별 절대경로 테스트
    print("\n🔍 절대경로 테스트")
    if platform.system() == 'Windows':
        absolute_commands = [
            ('C:\\Program Files\\nodejs\\node.exe', ['--version']),
            ('C:\\Program Files\\nodejs\\npm.cmd', ['--version']),
            ('C:\\Program Files\\nodejs\\npx.cmd', ['--version']),
        ]
    else:
        absolute_commands = [
            ('/opt/homebrew/bin/node', ['--version']),
            ('/opt/homebrew/bin/npm', ['--version']),
            ('/opt/homebrew/bin/npx', ['--version']),
        ]
    
    for cmd, args in absolute_commands:
        results[f"absolute_{cmd}"] = test_command_execution(cmd, args)
    
    return results

def test_with_env_loader():
    """환경변수 로더 적용 후 테스트"""
    print("\n🔄 환경변수 로더 적용 테스트")
    
    # env_loader 모듈 임포트 및 실행
    try:
        # 현재 디렉토리를 기준으로 상대경로 사용
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        from utils.env_loader import load_user_environment
        
        print("📥 환경변수 로딩...")
        load_user_environment()
        
        print(f"🔍 로딩 후 PATH: {os.environ.get('PATH', 'None')}")
        print(f"🔍 NODE_PATH: {os.environ.get('NODE_PATH', 'None')}")
        print(f"🔍 npm_config_prefix: {os.environ.get('npm_config_prefix', 'None')}")
        
        # Windows 전용 환경변수도 확인
        if platform.system() == 'Windows':
            print(f"🔍 npm_config_cache: {os.environ.get('npm_config_cache', 'None')}")
        
        # 다시 테스트
        return test_npm_environment()
        
    except Exception as e:
        print(f"❌ 환경변수 로더 오류: {e}")
        import traceback
        traceback.print_exc()
        return {}

def test_mcp_server():
    """실제 MCP 서버 실행 테스트 (크로스 플랫폼)"""
    print("\n🚀 MCP 서버 실행 테스트")
    
    # OS별 테스트 케이스 설정
    if platform.system() == 'Windows':
        test_cases = [
            {
                'name': 'npx (상대경로)',
                'command': 'npx',
                'args': ['mysql-mcp-server', '--help'],
            },
            {
                'name': 'npx (절대경로)',
                'command': 'C:\\Program Files\\nodejs\\npx.cmd',
                'args': ['mysql-mcp-server', '--help'],
            },
            {
                'name': 'node 직접 실행',
                'command': 'C:\\Program Files\\nodejs\\node.exe',
                'args': ['C:\\Program Files\\nodejs\\node_modules\\mysql-mcp-server\\bin\\mysql-mcp-server', '--help'],
            }
        ]
    else:
        test_cases = [
            {
                'name': 'npx (상대경로)',
                'command': 'npx',
                'args': ['mysql-mcp-server', '--help'],
            },
            {
                'name': 'npx (절대경로)',
                'command': '/opt/homebrew/bin/npx',
                'args': ['mysql-mcp-server', '--help'],
            },
            {
                'name': 'node 직접 실행',
                'command': '/opt/homebrew/bin/node',
                'args': ['/opt/homebrew/lib/node_modules/mysql-mcp-server/bin/mysql-mcp-server', '--help'],
            }
        ]
    
    results = {}
    for case in test_cases:
        print(f"\n📋 {case['name']} 테스트")
        results[case['name']] = test_command_execution(
            case['command'], 
            case['args'],
            {
                'MYSQL_HOST': 'localhost',
                'MYSQL_PORT': '3306',
                'MYSQL_USER': 'root',
                'MYSQL_PASSWORD': 'root',
                'MYSQL_DATABASE': 'spring_security'
            }
        )
    
    return results

def main():
    """메인 테스트 함수"""
    print("🧪 패키징 환경 npx 실행 테스트")
    print("=" * 50)
    
    # 원본 환경 백업
    original_env = simulate_packaged_environment()
    
    try:
        # 1. 패키징 환경에서 기본 테스트
        print("\n1️⃣ 패키징 환경 시뮬레이션 테스트")
        basic_results = test_npm_environment()
        
        # 2. 환경변수 로더 적용 후 테스트
        print("\n2️⃣ 환경변수 로더 적용 후 테스트")
        enhanced_results = test_with_env_loader()
        
        # 3. 실제 MCP 서버 실행 테스트
        print("\n3️⃣ MCP 서버 실행 테스트")
        mcp_results = test_mcp_server()
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("📊 테스트 결과 요약")
        print("=" * 50)
        
        print("\n🔸 기본 환경:")
        for cmd, success in basic_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {cmd}")
        
        print("\n🔸 환경변수 로더 적용:")
        for cmd, success in enhanced_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {cmd}")
        
        print("\n🔸 MCP 서버 실행:")
        for name, success in mcp_results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {name}")
        
        # 권장사항
        print("\n💡 권장사항:")
        if any(enhanced_results.values()):
            print("  ✅ 환경변수 로더가 효과적입니다!")
        else:
            print("  ⚠️  환경변수 로더 개선이 필요합니다.")
        
        if mcp_results.get('npx (상대경로)', False):
            print("  ✅ npx 상대경로 사용 가능!")
        elif mcp_results.get('npx (절대경로)', False):
            print("  ⚠️  npx 절대경로만 사용 가능")
        else:
            print("  ❌ npx 사용 불가, node 직접 실행 필요")
    
    finally:
        # 환경 복구
        restore_environment(original_env)

if __name__ == "__main__":
    main()