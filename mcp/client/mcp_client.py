import json
import subprocess
import threading
import uuid
from typing import Dict, Any, Optional, List
from utils.config_path import config_path_manager
from core.logging import get_logger

logger = get_logger("mcp_client")

class MCPClient:
    """MCP STDIO 클라이언트 - JSON-RPC over STDIO (개선된 버전)"""
    
    def __init__(self, command: str, args: List[str], env: Dict[str, str] = None):
        self.command = command
        self.args = args
        self.env = env or {}
        self.process = None
        self.initialized = False
        self.pending_requests = {}
        self._lock = threading.Lock()
        
    def start(self) -> bool:
        """MCP 서버 프로세스 시작"""
        try:
            import os
            
            # 환경변수 로더 사용하여 Node.js 환경 설정
            try:
                from utils.env_loader import load_user_environment
                load_user_environment()
            except Exception as e:
                logger.debug(f"환경변수 로더 실행 실패: {e}")
            
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            # Python 명령어 특별 처리: 가상환경 자동 감지
            command = self.command
            if self.command in ['python', 'python3'] and self.args:
                from pathlib import Path
                script_path = Path(self.args[0])
                if script_path.exists():
                    project_dir = script_path.parent
                    venv_python = project_dir / 'venv' / 'bin' / 'python'
                    
                    if venv_python.exists():
                        command = str(venv_python)
                        logger.info(f"가상환경 Python 감지: {command}")
                    else:
                        logger.debug(f"가상환경 없음, 시스템 Python 사용: {command}")
                
                # PYTHONPATH 설정
                if 'PYTHONPATH' in self.env:
                    pythonpath = self.env['PYTHONPATH']
                    if 'PYTHONPATH' in full_env:
                        full_env['PYTHONPATH'] = f"{pythonpath}:{full_env['PYTHONPATH']}"
                    else:
                        full_env['PYTHONPATH'] = pythonpath
                
                full_env['PYTHONIOENCODING'] = 'utf-8'
                full_env['PYTHONUNBUFFERED'] = '1'
            
            logger.info(f"MCP 서버 실행: {command} {' '.join(self.args)}")
            
            self.process = subprocess.Popen(
                [command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=full_env,
                bufsize=0
            )
            
            # 응답 처리 스레드 시작
            self.response_thread = threading.Thread(target=self._handle_responses, daemon=True)
            self.response_thread.start()
            
            # stderr 로깅 스레드 시작
            self.stderr_thread = threading.Thread(target=self._handle_stderr, daemon=True)
            self.stderr_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"MCP 서버 시작 실패: {e}")
            return False
    
    def _send_request(self, method: str, params: Dict[str, Any] = None) -> str:
        """JSON-RPC 요청 전송"""
        if not self.process or self.process.poll() is not None:
            logger.error("MCP 서버 프로세스가 종료됨")
            return None
            
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params is not None:
            request["params"] = params
            
        try:
            request_json = json.dumps(request) + '\n'
            if not self.process.stdin or self.process.stdin.closed:
                logger.error("MCP stdin 연결이 닫혀있음")
                return None
                
            self.process.stdin.write(request_json)
            self.process.stdin.flush()
            logger.debug(f"MCP 요청 전송: {method}")
            return request_id
        except Exception as e:
            logger.error(f"MCP 요청 전송 실패: {e}")
            return None
    
    def _send_notification(self, method: str, params: Dict[str, Any] = None):
        """JSON-RPC 알림 전송 (응답 없음)"""
        if not self.process or self.process.poll() is not None:
            logger.error("MCP 서버 프로세스가 종료됨")
            return
            
        notification = {
            "jsonrpc": "2.0",
            "method": method
        }
        if params is not None:
            notification["params"] = params
            
        try:
            notification_json = json.dumps(notification) + '\n'
            if not self.process.stdin or self.process.stdin.closed:
                logger.error("MCP stdin 연결이 닫혀있음")
                return
                
            self.process.stdin.write(notification_json)
            self.process.stdin.flush()
            logger.debug(f"MCP 알림 전송: {method}")
        except Exception as e:
            logger.error(f"MCP 알림 전송 실패: {e}")
    
    def _handle_stderr(self):
        """에러 출력 로깅"""
        try:
            for line in self.process.stderr:
                line = line.strip()
                if line:
                    logger.warning(f"MCP stderr: {line}")
        except:
            pass
    
    def _handle_responses(self):
        """응답 처리 스레드"""
        buffer = ""
        while self.process and self.process.poll() is None:
            try:
                chunk = self.process.stdout.read(1)
                if not chunk:
                    break
                    
                buffer += chunk
                
                # 완전한 JSON 메시지 찾기
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                        
                    try:
                        response = json.loads(line)
                        # 응답 요약만 로그
                        if 'result' in response and 'tools' in response.get('result', {}):
                            tool_count = len(response['result']['tools'])
                            logger.debug(f"MCP 도구 목록: {tool_count}개")
                        
                        if "id" in response:
                            with self._lock:
                                self.pending_requests[response["id"]] = response
                    except json.JSONDecodeError:
                        pass  # Non-JSON 출력 무시
                        
            except Exception as e:
                logger.error(f"MCP 응답 처리 오류: {e}")
                break
    
    def _wait_for_response(self, request_id: str, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """응답 대기"""
        import time
        start_time = time.time()
        check_interval = 0.2
        
        while time.time() - start_time < timeout:
            if self.process and self.process.poll() is not None:
                logger.error(f"MCP 서버 프로세스 종료 감지: {request_id}")
                return None
                
            with self._lock:
                if request_id in self.pending_requests:
                    response = self.pending_requests.pop(request_id)
                    return response
            
            time.sleep(check_interval)
            
        logger.warning(f"MCP 응답 타임아웃: {request_id} ({timeout}초)")
        return None
    
    def initialize(self) -> bool:
        """MCP 서버 초기화"""
        if not self.process:
            return False
            
        request_id = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            },
            "clientInfo": {
                "name": "chat-ai-agent",
                "version": "1.0.0"
            }
        })
        
        if not request_id:
            return False
            
        response = self._wait_for_response(request_id)
        if response and "result" in response:
            # MCP 표준에 따라 initialized 알림 전송
            self._send_notification("notifications/initialized")
            self.initialized = True
            # logger.info("MCP 서버 초기화 완료")  # 주석 처리
            return True
            
        # logger.error("MCP 서버 초기화 실패")  # 주석 처리
        return False
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회 - 표준 MCP 방식 (항상 실시간 조회)"""
        if not self.initialized:
            return []
            
        # 표준 MCP 방식: 빈 파라미터 객체로 호출
        request_id = self._send_request("tools/list", {})
        if not request_id:
            return []
            
        response = self._wait_for_response(request_id, timeout=10.0)
        
        if response and "result" in response:
            if "tools" in response["result"]:
                return response["result"]["tools"]
            else:
                logger.info("서버가 도구를 제공하지 않음")
                return []
        elif response and "error" in response:
            logger.warning(f"도구 목록 조회 오류: {response['error']}")
        else:
            logger.warning("도구 목록 조회 응답 없음")
            
        return []
    

    
    def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """도구 호출"""
        if not self.initialized:
            logger.warning(f"도구 '{name}' 호출 실패: 초기화되지 않음")
            return None
            
        params = {"name": name}
        if arguments is not None:
            # arguments가 딕셔너리가 아닌 경우 (예: 리스트) 그대로 전달
            if isinstance(arguments, dict):
                params["arguments"] = arguments
            else:
                # 리스트나 다른 타입의 경우, 빈 딕셔너리로 감싸지 않고 그대로 전달
                params["arguments"] = arguments
        else:
            params["arguments"] = {}
            
        try:
            logger.debug(f"도구 '{name}' 호출 파라미터: {params}")
            request_id = self._send_request("tools/call", params)
            if not request_id:
                return None
                
            response = self._wait_for_response(request_id, timeout=180.0)
            if response and "result" in response:
                return response["result"]
                
            if response and "error" in response:
                logger.error(f"도구 '{name}' 호출 오류: {response['error']}")
                return None
                
            return None
            
        except Exception as e:
            logger.error(f"도구 '{name}' 호출 예외: {e}")
            return None
    
    def close(self):
        """MCP 클라이언트 종료 - 메모리 누수 방지"""
        if self.process:
            try:
                # 응답 스레드 종료 대기
                if hasattr(self, 'response_thread') and self.response_thread.is_alive():
                    self.response_thread.join(timeout=1.0)
                
                # stdin 먼저 닫기
                if self.process.stdin and not self.process.stdin.closed:
                    try:
                        self.process.stdin.close()
                    except:
                        pass
                
                # 프로세스 종료
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=1)
            except Exception as e:
                logger.debug(f"프로세스 종료 중 오류: {e}")
                try:
                    self.process.kill()
                    self.process.wait(timeout=1)
                except:
                    pass
            finally:
                # 파이프 정리
                try:
                    if self.process.stdout:
                        self.process.stdout.close()
                    if self.process.stderr:
                        self.process.stderr.close()
                except:
                    pass
                
                # 대기 중인 요청 정리
                with self._lock:
                    self.pending_requests.clear()
                
                self.process = None
                self.initialized = False


class MCPManager:
    """여러 MCP 서버 관리"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        
    def load_from_config(self, config_path: str) -> bool:
        """mcp.json에서 설정 로드 및 활성화된 서버만 시작"""
        try:
            # MCP 설정 파일 경로 해결
            resolved_path = config_path_manager.get_config_path(config_path)
            logger.info(f"MCP 설정 파일 경로: {resolved_path}")
            
            # MCP 설정 파일 로드
            with open(resolved_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 서버 상태 파일 로드
            from .mcp_state import mcp_state
            
            servers = config.get("mcpServers", {})
            
            for name, server_config in servers.items():
                # 설정에서 비활성화된 서버 건너뛰기
                if server_config.get("disabled", False):
                    continue
                
                command = server_config.get("command")
                args = server_config.get("args", [])
                env = server_config.get("env", {})
                
                if not command:
                    continue
                    
                client = MCPClient(command, args, env)
                
                # 상태 파일에서 활성화된 서버만 실제 시작
                if mcp_state.is_server_enabled(name):
                    if client.start() and client.initialize():
                        self.clients[name] = client
                        # logger.info(f"MCP 서버 '{name}' 시작 완료")  # 주석 처리
                    else:
                        # logger.error(f"MCP 서버 '{name}' 시작 실패")  # 주석 처리
                        self.clients[name] = client  # 실패해도 등록
                else:
                    # 비활성화된 서버도 등록 (시작하지 않음)
                    self.clients[name] = client
                    # logger.info(f"MCP 서버 '{name}' 등록됨 (비활성화 상태)")  # 주석 처리
                    
            return len(self.clients) > 0
            
        except Exception as e:
            logger.error(f"MCP 설정 로드 실패: {e}")
            return False
    
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 서버의 도구 목록 조회 (항상 실시간)"""
        all_tools = {}
        
        # 딕셔너리 변경 오류 방지를 위해 복사본 사용
        clients_copy = dict(self.clients)
        
        for name, client in clients_copy.items():
            if client and client.initialized and client.process and client.process.poll() is None:
                try:
                    tools = client.list_tools()
                    if tools:
                        all_tools[name] = tools
                except Exception as e:
                    logger.error(f"서버 '{name}' 도구 목록 조회 오류: {e}")
        
        return all_tools
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """특정 서버의 도구 호출"""
        if server_name not in self.clients:
            logger.warning(f"MCP 서버 '{server_name}' 없음")
            return None
            
        client = self.clients[server_name]
        return client.call_tool(tool_name, arguments)
    
    def close_all(self):
        """모든 MCP 클라이언트 종료 - 세마포어 누수 방지"""
        import time
        import gc
        
        # 복사본으로 작업하여 딕셔너리 변경 오류 방지
        clients_to_close = list(self.clients.values())
        
        for client in clients_to_close:
            try:
                client.close()
            except Exception as e:
                logger.error(f"클라이언트 종료 오류: {e}")
        
        self.clients.clear()
        
        # 프로세스 완전 종료 대기
        time.sleep(0.3)
        
        # 가비지 컬렉션으로 리소스 정리
        gc.collect()
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """모든 서버의 상태 정보 반환 - 실시간 도구 목록 조회"""
        status = {}
        
        # 설정 파일에서 서버 정보 로드
        try:
            mcp_config_path = config_path_manager.get_config_path('mcp.json')
            with open(mcp_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            servers = config.get("mcpServers", {})
        except Exception as e:
            logger.warning(f"mcp.json 로드 실패: {e}")
            servers = {}
        
        # 딕셔너리 변경 오류 방지를 위해 복사본 사용
        clients_copy = dict(self.clients)
        
        for name, server_config in servers.items():
            client = clients_copy.get(name)
            
            # 실시간 도구 목록 조회 - 강제 새로고침
            tools = []
            server_type = "unknown"
            
            if client and client.initialized and client.process and client.process.poll() is None:
                try:
                    tools = client.list_tools()
                    if tools:
                        server_type = "tools_provider"
                    else:
                        server_type = "no_tools"
                except Exception as e:
                    logger.warning(f"서버 '{name}' 도구 목록 조회 실패: {e}")
                    server_type = "error"
            
            status[name] = {
                'command': server_config.get('command', ''),
                'args': server_config.get('args', []),
                'env': server_config.get('env', {}),
                'status': 'running' if client and client.process and client.process.poll() is None else 'stopped',
                'tools': tools,
                'server_type': server_type
            }
        
        return status
    
    def start_server(self, server_name: str) -> bool:
        """특정 서버 시작"""
        if server_name in self.clients:
            client = self.clients[server_name]
            if client.process and client.process.poll() is None:
                return True
        
        try:
            mcp_config_path = config_path_manager.get_config_path('mcp.json')
            with open(mcp_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            servers = config.get("mcpServers", {})
            
            if server_name not in servers:
                return False
            
            server_config = servers[server_name]
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", {})
            
            if not command:
                return False
            
            client = MCPClient(command, args, env)
            if client.start() and client.initialize():
                self.clients[server_name] = client
                # logger.info(f"MCP 서버 '{server_name}' 시작 완료")  # 주석 처리
                return True
            else:
                # logger.error(f"MCP 서버 '{server_name}' 시작 실패")  # 주석 처리
                return False
                
        except Exception as e:
            logger.error(f"MCP 서버 '{server_name}' 시작 오류: {e}")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """특정 서버 중지"""
        if server_name in self.clients:
            try:
                self.clients[server_name].close()
                del self.clients[server_name]
                # logger.info(f"MCP 서버 '{server_name}' 중지 완료")  # 주석 처리
                return True
            except Exception as e:
                logger.error(f"MCP 서버 '{server_name}' 중지 오류: {e}")
                return False
        return True
    
    def restart_server(self, server_name: str) -> bool:
        """특정 서버 재시작"""
        self.stop_server(server_name)
        return self.start_server(server_name)


# 전역 MCP 매니저 인스턴스
mcp_manager = MCPManager()