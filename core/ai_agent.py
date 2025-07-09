from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.agents import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import BaseTool
from core.langchain_tools import tool_registry, MCPTool
from core.mcp import get_all_mcp_tools
from core.tool_manager import tool_manager, ToolCategory
from core.conversation_history import ConversationHistory
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AIAgent:
    """AI 에이전트 - 도구 사용 여부를 결정하고 실행"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model_name = model_name
        self.llm = self._create_llm()
        self.tools: List[MCPTool] = []
        self.agent_executor: Optional[AgentExecutor] = None
        self.conversation_history = ConversationHistory()
        
        # MCP 도구 로드 및 등록
        self._load_mcp_tools()
        # 기존 히스토리 로드
        self.conversation_history.load_from_file()
    
    def _create_llm(self):
        """LLM 인스턴스 생성"""
        if self.model_name.startswith('gemini'):
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=self.api_key,
                temperature=0.1
            )
        else:
            return ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.api_key,
                temperature=0.1
            )
    
    def _load_mcp_tools(self):
        """MCP 도구 로드 및 LangChain 도구로 등록"""
        try:
            all_mcp_tools = get_all_mcp_tools()
            if all_mcp_tools:
                # 모든 도구 등록
                self.tools = tool_registry.register_mcp_tools(all_mcp_tools)
                tool_manager.register_tools(all_mcp_tools)
                logger.info(f"AI 에이전트에 {len(self.tools)}개 도구 로드됨")
            else:
                logger.warning("사용 가능한 MCP 도구가 없습니다")
        except Exception as e:
            logger.error(f"MCP 도구 로드 실패: {e}")
    
    def _should_use_tools(self, user_input: str) -> bool:
        """AI가 컴텍스트를 분석하여 도구 사용 여부 결정"""
        try:
            # 도구 목록 요청은 항상 도구 사용
            if any(keyword in user_input.lower() for keyword in ['도구', '툴', 'tool', '기능', '목록', '리스트']):
                return True
            
            # 도구 설명 수집 (간단하게)
            tool_names = [tool.name for tool in self.tools[:5]]  # 첫 5개만
            tools_summary = ", ".join(tool_names) if tool_names else "없음"
            
            decision_prompt = f"""사용자: "{user_input}"

사용 가능한 도구: {tools_summary}

이 요청이 도구를 사용해야 하는 작업인지 판단하세요.
예: 데이터 검색, 웹 조회, 여행 상품 찾기 등은 도구 필요.
예: 일반 대화, 설명 요청, 의견 문의 등은 도구 불필요.

YES 또는 NO로만 답하세요."""
            
            messages = [
                SystemMessage(content="도구 사용 판단 전문가"),
                HumanMessage(content=decision_prompt)
            ]
            
            response = self.llm.invoke(messages)
            decision = response.content.strip().upper()
            
            result = decision == "YES"
            logger.info(f"도구 사용 판단: {decision} -> {result} (입력: {user_input[:30]}...)")
            return result
            
        except Exception as e:
            logger.error(f"도구 사용 판단 오류: {e}")
            return False
    
    def _create_agent_executor(self) -> AgentExecutor:
        """에이전트 실행기 생성"""
        if not self.tools:
            return None
        
        # OpenAI 도구 에이전트 생성 (GPT 모델용)
        if not self.model_name.startswith('gemini'):
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
            
            system_message = """당신은 다양한 도구를 사용할 수 있는 AI 어시스턴트입니다.

사용자의 요청을 분석하여 가장 적절한 도구를 선택하고 사용하세요.
도구 사용 결과를 바탕으로 사용자에게 유용한 답변을 제공하세요."""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            agent = create_openai_tools_agent(self.llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=True, max_iterations=2, handle_parsing_errors=True)
        
        # ReAct 에이전트 생성 (Gemini 등 다른 모델용)
        else:
            react_prompt = PromptTemplate.from_template("""
당신은 도구를 사용할 수 있는 AI 어시스턴트입니다.

