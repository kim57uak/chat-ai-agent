import json
import subprocess
import threading
import uuid
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class MCPClient:
    """MCP STDIO 클라이언트 - JSON-RPC over STDIO (개선된 버전)"""
    
    def __init__(self, command: str, args: List[str], env: Dict[str, str] = None):
        self.command = command
        self.args = args
        self.env = env or {}
        self.process = None
        self.initialized = False
        self.pending_requests = {}
        self.tools = []
        self._lock = threading.Lock()
        
    def start(self) -> bool:
        """MCP 서버 프로세스 시작"""
        try:
            import os
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            self.process = subprocess.Popen(
                [self.command] + self.args,
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
                        logger.debug(f"MCP 응답 수신: {response}")
                        
                        if "id" in response:
                            with self._lock:
                                self.pending_requests[response["id"]] = response
                    except json.JSONDecodeError:
                        logger.debug(f"Non-JSON output ignored: {line}")
                        
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
            logger.info("MCP 서버 초기화 완료")
            return True
            
        logger.error("MCP 서버 초기화 실패")
        return False
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회 - 표준 MCP 방식"""
        if not self.initialized:
            return []
            
        # 표준 MCP 방식: 빈 파라미터 객체로 호출
        request_id = self._send_request("tools/list", {})
        if not request_id:
            return []
            
        response = self._wait_for_response(request_id, timeout=10.0)
        
        if response and "result" in response:
            if "tools" in response["result"]:
                self.tools = response["result"]["tools"]
                logger.info(f"도구 {len(self.tools)}개 발견")
                return self.tools
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
        """MCP 클라이언트 종료"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            finally:
                self.process = None
                self.initialized = False


class MCPManager:
    """여러 MCP 서버 관리"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        
    def load_from_config(self, config_path: str) -> bool:
        """mcp.json에서 설정 로드 및 활성화된 서버만 시작"""
        try:
            # MCP 설정 파일 로드
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 서버 상태 파일 로드
            from .mcp_state import mcp_state
            
            servers = config.get("mcpServers", {})
            
            for name, server_config in servers.items():
                # 설정에서 비활성화된 서버 건너뛰기
                if server_config.get("disabled", False):
                    continue
                
                # 상태 파일에서 비활성화된 서버 건너뛰기
                if not mcp_state.is_server_enabled(name):
                    logger.info(f"MCP 서버 '{name}' 상태 파일에서 비활성화됨")
                    continue
                    
                command = server_config.get("command")
                args = server_config.get("args", [])
                env = server_config.get("env", {})
                
                if not command:
                    continue
                    
                client = MCPClient(command, args, env)
                if client.start() and client.initialize():
                    self.clients[name] = client
                    logger.info(f"MCP 서버 '{name}' 시작 완료")
                else:
                    logger.error(f"MCP 서버 '{name}' 시작 실패")
                    
            return len(self.clients) > 0
            
        except Exception as e:
            logger.error(f"MCP 설정 로드 실패: {e}")
            return False
    
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """모든 서버의 도구 목록 조회 (실시간)"""
        all_tools = {}
        
        # 딕셔너리 변경 오류 방지를 위해 복사본 사용
        clients_copy = dict(self.clients)
        
        for name, client in clients_copy.items():
            if client and client.initialized and client.process and client.process.poll() is None:
                try:
                    tools = client.list_tools()
                    if tools:
                        # 도구 목록도 복사본으로 저장
                        all_tools[name] = list(tools)
                        logger.info(f"서버 '{name}'에서 {len(tools)}개 도구 조회됨")
                    else:
                        logger.warning(f"서버 '{name}'에서 도구를 찾을 수 없음")
                except Exception as e:
                    logger.error(f"서버 '{name}' 도구 목록 조회 오류: {e}")
            else:
                logger.warning(f"서버 '{name}' 연결되지 않음 또는 초기화되지 않음")
        return all_tools
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """특정 서버의 도구 호출"""
        if server_name not in self.clients:
            logger.warning(f"MCP 서버 '{server_name}' 없음")
            return None
            
        client = self.clients[server_name]
        return client.call_tool(tool_name, arguments)
    
    def close_all(self):
        """모든 MCP 클라이언트 종료"""
        for client in self.clients.values():
            client.close()
        self.clients.clear()
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """모든 서버의 상태 정보 반환"""
        status = {}
        
        # 설정 파일에서 서버 정보 로드
        try:
            with open('mcp.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            servers = config.get("mcpServers", {})
        except Exception as e:
            logger.warning(f"mcp.json 로드 실패: {e}")
            servers = {}
        
        for name, server_config in servers.items():
            client = self.clients.get(name)
            
            # 실시간 도구 목록 조회
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
            with open('mcp.json', 'r', encoding='utf-8') as f:
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
                logger.info(f"MCP 서버 '{server_name}' 시작 완료")
                return True
            else:
                logger.error(f"MCP 서버 '{server_name}' 시작 실패")
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
                logger.info(f"MCP 서버 '{server_name}' 중지 완료")
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