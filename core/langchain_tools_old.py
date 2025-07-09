from typing import Dict, Any, List, Optional, Type, Union
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field
from core.mcp import call_mcp_tool
import json
import logging
import inspect

logger = logging.getLogger(__name__)

class MCPToolInput(BaseModel):
    """MCP 도구 입력 스키마"""
    pass

class MCPTool(BaseTool):
    """MCP 서버의 도구를 LangChain Tool로 래핑"""
    
    server_name: str = Field(description="MCP 서버 이름")
    tool_name: str = Field(description="MCP 도구 이름")
    tool_schema: Dict[str, Any] = Field(description="MCP 도구 스키마")
    
    def __init__(self, server_name: str, tool_name: str, tool_schema: Dict[str, Any], **kwargs):
        # 동적으로 입력 스키마 생성
        input_schema = self._create_input_schema(tool_schema)
        
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
            args_schema=input_schema,
            server_name=server_name,
            tool_name=tool_name,
            tool_schema=tool_schema,
            **kwargs
        )
    
    def _create_input_schema(self, tool_schema: Dict[str, Any]) -> Type[BaseModel]:
        """MCP 도구 스키마에서 Pydantic 모델 생성"""
        input_schema = tool_schema.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        if not properties:
            return MCPToolInput
        
        # 동적으로 필드 생성
        fields = {}
        annotations = {}
        
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")
            description = prop_info.get("description", "")
            
            # Python 타입 매핑
            python_type = self._get_python_type(prop_type)
            
            # 필수 필드 여부 확인
            if prop_name in required:
                annotations[prop_name] = python_type
                fields[prop_name] = Field(description=description)
            else:
                annotations[prop_name] = Optional[python_type]
                fields[prop_name] = Field(default=None, description=description)
        
        # 동적 클래스 생성
        if fields:
            tool_name = tool_schema.get("name", "Unknown")
            safe_name = tool_name.replace("-", "_").replace(".", "_")
            DynamicInputSchema = type(
                f"{safe_name}Input",
                (BaseModel,),
                {
                    "__annotations__": annotations,
                    **fields
                }
            )
            return DynamicInputSchema
        
        return MCPToolInput
    
    def _get_python_type(self, json_type: str):
        """JSON 스키마 타입을 Python 타입으로 변환"""
        type_mapping = {
            "string": str,
            "number": float,
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        return type_mapping.get(json_type, str)
    
    def _run(self, *args, **kwargs: Any) -> str:
        """도구 실행 - LangChain 버전 호환성을 위해 유연한 인수 처리"""
        try:
            # run_manager 추출 (위치 인수 또는 키워드 인수)
            run_manager = None
            if args and len(args) > 0:
                # 첫 번째 인수가 CallbackManagerForToolRun 인스턴스인지 확인
                if hasattr(args[0], 'on_text'):
                    run_manager = args[0]
            elif 'run_manager' in kwargs:
                run_manager = kwargs.pop('run_manager')
            
            # 도구 실행에 필요한 파라미터만 추출
            clean_kwargs = {k: v for k, v in kwargs.items() 
                          if v is not None and v != "" and v != {}}
            
            logger.info(f"MCP 도구 호출: {self.server_name}.{self.tool_name} with {clean_kwargs}")
            
            # run_manager를 사용한 로깅
            if run_manager and hasattr(run_manager, 'on_text'):
                try:
                    run_manager.on_text(f"MCP 도구 호출: {self.server_name}.{self.tool_name}")
                except:
                    pass  # 로깅 실패는 무시
            
            # MCP 도구에 전달할 arguments 준비
            # 빈 값들을 제거하고, 필수 필드가 빠진 경우 기본값 설정
            arguments = {}
            
            # 도구 스키마에서 필수 필드 확인
            input_schema = self.tool_schema.get('inputSchema', {})
            required_fields = input_schema.get('required', [])
            properties = input_schema.get('properties', {})
            
            # 전달된 파라미터 처리
            for key, value in clean_kwargs.items():
                if key in properties:
                    arguments[key] = value
            
            # 필수 필드가 빠진 경우 기본값 설정
            for field in required_fields:
                if field not in arguments:
                    # 기본값이 있는지 확인
                    field_info = properties.get(field, {})
                    if 'default' in field_info:
                        arguments[field] = field_info['default']
                    else:
                        logger.warning(f"필수 필드 '{field}'가 빠졌습니다: {clean_kwargs}")
            
            logger.info(f"MCP 도구에 전달할 arguments: {arguments}")
            
            result = call_mcp_tool(self.server_name, self.tool_name, arguments if arguments else None)
            
            if result is None:
                return f"도구 '{self.tool_name}' 호출 실패"
            
            # 결과를 문자열로 변환
            if isinstance(result, dict):
                return json.dumps(result, ensure_ascii=False, indent=2)
            elif isinstance(result, list):
                return json.dumps(result, ensure_ascii=False, indent=2)
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"MCP 도구 실행 오류: {e}")
            if run_manager and hasattr(run_manager, 'on_text'):
                try:
                    run_manager.on_text(f"오류: {str(e)}")
                except:
                    pass
            return f"도구 실행 중 오류 발생: {str(e)}"


class MCPToolRegistry:
    """MCP 도구를 LangChain 도구로 등록 및 관리"""
    
    def __init__(self):
        self.tools: List[MCPTool] = []
        self.tools_by_category: Dict[str, List[MCPTool]] = {}
    
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
                        tool_schema=tool_schema
                    )
                    
                    self.tools.append(mcp_tool)
                    server_tools.append(mcp_tool)
                    logger.info(f"도구 등록 성공: {server_name}.{tool_name}")
                    
                except Exception as e:
                    logger.error(f"도구 등록 실패 {server_name}.{tool_name}: {e}")
                    logger.error(f"도구 스키마: {tool_schema}")
                    import traceback
                    logger.error(f"상세 오류: {traceback.format_exc()}")
                    continue
            
            if server_tools:
                self.tools_by_category[server_name] = server_tools
        
        logger.info(f"총 {len(self.tools)}개 도구 등록 완료")
        
        # 등록된 도구 목록 출력
        for tool in self.tools:
            logger.info(f"  ✓ {tool.name}")
        
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


# 전역 도구 레지스트리
tool_registry = MCPToolRegistry()