사용 가능한 도구들:
{tools}

도구 이름들: {tool_names}

다음 형식을 정확히 따르세요:

Question: {input}
Thought: 이 질문에 답하기 위해 어떤 도구를 사용해야 할지 생각해보겠습니다.
Action: 도구이름
Action Input: 도구에 전달할 입력값
Observation: 도구 실행 결과
Thought: 결과를 바탕으로 최종 답변을 작성하겠습니다.
Final Answer: 사용자 질문에 대한 최종 답변

{agent_scratchpad}
""")
            
            agent = create_react_agent(self.llm, self.tools, react_prompt)
            return AgentExecutor(
                agent=agent, 
                tools=self.tools, 
                verbose=False,
                max_iterations=2,
                handle_parsing_errors=True,
                early_stopping_method="force",
                return_intermediate_steps=False
            )
    
    def chat_with_tools(self, user_input: str) -> str:
        """도구를 사용한 채팅"""
        try:
            # 토큰 제한 오류 방지를 위해 대화 히스토리 제한
            if "context_length_exceeded" in str(getattr(self, '_last_error', '')):
                logger.warning("토큰 제한 오류로 인해 일반 채팅으로 대체")
                return self.simple_chat(user_input)
            
            # Gemini 모델은 직접 도구 호출 방식 사용
            if self.model_name.startswith('gemini'):
                return self._gemini_tool_chat(user_input)
            
            # GPT 모델은 기존 에이전트 방식 사용
            if not self.agent_executor:
                self.agent_executor = self._create_agent_executor()
            
            if not self.agent_executor:
                return "사용 가능한 도구가 없습니다."
            
            result = self.agent_executor.invoke({"input": user_input})
            output = result.get("output", "")
            
            if "Agent stopped" in output or not output.strip():
                logger.warning("에이전트 중단로 인해 일반 채팅으로 대체")
                return self.simple_chat(user_input)
            
            return output
            
        except Exception as e:
            error_msg = str(e)
            self._last_error = error_msg
            logger.error(f"도구 사용 채팅 오류: {e}")
            
            # 토큰 제한 오류 처리
            if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                logger.warning("토큰 제한 오류 발생, 일반 채팅으로 대체")
                return self.simple_chat(user_input)
            
            return self.simple_chat(user_input)
    
    def simple_chat(self, user_input: str) -> str:
        """일반 채팅 (도구 사용 없음)"""
        try:
            # 가독성 좋은 응답을 위한 시스템 메시지
            system_content = """당신은 도움이 되는 AI 어시스턴트입니다. 친근하고 정확한 답변을 제공하세요.

