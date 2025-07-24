#!/usr/bin/env python
"""
MCP 서버 시작 스크립트
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def load_mcp_config(config_path):
    """MCP 설정 파일 로드"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 'servers' 키가 있는지 확인
            if 'mcpServers' not in config:
                logger.warning("MCP 설정 파일에 'servers' 키가 없습니다. 기본값 사용")
                config['mcpServers'] = {}
            return config
    except Exception as e:
        logger.error(f"MCP 설정 파일 로드 실패: {e}")
        return {"servers": {}}

def start_mcp_server(server_name, command, args, env=None):
    """MCP 서버 시작"""
    try:
        # 명령어가 존재하는지 확인
        if not command or not os.path.exists(command) and not any(os.path.exists(os.path.join(path, command)) for path in os.environ["PATH"].split(os.pathsep)):
            logger.warning(f"MCP 서버 {server_name} 시작 실패: 명령어 '{command}'를 찾을 수 없습니다")
            return None
        
        # 환경 변수 설정
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # 명령어 구성
        cmd = [command] + args
        
        # 서버 시작
        logger.info(f"MCP 서버 시작 중: {server_name} - 명령어: {' '.join(cmd)}")
        
        try:
            process = subprocess.Popen(
                cmd,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
        except FileNotFoundError:
            logger.error(f"MCP 서버 {server_name} 시작 실패: 명령어 '{command}'를 찾을 수 없습니다")
            return None
        
        # 서버 시작 확인 (최대 5초 대기)
        time.sleep(1)  # 지연 추가
        
        if process.poll() is not None:
            # 프로세스가 종료된 경우
            stdout, stderr = process.communicate()
            logger.error(f"MCP 서버 {server_name} 시작 실패: {stderr}")
            return None
        
        # 서버가 실행 중이면 성공
        logger.info(f"MCP 서버 {server_name} 시작됨 (PID: {process.pid})")
        return process
    
    except Exception as e:
        logger.error(f"MCP 서버 {server_name} 시작 중 오류 발생: {e}")
        return None

def main():
    """메인 함수"""
    # 프로젝트 루트 디렉토리 찾기
    project_root = Path(__file__).parent.absolute()
    
    # MCP 설정 파일 경로
    config_path = project_root / "mcp.json"
    
    # 설정 파일이 없으면 생성
    if not config_path.exists():
        logger.warning(f"MCP 설정 파일이 없습니다: {config_path}")
        default_config = {
            "mcpServers": {
                "mcp-atlassian": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-atlassian"],
                    "env": {}
                },
                "search-mcp-server": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-search"],
                    "env": {}
                }
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"기본 MCP 설정 파일 생성됨: {config_path}")
    
    # MCP 설정 로드
    config = load_mcp_config(config_path)
    
    # 활성화할 서버 목록 (명령줄 인수 또는 모든 서버)
    servers_to_activate = sys.argv[1:] if len(sys.argv) > 1 else list(config.get("mcpServers", {}).keys())
    
    logger.info(f"활성화할 MCP 서버: {servers_to_activate}")
    
    # 서버 시작
    processes = {}
    for server_name in servers_to_activate:
        if server_name in config.get("mcpServers", {}):
            server_config = config["mcpServers"][server_name]
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            if not command:
                logger.warning(f"MCP 서버 {server_name} 시작 실패: 명령어가 지정되지 않았습니다")
                continue
                
            process = start_mcp_server(server_name, command, args, env)
            if process:
                processes[server_name] = process
        else:
            logger.warning(f"알 수 없는 MCP 서버: {server_name}")
    
    logger.info(f"활성화된 MCP 서버: {list(processes.keys())}")
    
    try:
        # 모든 서버가 실행 중인 동안 대기
        while processes:
            for server_name, process in list(processes.items()):
                if process.poll() is not None:
                    # 서버가 종료된 경우
                    stdout, stderr = process.communicate()
                    logger.warning(f"MCP 서버 {server_name} 종료됨: {stderr}")
                    del processes[server_name]
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨, MCP 서버 종료 중...")
        for server_name, process in processes.items():
            try:
                process.terminate()
                logger.info(f"MCP 서버 {server_name} 종료 요청됨")
            except:
                pass

if __name__ == "__main__":
    main()