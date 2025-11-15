from typing import List, Dict, Any, Optional, Tuple
from core.models.model_strategy_factory import ModelStrategyFactory
from core.chat.simple_chat_processor import SimpleChatProcessor
from core.chat.tool_chat_processor import ToolChatProcessor
from core.chat.chat_mode_manager import ChatModeManager, ChatMode
from core.conversation_history import ConversationHistory
from core.token_tracker import token_tracker
from tools.langchain.langchain_tools import MCPTool, MCPToolRegistry
from mcp.servers.mcp import get_all_mcp_tools
from mcp.tools.tool_manager import tool_manager
from core.logging import get_logger

_logger = get_logger("ai_agent_v2")


class AIAgentV2:
    """리팩토링된 AI 에이전트 - SOLID 원칙 적용"""
    
    logger = _logger
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        
        # 전략 패턴으로 모델별 처리 분리
        self.model_strategy = ModelStrategyFactory.create_strategy(api_key, model_name)
        
        # 채팅 모드 관리자
        self.mode_manager = ChatModeManager(self.model_strategy)
        
        # 채팅 처리기들 (하위 호환성)
        self.simple_processor = SimpleChatProcessor(self.model_strategy)
        self.tool_processor = None  # 지연 로딩
        self.rag_processor = None  # 지연 로딩
        
        # 도구 및 대화 히스토리
        self.tools: List[MCPTool] = []
        self.conversation_history = ConversationHistory()
        
        # RAG 관련
        self.vectorstore = None
        self.mcp_client = None
        
        # 세션 ID (토큰 추적용)
        self.session_id = None
        
        # 초기화
        self._load_mcp_tools()
        self.conversation_history.load_from_file()
    
    def _load_mcp_tools(self):
        """MCP 도구 로드"""
        try:
            from core.mcp_implementation import mcp_tool_caller
            tool_registry = MCPToolRegistry(mcp_tool_caller)
            
            all_mcp_tools = get_all_mcp_tools()
            if all_mcp_tools:
                self.tools = tool_registry.register_mcp_tools(all_mcp_tools)
                tool_manager.register_tools(all_mcp_tools)
                self.logger.info(f"AI 에이전트에 {len(self.tools)}개 도구 로드됨")
            else:
                self.logger.warning("사용 가능한 MCP 도구가 없습니다")
                
        except Exception as e:
            self.logger.error(f"MCP 도구 로드 실패: {e}")
            self.tools = []
    
    def process_message(self, user_input: str) -> Tuple[str, List]:
        """메시지 처리 - 도구 사용 여부 자동 결정"""
        # 대화 토큰 트래킹 시작
        conversation_id = token_tracker.start_conversation(user_input, self.model_name)
        
        # 사용자 메시지를 히스토리에 추가
        self.conversation_history.add_message("user", user_input)
        
        try:
            # 도구 사용 여부 결정
            should_use_tools = self._should_use_tools(user_input)
            
            if should_use_tools and self.tools:
                response, used_tools = self._process_with_tools(user_input)
            else:
                response, used_tools = self._process_simple(user_input)
            
            # 응답을 히스토리에 추가
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            
            # 대화 토큰 트래킹 종료
            token_tracker.end_conversation(response)
            
            return response, used_tools
            
        except Exception as e:
            self.logger.error(f"메시지 처리 오류: {e}")
            error_response = f"메시지 처리 중 오류가 발생했습니다: {str(e)[:100]}..."
            
            # 오류 시에도 대화 토큰 트래킹 종료
            token_tracker.end_conversation(error_response)
            
            return error_response, []
    
    def process_message_with_history(
        self, 
        user_input: str, 
        conversation_history: List[Dict], 
        force_agent: bool = False
    ) -> Tuple[str, List]:
        """대화 기록을 포함한 메시지 처리"""
        try:
            # RAG 모드이거나 force_agent=True이고 도구가 있으면 Agent 모드
            if force_agent and (self.tools or self.mode_manager.current_mode == ChatMode.RAG):
                self.logger.info(f"Agent 모드 처리: force_agent={force_agent}, tools={len(self.tools)}, mode={self.mode_manager.current_mode}")
                return self._process_with_tools(user_input, conversation_history)
            else:
                self.logger.info(f"Simple 모드 처리: force_agent={force_agent}, tools={len(self.tools)}, mode={self.mode_manager.current_mode}")
                return self._process_simple(user_input, conversation_history)
                
        except Exception as e:
            self.logger.error(f"히스토리 포함 메시지 처리 오류: {e}")
            return f"메시지 처리 중 오류가 발생했습니다: {str(e)[:100]}...", []
    
    def simple_chat(self, user_input: str) -> str:
        """단순 채팅 (도구 사용 없음)"""
        response, _ = self.simple_processor.process_message(user_input)
        return response
    
    def simple_chat_with_history(self, user_input: str, conversation_history: List[Dict]) -> str:
        """대화 기록을 포함한 단순 채팅"""
        self.simple_processor.session_id = self.session_id
        response, _ = self.simple_processor.process_message(user_input, conversation_history)
        return response
    
    def set_chat_mode(self, mode: str):
        """채팅 모드 설정"""
        try:
            chat_mode = ChatMode(mode)
            self.mode_manager.set_mode(chat_mode)
            self.logger.info(f"채팅 모드 변경: {mode}")
        except ValueError:
            self.logger.error(f"잘못된 채팅 모드: {mode}")
    
    def set_vectorstore(self, vectorstore):
        """벡터 스토어 설정 (RAG용)"""
        self.vectorstore = vectorstore
        self.logger.info("벡터 스토어 설정됨")
    
    def set_mcp_client(self, mcp_client):
        """MCP 클라이언트 설정 (RAG용)"""
        self.mcp_client = mcp_client
        self.logger.info("MCP 클라이언트 설정됨")
    
    def _should_use_tools(self, user_input: str) -> bool:
        """도구 사용 여부 결정"""
        # RAG 모드면 항상 RAG 프로세서 사용
        if self.mode_manager.current_mode == ChatMode.RAG:
            return True
        
        if not self.tools:
            self.logger.info(f"도구가 없어서 도구 사용 안함: {len(self.tools)}개")
            return False
        
        # 도구 정보를 전략에 전달
        if hasattr(self.model_strategy, 'set_tools'):
            self.model_strategy.set_tools(self.tools)
        else:
            self.model_strategy.tools = self.tools
        
        # 모델별 전략에 위임
        result = self.model_strategy.should_use_tools(user_input)
        self.logger.info(f"도구 사용 판단: '{user_input}' -> {result} (도구 {len(self.tools)}개 사용 가능)")
        return result
    
    def _process_with_tools(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """도구를 사용한 처리 - LLM 기반 Multi-Agent 선택"""
        # 대화 히스토리가 없으면 내부 히스토리에서 5단계 가져오기
        if not conversation_history:
            conversation_history = self.conversation_history.get_context_messages()
        
        # RAG 모드: RAG Agent 기본 실행 + 필요시 추가 Agent 선택
        if self.mode_manager.current_mode == ChatMode.RAG:
            self.logger.info("RAG 모드: RAG Agent 기본 실행")
            
            # 1. RAG Agent 먼저 실행
            if self.vectorstore:
                rag_processor = self.mode_manager.get_processor(
                    mode=ChatMode.RAG,
                    vectorstore=self.vectorstore,
                    mcp_client=self.mcp_client,
                    tools=self.tools,
                    session_id=self.session_id
                )
                rag_response, rag_tools = rag_processor.process_message(user_input, conversation_history)
                
                # 2. RAG 응답이 충분한지 LLM이 판단
                needs_additional_agent = self._check_if_additional_agent_needed(user_input, rag_response)
                
                if not needs_additional_agent:
                    self.logger.info("RAG Agent 응답으로 충분함")
                    return rag_response, rag_tools
                
                # 3. 추가 Agent 필요시 선택 및 실행
                self.logger.info("추가 Agent 필요: LLM 기반 Agent 선택")
                available_agents = self._load_additional_agents()  # RAG 제외
                
                if available_agents:
                    selected_agent = self._select_agent_with_llm(user_input, available_agents)
                    if selected_agent:
                        self.logger.info(f"추가 선택된 Agent: {selected_agent['name']}")
                        additional_response, additional_tools = self._execute_selected_agent(selected_agent, user_input, conversation_history)
                        
                        # RAG + 추가 Agent 응답 결합
                        combined_response = f"{rag_response}\n\n---\n\n{additional_response}"
                        combined_tools = rag_tools + additional_tools
                        return combined_response, combined_tools
                
                # 추가 Agent 실패시 RAG 응답만 반환
                return rag_response, rag_tools
            
            # vectorstore 없으면 기본 처리
            self.logger.warning("RAG 모드이지만 vectorstore가 없음")
            if not self.tool_processor:
                self.tool_processor = ToolChatProcessor(self.model_strategy, self.tools)
                self.tool_processor.session_id = self.session_id
            return self.tool_processor.process_message(user_input, conversation_history)
        
        # TOOL 모드 (기존 로직)
        if not self.tool_processor:
            self.tool_processor = ToolChatProcessor(self.model_strategy, self.tools)
            self.tool_processor.session_id = self.session_id
        
        return self.tool_processor.process_message(user_input, conversation_history)
    
    def _process_simple(self, user_input: str, conversation_history: List[Dict] = None) -> Tuple[str, List]:
        """단순 처리 - 5단계 대화 히스토리 포함"""
        # 대화 히스토리가 없으면 내부 히스토리에서 5단계 가져오기
        if not conversation_history:
            conversation_history = self.conversation_history.get_context_messages()
        
        # 단순 채팅에서도 토큰 트래킹 시작 (현재 대화가 없는 경우)
        if not token_tracker.current_conversation:
            token_tracker.start_conversation(user_input, self.model_name)
        
        # session_id 설정
        self.simple_processor.session_id = self.session_id
        
        response, used_tools = self.simple_processor.process_message(user_input, conversation_history)
        return response, used_tools
    
    def get_available_tools(self) -> List[str]:
        """사용 가능한 도구 목록 반환"""
        return [tool.name for tool in self.tools]
    
    def _check_if_additional_agent_needed(self, user_input: str, rag_response: str) -> bool:
        """추가 Agent가 필요한지 LLM이 판단"""
        prompt = f"""Does the user's question require additional tools beyond document search?

User Question: {user_input}
RAG Response: {rag_response[:500]}...

Select YES if user needs:
- External web search or real-time information
- File operations (create, modify, delete)
- Calculations or code execution
- Database queries
- Other external tools

Select NO if:
- RAG response fully answers the question
- Only document-based information needed
- Question is completely satisfied

Answer only 'YES' or 'NO'."""
        
        try:
            from langchain.schema import HumanMessage
            response = self.model_strategy.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper() if hasattr(response, 'content') else str(response).strip().upper()
            result = "YES" in decision
            self.logger.info(f"Additional agent needed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Additional agent check failed: {e}")
            return False
    
    def _load_additional_agents(self) -> List[Dict[str, Any]]:
        """추가 Agent들 로드 (RAG Agent 제외)"""
        agents = []
        
        try:
            # MCP Agent
            if self.tools:
                from core.agents.mcp_agent import MCPAgent
                agents.append({
                    "name": "MCPAgent", 
                    "description": "External tool usage. Use for: web search, API calls, file operations, system commands, real-time data retrieval.",
                    "class": MCPAgent,
                    "init_params": {"llm": self.model_strategy.llm, "tools": self.tools}
                })
            
            # 추가 Agent들을 동적으로 로드 (RAG, SQL Agent 제외)
            try:
                import importlib
                import pkgutil
                from core.agents import base_agent
                
                # 비활성화할 Agent 목록
                disabled_agents = ['core.agents.sql_agent', 'core.agents.rag_agent']
                
                # core.agents 모듈에서 모든 Agent 클래스 찾기
                agents_module = importlib.import_module('core.agents')
                for importer, modname, ispkg in pkgutil.iter_modules(agents_module.__path__, agents_module.__name__ + "."):
                    if (modname.endswith('_agent') and 
                        modname not in ['core.agents.base_agent', 'core.agents.mcp_agent'] and
                        modname not in disabled_agents):
                        try:
                            module = importlib.import_module(modname)
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (isinstance(attr, type) and 
                                    issubclass(attr, base_agent.BaseAgent) and 
                                    attr != base_agent.BaseAgent and
                                    hasattr(attr, '__doc__') and attr.__doc__):
                                    
                                    agents.append({
                                        "name": attr.__name__,
                                        "description": attr.__doc__.strip(),
                                        "class": attr,
                                        "init_params": {"llm": self.model_strategy.llm}
                                    })
                        except Exception as e:
                            self.logger.debug(f"Agent 로드 실패: {modname} - {e}")
            
            except Exception as e:
                self.logger.debug(f"동적 Agent 로드 실패: {e}")
            
            self.logger.info(f"로드된 추가 Agent: {len(agents)}개 - {[a['name'] for a in agents]}")
            return agents
            
        except Exception as e:
            self.logger.error(f"추가 Agent 로드 오류: {e}")
            return []
    
    def _load_all_agents(self) -> List[Dict[str, Any]]:
        """사용 가능한 모든 Agent 로드 (우선순위 순서)"""
        agents = []
        
        try:
            # RAG Agent
            if self.vectorstore:
                from core.agents.rag_agent import RAGAgent
                agents.append({
                    "name": "RAGAgent",
                    "description": "Internal knowledge base search. Use for: retrieving information from uploaded documents, searching company knowledge base, answering questions based on internal files.",
                    "class": RAGAgent,
                    "init_params": {"llm": self.model_strategy.llm, "vectorstore": self.vectorstore}
                })
            
            # MCP Agent
            if self.tools:
                from core.agents.mcp_agent import MCPAgent
                agents.append({
                    "name": "MCPAgent", 
                    "description": "External tool usage. Use for: web search, API calls, file operations, system commands, real-time data retrieval.",
                    "class": MCPAgent,
                    "init_params": {"llm": self.model_strategy.llm, "tools": self.tools}
                })
            
            # 추가 Agent들을 동적으로 로드 (SQLAgent 제외)
            try:
                import importlib
                import pkgutil
                from core.agents import base_agent
                
                # 비활성화할 Agent 목록
                disabled_agents = ['core.agents.sql_agent']
                
                # core.agents 모듈에서 모든 Agent 클래스 찾기
                agents_module = importlib.import_module('core.agents')
                for importer, modname, ispkg in pkgutil.iter_modules(agents_module.__path__, agents_module.__name__ + "."):
                    if (modname.endswith('_agent') and 
                        modname not in ['core.agents.base_agent', 'core.agents.rag_agent', 'core.agents.mcp_agent'] and
                        modname not in disabled_agents):
                        try:
                            module = importlib.import_module(modname)
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (isinstance(attr, type) and 
                                    issubclass(attr, base_agent.BaseAgent) and 
                                    attr != base_agent.BaseAgent and
                                    hasattr(attr, '__doc__') and attr.__doc__):
                                    
                                    agents.append({
                                        "name": attr.__name__,
                                        "description": attr.__doc__.strip(),
                                        "class": attr,
                                        "init_params": {"llm": self.model_strategy.llm}
                                    })
                        except Exception as e:
                            self.logger.debug(f"Agent 로드 실패: {modname} - {e}")
            
            except Exception as e:
                self.logger.debug(f"동적 Agent 로드 실패: {e}")
            
            self.logger.info(f"로드된 Agent: {len(agents)}개 - {[a['name'] for a in agents]}")
            return agents
            
        except Exception as e:
            self.logger.error(f"Agent 로드 오류: {e}")
            return []
    
    def _select_agent_with_llm(self, user_input: str, available_agents: List[Dict]) -> Optional[Dict]:
        """사용자 입력에 기반하여 LLM이 적절한 Agent 선택"""
        if not available_agents:
            return None
        
        try:
            # Agent 선택 프롬프트 생성
            agent_descriptions = "\n".join([
                f"{i+1}. {agent['name']}: {agent['description']}"
                for i, agent in enumerate(available_agents)
            ])
            
            selection_prompt = f"""
You are an Agent-Selection Router.
Analyze the user's request and choose exactly ONE agent from the list.

Available Agents:
{agent_descriptions}

Instructions:
1. Read the user's request carefully
2. Choose the agent whose capabilities BEST match the request's primary intent
3. Return ONLY the agent number (1-{len(available_agents)})
4. If no agent is suitable, return "0"

User Request: "{user_input}"

Output: (number only)
"""
            
            # 프롬프트 로깅 (디버깅용)
            self.logger.info(f"[AGENT SELECTION PROMPT]\n{selection_prompt}")
            
            # LLM에게 Agent 선택 요청
            response = self.model_strategy.llm.invoke(selection_prompt)
            
            # 응답 로깅
            self.logger.info(f"[AGENT SELECTION RESPONSE] {response.content if hasattr(response, 'content') else response}")
            
            # 응답에서 숫자 추출
            import re
            response_text = str(response.content if hasattr(response, 'content') else response)
            numbers = re.findall(r'\d+', response_text)
            
            if numbers:
                selected_num = int(numbers[0])
                if 1 <= selected_num <= len(available_agents):
                    selected_agent = available_agents[selected_num - 1]
                    self.logger.info(f"LLM Agent 선택: {selected_agent['name']} (입력: {user_input[:50]})")
                    return selected_agent
            
            self.logger.info(f"LLM Agent 선택 실패: 응답={response}")
            return None
            
        except Exception as e:
            self.logger.error(f"LLM Agent 선택 오류: {e}")
            return None
    
    def _execute_selected_agent(self, agent_info: Dict, user_input: str, conversation_history: List[Dict]) -> Tuple[str, List]:
        """선택된 Agent 실행"""
        try:
            agent_class = agent_info["class"]
            init_params = agent_info["init_params"]
            
            # Agent 인스턴스 생성
            agent = agent_class(**init_params)
            
            # RAG Agent인 경우 특별 처리
            if agent_info["name"] == "RAGAgent":
                processor = self.mode_manager.get_processor(
                    mode=ChatMode.RAG,
                    vectorstore=self.vectorstore,
                    mcp_client=self.mcp_client,
                    tools=self.tools,
                    session_id=self.session_id
                )
                return processor.process_message(user_input, conversation_history)
            
            # MCP Agent인 경우 Tool Processor 사용
            elif agent_info["name"] == "MCPAgent":
                if not self.tool_processor:
                    self.tool_processor = ToolChatProcessor(self.model_strategy, self.tools)
                    self.tool_processor.session_id = self.session_id
                return self.tool_processor.process_message(user_input, conversation_history)
            
            # 기타 Agent들은 BaseAgent의 execute 메서드 사용
            else:
                # BaseAgent 기반 Agent들은 execute 메서드 사용
                context = {
                    'conversation_history': conversation_history,
                    'model_name': self.model_name
                }
                result = agent.execute(user_input, context)
                return result.output, []
            
        except Exception as e:
            self.logger.error(f"Agent 실행 오류: {e}")
            return f"Agent 실행 오류: {str(e)[:100]}...", []
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "strategy_type": type(self.model_strategy).__name__,
            "supports_streaming": self.model_strategy.supports_streaming(),
            "tools_count": len(self.tools)
        }