**응답 형식 가이드라인:**
- 긴 문장은 적절히 줄바꿈하여 가독성 향상
- 중요한 정보는 **굵은 글씨**나 • 불릿 포인트 사용
- 여러 항목이 있을 때는 번호나 구분자로 정리
- 한 줄에 너무 많은 내용을 담지 말고 단락으로 구분
- 핵심 내용을 먼저 제시하고 세부사항은 뒤에 배치"""
            
            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=user_input)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"일반 채팅 오류: {e}")
            return f"죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요."
    
    def simple_chat_with_history(self, user_input: str, conversation_history: List[Dict]) -> str:
        """대화 기록을 포함한 일반 채팅"""
        try:
            messages = self._convert_history_to_messages(conversation_history)
            # 마지막 사용자 메시지 추가
            messages.append(HumanMessage(content=user_input))
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"대화 기록 채팅 오류: {e}")
            return self.simple_chat(user_input)
    
    def process_message(self, user_input: str) -> tuple[str, bool]:
        """메시지 처리 - AI가 도구 사용 여부 결정"""
        # 사용자 메시지를 히스토리에 추가
        self.conversation_history.add_message("user", user_input)
        
        if not self.tools:
            response = self.simple_chat_with_history(user_input, self.conversation_history.get_recent_messages(10))
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, False
        
        # AI가 컨텍스트를 분석하여 도구 사용 여부 결정
        use_tools = self._should_use_tools(user_input)
        
        if use_tools:
            response = self.chat_with_tools(user_input)
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, True
        else:
            response = self.simple_chat_with_history(user_input, self.conversation_history.get_recent_messages(10))
            self.conversation_history.add_message("assistant", response)
            self.conversation_history.save_to_file()
            return response, False
    
    def process_message_with_history(self, user_input: str, conversation_history: List[Dict]) -> tuple[str, bool]:
        """대화 기록을 포함한 메시지 처리"""
        if not self.tools:
            response = self.simple_chat_with_history(user_input, conversation_history)
            return response, False
        
        use_tools = self._should_use_tools(user_input)
        
        if use_tools:
            response = self.chat_with_tools(user_input)
            return response, True
        else:
            response = self.simple_chat_with_history(user_input, conversation_history)
            return response, False
    
    def _convert_history_to_messages(self, conversation_history: List[Dict]):
        """대화 기록을 LangChain 메시지로 변환 - 토큰 제한 고려"""
        messages = []
        
        # 간단한 시스템 메시지
        messages.append(SystemMessage(content="AI 어시스턴트"))
        
        # 토큰 제한을 위해 최근 2개 메시지만 사용
        recent_history = conversation_history[-2:] if len(conversation_history) > 2 else conversation_history
        
        for msg in recent_history:
            role = msg.get('role', '')
            content = msg.get('content', '')[:100]  # 내용도 100자로 제한
            if role == 'user':
                messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                from langchain.schema import AIMessage
                messages.append(AIMessage(content=content))
        
        return messages
    
    def _gemini_tool_chat(self, user_input: str) -> str:
        """게미니 모델용 AI 기반 도구 선택 및 실행"""
        try:
            # 도구 목록 요청 처리
            if any(keyword in user_input.lower() for keyword in ['도구', '툴', 'tool', '기능', '목록', '리스트']):
                return self._show_tool_list()
            
            # 1단계: AI가 사용할 도구와 파라미터 결정
            tool_decision = self._ai_select_tool(user_input)
            if tool_decision:
                tool_decision['original_query'] = user_input  # 청크 처리용
            
            if not tool_decision or tool_decision.get('tool') == 'none':
                return self.simple_chat(user_input)
            
            # 2단계: 선택된 도구 실행
            tool_result = self._execute_selected_tool(tool_decision)
            
            # 3단계: 결과를 바탕으로 최종 응답 생성
            return self._generate_final_response(user_input, tool_result)
            
        except Exception as e:
            logger.error(f"게미니 도구 채팅 오류: {e}")
            return self.simple_chat(user_input)
    
    def _get_realistic_date_range(self, user_input: str) -> tuple[str, str]:
        """사용자 입력에서 현실적인 날짜 범위 생성"""
        now = datetime.now()
        
        # 사용자 입력에서 연도/월 추출
        import re
        year_match = re.search(r'(20\d{2})', user_input)
        month_match = re.search(r'(\d{1,2})월', user_input)
        
        if year_match and month_match:
            year = int(year_match.group(1))
            month = int(month_match.group(1))
            
            # 너무 먼 미래는 현재로부터 3개월 후로 조정
            target_date = datetime(year, month, 1)
            max_future = now + timedelta(days=90)  # 3개월
            
            if target_date > max_future:
                target_date = max_future.replace(day=1)
        else:
            # 날짜 없으면 다음 달
            target_date = (now + timedelta(days=30)).replace(day=1)
        
        # 시작일과 종료일 생성
        start_date = target_date.strftime('%Y%m%d')
        end_date = (target_date + timedelta(days=30)).strftime('%Y%m%d')
        
        return start_date, end_date
    
    def _get_area_code(self, user_input: str) -> str:
        """사용자 입력에서 지역 코드 추출"""
        user_lower = user_input.lower()
        
        # 지역별 코드 매핑
        area_mapping = {
            '동남아': 'A0',
            '아시아': 'A0', 
            '태국': 'A0',
            '베트남': 'A0',
            '싱가포르': 'A0',
            '인도네시아': 'A0',
            '유럽': 'E0',
            '영국': 'E0',
            '프랑스': 'E0',
            '독일': 'E0',
            '이탈리아': 'E0',
            '스페인': 'E0',
            '일본': 'J0',
            '중국': 'C0',
            '미국': 'U0',
            '캐나다': 'U0'
        }
        
        for region, code in area_mapping.items():
            if region in user_lower:
                return code
        
        # 기본값: 동남아
        return 'A0'
    
    def _ai_select_tool(self, user_input: str):
        """게미니 AI가 사용할 도구와 파라미터 결정 - 토큰 제한 고려"""
        try:
            if not self.tools:
                logger.warning("사용 가능한 도구가 없습니다")
                return None
            
            # 도구 설명 수집
            tools_info = []
            for tool in self.tools:
                desc = getattr(tool, 'description', tool.name)
                tools_info.append(f"- {tool.name}: {desc}")
            
            tools_list = "\n".join(tools_info)
            
            # 여행 상품 검색인 경우 현실적인 날짜와 지역 코드 제안
            realistic_dates = ""
            if any(keyword in user_input for keyword in ['여행', '상품', '패키지']):
                start_date, end_date = self._get_realistic_date_range(user_input)
                area_code = self._get_area_code(user_input)
                realistic_dates = f"\n\n**추천 파라미터:**\n- startDate: {start_date}\n- endDate: {end_date}\n- productAreaCode: {area_code}"
            
            selection_prompt = f"""사용자 요청: "{user_input}"

