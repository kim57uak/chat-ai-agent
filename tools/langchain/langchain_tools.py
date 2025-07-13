from typing import Dict, Any, List, Optional, Type, Union
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from core.mcp_interface import MCPToolCaller
import json
import logging

logger = logging.getLogger(__name__)

class MCPTool(BaseTool):
    """MCP 서버의 도구를 LangChain Tool로 래핑"""
    
    server_name: str = Field(description="MCP 서버 이름")
    tool_name: str = Field(description="MCP 도구 이름")
    tool_schema: Dict[str, Any] = Field(description="MCP 도구 스키마")
    mcp_caller: MCPToolCaller = Field(description="MCP 도구 호출자")
    
    def __init__(self, server_name: str, tool_name: str, tool_schema: Dict[str, Any], mcp_caller: MCPToolCaller, **kwargs):
        # 도구 이름 길이 제한 (OpenAI API 64자 제한)
        full_name = f"{server_name}_{tool_name}"
        if len(full_name) > 60:  # 안전 마진
            # 서버명 축약
            server_short = server_name[:10] if len(server_name) > 10 else server_name
            tool_short = tool_name[:45] if len(tool_name) > 45 else tool_name
            full_name = f"{server_short}_{tool_short}"
        
        super().__init__(
            name=full_name,
            description=tool_schema.get("description", f"{server_name}의 {tool_name} 도구"),
            server_name=server_name,
            tool_name=tool_name,
            tool_schema=tool_schema,
            mcp_caller=mcp_caller,
            **kwargs
        )
    
    def _run(self, *args, **kwargs):
        """도구 실행"""
        # ReAct 에이전트의 문자열 입력 처리
        if args and len(args) == 1 and isinstance(args[0], str):
            try:
                import json
                parsed_input = json.loads(args[0])
                return self._execute_tool(parsed_input)
            except:
                # JSON 파싱 실패 시 스키마 기반 처리
                input_schema = self.tool_schema.get('inputSchema', {})
                required = input_schema.get('required', [])
                if required:
                    return self._execute_tool({required[0]: args[0]})
                return self._execute_tool({'input': args[0]})
        
        return self._execute_tool(kwargs)
    
    def invoke(self, input_data: Dict[str, Any], config=None, **kwargs):
        """OpenAI 도구 에이전트용 invoke 메서드"""
        return self._execute_tool(input_data)
    
    def _execute_tool(self, input_data: Dict[str, Any]):
        """실제 도구 실행 로직"""
        try:
            logger.info(f"MCP 도구 호출: {self.server_name}.{self.tool_name}")
            logger.info(f"원본 입력 데이터: {input_data}")
            
            # OpenAI 도구 에이전트의 특수한 형식 처리
            processed_input = self._process_openai_input(input_data)
            logger.info(f"처리된 입력 데이터: {processed_input}")
            
            # run_manager 제거
            clean_input = {k: v for k, v in processed_input.items() if k != 'run_manager'}
            
            # MCP 도구에 전달할 arguments 준비
            arguments = {}
            
            # 도구 스키마에서 필수 필드 확인
            input_schema = self.tool_schema.get('inputSchema', {})
            properties = input_schema.get('properties', {})
            
            # 전달된 파라미터 처리 (None이 아닌 값만)
            for key, value in clean_input.items():
                if value is not None and value != "" and key in properties:
                    # 타입 변환 처리
                    property_schema = properties[key]
                    expected_type = property_schema.get('type')
                    
                    # 날짜 파라미터 (startDate, endDate) 숫자 변환
                    if expected_type == 'number' and isinstance(value, str) and value.isdigit():
                        arguments[key] = int(value)
                    else:
                        arguments[key] = value
            
            logger.info(f"MCP 도구에 전달할 arguments: {arguments}")
            
            result = self.mcp_caller.call_tool(self.server_name, self.tool_name, arguments if arguments else None)
            
            if result is None:
                return f"도구 '{self.tool_name}' 호출 실패"
            
            # 결과를 문자열로 변환 (범용적 처리)
            if isinstance(result, dict):
                # 검색 도구의 경우 특별 포맷팅
                if self.tool_name == 'search' and 'content' in result:
                    return self._format_search_result(result)
                # 모든 구조화된 데이터는 동일하게 처리
                else:
                    return json.dumps(result, ensure_ascii=False, indent=2)
            elif isinstance(result, list):
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"MCP 도구 실행 오류: {e}")
            return f"도구 '{self.tool_name}' 호출 실패. 오류: {str(e)}"
    
    def _process_openai_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI 도구 에이전트의 입력 형식을 스키마 기반으로 처리"""
        # {'args': []} 형태를 스키마 기반으로 매핑
        if 'args' in input_data and isinstance(input_data['args'], list):
            args = input_data['args']
            input_schema = self.tool_schema.get('inputSchema', {})
            required = input_schema.get('required', [])
            properties = input_schema.get('properties', {})
            
            result = {}
            for i, arg in enumerate(args):
                if i < len(required):
                    field_name = required[i]
                    field_schema = properties.get(field_name, {})
                    if field_schema.get('type') == 'array':
                        result[field_name] = [arg] if isinstance(arg, str) else arg
                    else:
                        result[field_name] = arg
            
            return result if result else {'input': args[0] if args else ''}
        
        return input_data
    
    def _format_search_result(self, result: Dict[str, Any]) -> str:
        """검색 결과 포맷팅 (요약하지 않고 구조화)"""
        try:
            content = result.get('content', [])
            if not content:
                return "검색 결과가 없습니다."
            
            # 모든 검색 결과 처리 (첫 번째만이 아닌)
            formatted_results = []
            
            for i, item in enumerate(content[:3]):  # 최대 3개 결과만
                text_content = item.get('text', '')
                
                # JSON 파싱 시도
                if text_content.startswith('['):
                    try:
                        search_data = json.loads(text_content)
                        if isinstance(search_data, list):
                            for j, search_item in enumerate(search_data[:2]):  # 각 결과에서 최대 2개
                                query = search_item.get('query', '')
                                engine = search_item.get('engine', '')
                                result_text = search_item.get('resultText', '')
                                url = search_item.get('url', '')
                                
                                formatted_results.append(f"**검색 결과 {len(formatted_results)+1}:**")
                                formatted_results.append(f"검색어: {query}")
                                formatted_results.append(f"검색엔진: {engine}")
                                if url:
                                    formatted_results.append(f"URL: {url}")
                                formatted_results.append(f"내용: {result_text}")
                                formatted_results.append("")  # 빈 줄
                    except:
                        # JSON 파싱 실패 시 원본 텍스트 사용
                        formatted_results.append(f"**검색 결과 {len(formatted_results)+1}:**")
                        formatted_results.append(text_content)
                        formatted_results.append("")  # 빈 줄
                else:
                    # 일반 텍스트 결과
                    formatted_results.append(f"**검색 결과 {len(formatted_results)+1}:**")
                    formatted_results.append(text_content)
                    formatted_results.append("")  # 빈 줄
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"검색 결과 포맷팅 오류: {e}")
            return f"검색 결과 처리 중 오류가 발생했습니다: {e}"


class MCPToolRegistry:
    """MCP 도구를 LangChain 도구로 등록 및 관리"""
    
    def __init__(self, mcp_caller: MCPToolCaller):
        self.tools: List[MCPTool] = []
        self.tools_by_category: Dict[str, List[MCPTool]] = {}
        self.mcp_caller = mcp_caller
    
    def register_mcp_tools(self, all_mcp_tools: Dict[str, List[Dict[str, Any]]]) -> List[MCPTool]:
        """MCP 도구들을 LangChain 도구로 등록"""
        self.tools.clear()
        self.tools_by_category.clear()
        
        for server_name, tools in all_mcp_tools.items():
            server_tools = []
            
            for tool_schema in tools:
                tool_name = tool_schema.get("name")
                if not tool_name:
                    continue
                    
                try:
                    mcp_tool = MCPTool(
                        server_name=server_name,
                        tool_name=tool_name,
                        tool_schema=tool_schema,
                        mcp_caller=self.mcp_caller
                    )
                    
                    self.tools.append(mcp_tool)
                    server_tools.append(mcp_tool)
                    logger.info(f"도구 등록 성공: {server_name}.{tool_name}")
                    
                except Exception as e:
                    logger.error(f"도구 등록 실패 {server_name}.{tool_name}: {e}")
                    continue
            
            if server_tools:
                self.tools_by_category[server_name] = server_tools
        
        logger.info(f"총 {len(self.tools)}개 도구 등록 완료")
        return self.tools
    
    def get_tools(self, category: Optional[str] = None) -> List[MCPTool]:
        """도구 목록 반환"""
        if category:
            return self.tools_by_category.get(category, [])
        return self.tools
    
    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """이름으로 도구 찾기"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tools_description(self) -> str:
        """도구 목록 설명 반환"""
        if not self.tools:
            return "사용 가능한 도구가 없습니다."
        
        descriptions = []
        for category, tools in self.tools_by_category.items():
            descriptions.append(f"\n📦 {category} ({len(tools)}개 도구):")
            for tool in tools[:5]:  # 처음 5개만
                descriptions.append(f"  🔧 {tool.name}: {tool.description[:100]}...")
            if len(tools) > 5:
                descriptions.append(f"  ... 및 {len(tools) - 5}개 더")
        
        return "\n".join(descriptions)


# 도구 레지스트리 팩토리 함수
def create_tool_registry(mcp_caller: MCPToolCaller) -> MCPToolRegistry:
    """MCP 도구 레지스트리 생성"""
    return MCPToolRegistry(mcp_caller)