사용 가능한 도구들:
{tools_list}{realistic_dates}

사용자 요청을 처리하기 위해 어떤 도구를 사용해야 하는지 결정하고, 필요한 파라미터를 추출하세요.

다음 형식으로 답하세요:
- 도구가 필요한 경우: TOOL: 도구이름 | PARAMS: {{"key": "value"}}
- 도구가 필요없는 경우: TOOL: none"""
            
            # 간단한 메시지만 사용
            messages = [
                SystemMessage(content="도구 선택 전문가"),
                HumanMessage(content=selection_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return self._parse_tool_decision(response.content)
            
        except Exception as e:
            logger.error(f"AI 도구 선택 오류: {e}")
            return None
    
    def _parse_tool_decision(self, response: str):
        """도구 선택 응답 파싱"""
        try:
            import re
            import json
            
            logger.info(f"파싱할 응답: {response}")
            
            # "TOOL: toolname | PARAMS: {...}" 형식 파싱
            match = re.search(r'TOOL:\s*([^|\n]+)(?:\s*\|\s*PARAMS:\s*([^\n]+))?', response, re.IGNORECASE)
            if not match:
                logger.warning(f"도구 형식 매칭 실패: {response}")
                return None
            
            tool_name = match.group(1).strip()
            params_str = match.group(2).strip() if match.group(2) else '{}'
            
            logger.info(f"파싱된 도구명: '{tool_name}', 파라미터: '{params_str}'")
            
            if tool_name.lower() == 'none':
                return {'tool': 'none'}
            
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError as je:
                logger.warning(f"JSON 파싱 실패: {params_str}, 오류: {je}")
                params = {}
            
            return {
                'tool': tool_name,
                'params': params
            }
            
        except Exception as e:
            logger.error(f"도구 결정 파싱 오류: {e}")
            return None
    
    def _split_large_response(self, response_text: str, max_chunk_size: int = 3000) -> List[str]:
        """큰 응답을 청크로 분할"""
        if len(response_text) <= max_chunk_size:
            return [response_text]
        
        chunks = []
        current_pos = 0
        
        while current_pos < len(response_text):
            # JSON 구조를 고려한 분할 지점 찾기
            end_pos = min(current_pos + max_chunk_size, len(response_text))
            
            # JSON 객체나 배열 끝에서 분할
            if end_pos < len(response_text):
                # 뒤에서 가장 가까운 }, ] 찾기
                for i in range(end_pos, current_pos, -1):
                    if response_text[i] in ['}', ']', ',']:
                        end_pos = i + 1
                        break
            
            chunk = response_text[current_pos:end_pos]
            chunks.append(chunk)
            current_pos = end_pos
        
        return chunks
    
    def _process_chunked_response(self, large_response: str, user_query: str) -> str:
        """대용량 응답을 전체 분석하여 결과만 보여주기"""
        logger.info(f"대용량 응답 분석 시작: {len(large_response)}자")
        
        # 전체 데이터를 한 번에 분석
        analysis_prompt = f"""사용자 질의: {user_query}

데이터:
{large_response}

위 데이터를 분석하여 사용자에게 유용한 정보를 제공해주세요. 청크 번호나 분석 진행 상황은 언급하지 말고 결과만 보여주세요."""
        
        messages = [
            SystemMessage(content="당신은 데이터를 분석하여 사용자에게 유용한 정보를 제공하는 전문가입니다. 분석 과정은 언급하지 말고 결과만 보여주세요."),
            HumanMessage(content=analysis_prompt)
        ]
        
        analysis_response = self.llm.invoke(messages)
        return analysis_response.content
    
    def _execute_selected_tool(self, tool_decision):
        """선택된 도구 실행"""
        try:
            tool_name = tool_decision['tool']
            params = tool_decision.get('params', {})
            
            # 도구 스키마에 따라 파라미터 자동 변환
            selected_tool = None
            for tool in self.tools:
                if tool.name.lower() == tool_name.lower():
                    selected_tool = tool
                    break
            
            if selected_tool and hasattr(selected_tool, 'args_schema') and selected_tool.args_schema:
                try:
                    schema = selected_tool.args_schema.schema()
                    if 'properties' in schema:
                        for param_name, param_value in params.items():
                            if param_name in schema['properties']:
                                param_schema = schema['properties'][param_name]
                                if param_schema.get('type') == 'array' and isinstance(param_value, str):
                                    params[param_name] = [param_value]
                except:
                    pass
            
            logger.info(f"도구 찾기: '{tool_name}'")
            
            # 도구 찾기 (더 유연한 매칭)
            selected_tool = None
            for tool in self.tools:
                tool_name_lower = tool_name.lower()
                actual_name_lower = tool.name.lower()
                
                # 정확한 이름 매칭 또는 부분 매칭
                if (tool_name_lower == actual_name_lower or 
                    tool_name_lower in actual_name_lower or 
                    actual_name_lower in tool_name_lower or
                    tool_name_lower.replace('_', '-') == actual_name_lower.replace('_', '-')):
                    selected_tool = tool
                    logger.info(f"도구 매칭 성공: '{tool_name}' -> '{tool.name}'")
                    break
            
            if not selected_tool:
                available_tools = [t.name for t in self.tools]
                logger.error(f"도구 '{tool_name}'을 찾을 수 없습니다. 사용 가능한 도구: {available_tools}")
                return f"도구 '{tool_name}'을 찾을 수 없습니다. 사용 가능한 도구: {available_tools}"
            
            # 검색 도구의 경우 더 많은 결과 요청
            if 'search' in selected_tool.name.lower():
                if 'limit' not in params and 'maxResults' not in params:
                    params['maxResults'] = 10  # 기본 10개 결과
                if 'includeHtml' not in params:
                    params['includeHtml'] = False
            
            # 도구 실행 (GPT 스타일 로깅)
            print(f"\n> Invoking: `{selected_tool.name}` with `{params}`\n")
            
            result = selected_tool.invoke(params)
            
            # 결과 출력
            print(result)
            print("\n")
            
            # 결과가 비어있는 경우 대안 제시
            if isinstance(result, str) and ('"resultCount": 0' in result or '"saleProductItemResponseList": []' in result):
                logger.warning(f"도구 실행 결과가 비어있음: {selected_tool.name}")
                return f"검색 결과가 없습니다. 다른 날짜나 지역으로 다시 시도해보세요.\n\n원본 결과: {result}"
            
            logger.info(f"도구 실행 결과: {str(result)[:200]}...")
            
            # 대용량 응답 처리
            if isinstance(result, str) and len(result) > 5000:
                logger.info(f"대용량 응답 감지: {len(result)}자")
                original_query = tool_decision.get('original_query', '') if isinstance(tool_decision, dict) else ''
                return self._process_chunked_response(result, original_query)
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"도구 실행 오류: {e}")
            
            # 타임아웃 오류 처리
            if 'timeout' in error_msg.lower() or 'MCP 응답 타임아웃' in error_msg:
                return f"도구 호출 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            
            return f"도구 실행 중 오류가 발생했습니다: {e}"
    
    def _show_tool_list(self) -> str:
        """사용 가능한 도구 목록을 동적으로 생성하여 반환"""
        if not self.tools:
            return "현재 사용 가능한 도구가 없습니다."
        
        # 서버별로 도구 분류
        tools_by_server = {}
        for tool in self.tools:
            server_name = getattr(tool, 'server_name', 'Unknown')
            if server_name not in tools_by_server:
                tools_by_server[server_name] = []
            tools_by_server[server_name].append(tool)
        
        # 도구 목록 생성
        result = ["🔧 **사용 가능한 도구 목록**\n"]
        
        for server_name, server_tools in tools_by_server.items():
            result.append(f"📦 **{server_name}** ({len(server_tools)}개 도구):")
            for tool in server_tools:
                desc = getattr(tool, 'description', tool.name)
                # 전체 설명 표시
                result.append(f"  • {tool.name}: {desc}")
            result.append("")  # 빈 줄 추가
        
        result.append(f"총 {len(self.tools)}개의 도구를 사용할 수 있습니다.")
        return "\n".join(result)
    
    def _format_response(self, text: str) -> str:
        """응답 텍스트를 가독성 좋게 포맷팅"""
        if not text or len(text) < 50:
            return text
        
        import re
        
        # 1. 문장 끝에 줄바꿈 추가
        formatted = text.replace('다. ', '다.\n\n')
        formatted = formatted.replace('습니다. ', '습니다.\n\n')
        
        # 2. 연속된 정보를 불릿으로 변환
        formatted = re.sub(r'([^.]+?)은 ([^,이며]+?)[이고,]\s*', r'• **\1**: \2\n', formatted)
        formatted = re.sub(r'([^.]+?)는 ([^,이며]+?)[이며,]\s*', r'• **\1**: \2\n', formatted)
        
        # 3. 주요 정보 강조
        formatted = re.sub(r'(대통령|정부|관세|협상|대응)', r'**\1**', formatted)
        
        # 4. 과도한 줄바꿈 정리
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        
        return formatted.strip()
    
    def _generate_final_response(self, user_input: str, tool_result: str):
        """도구 결과를 바탕으로 최종 응답 생성 - 토큰 제한 고려"""
        try:
            # 도구 결과가 너무 길면 요약
            if len(tool_result) > 2000:
                tool_result = tool_result[:2000] + "...(생략)"
            
            response_prompt = f"""질문: {user_input}
결과: {tool_result}

위 결과를 바탕으로 사용자에게 도움되는 답변을 작성하세요."""
            
            messages = [
                SystemMessage(content="AI 어시스턴트"),
                HumanMessage(content=response_prompt)
            ]
            
            response = self.llm.invoke(messages)
            return self._format_response(response.content)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"최종 응답 생성 오류: {e}")
            
            # 토큰 제한 오류 처리
            if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                return self._format_response("검색 결과를 찾았지만 내용이 너무 길어 요약할 수 없습니다. 더 구체적인 질문으로 다시 시도해주세요.")
            
            return self._format_response("도구 실행은 성공했지만 응답 생성 중 오류가 발생했습니다.")