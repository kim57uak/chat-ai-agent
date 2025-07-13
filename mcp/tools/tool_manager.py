from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class ToolCategory(Enum):
    """도구 카테고리"""
    SEARCH = "search"
    DATABASE = "database"
    EMAIL = "email"
    TRAVEL = "travel"
    OFFICE = "office"
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    GENERAL = "general"

@dataclass
class ToolInfo:
    """도구 정보"""
    name: str
    server_name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]
    usage_count: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0

class ToolManager:
    """고급 도구 관리 시스템"""
    
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}
        self.category_mapping = self._create_category_mapping()
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
    
    def _create_category_mapping(self) -> Dict[str, ToolCategory]:
        """서버명 기반 동적 카테고리 매핑 - 키워드 기반 분류"""
        # 하드코딩 대신 키워드 기반 동적 분류
        return {}
    
    def register_tools(self, all_mcp_tools: Dict[str, List[Dict[str, Any]]]):
        """MCP 도구들을 등록하고 동적 분류"""
        self.tools.clear()
        
        for server_name, tools in all_mcp_tools.items():
            category = self._classify_server_dynamically(server_name, tools)
            
            for tool_schema in tools:
                tool_name = tool_schema.get('name')
                if not tool_name:
                    continue
                
                full_name = f"{server_name}_{tool_name}"
                
                tool_info = ToolInfo(
                    name=full_name,
                    server_name=server_name,
                    description=tool_schema.get('description', ''),
                    category=category,
                    parameters=tool_schema.get('inputSchema', {})
                )
                
                self.tools[full_name] = tool_info
                logger.debug(f"도구 등록: {full_name} ({category.value})")
        
        logger.info(f"총 {len(self.tools)}개 도구 등록 완료")
    
    def _classify_server_dynamically(self, server_name: str, tools: List[Dict[str, Any]]) -> ToolCategory:
        """모든 서버를 GENERAL로 분류 - AI가 동적으로 선택"""
        return ToolCategory.GENERAL
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolInfo]:
        """카테고리별 도구 조회"""
        return [tool for tool in self.tools.values() if tool.category == category]
    
    def get_recommended_tools(self, user_input: str, limit: int = 5) -> List[ToolInfo]:
        """모든 도구를 동일하게 반환 - AI가 선택"""
        all_tools = list(self.tools.values())
        # 사용 통계 기반 정렬만 유지
        all_tools.sort(key=lambda x: x.success_rate * (x.usage_count + 1), reverse=True)
        return all_tools[:limit]
    
    def record_tool_usage(self, tool_name: str, success: bool, response_time: float = 0.0):
        """도구 사용 통계 기록"""
        if tool_name not in self.tools:
            return
        
        tool = self.tools[tool_name]
        tool.usage_count += 1
        
        # 성공률 업데이트 (이동 평균)
        if tool.usage_count == 1:
            tool.success_rate = 1.0 if success else 0.0
        else:
            alpha = 0.1  # 학습률
            tool.success_rate = (1 - alpha) * tool.success_rate + alpha * (1.0 if success else 0.0)
        
        # 응답 시간 업데이트
        if response_time > 0:
            if tool.avg_response_time == 0:
                tool.avg_response_time = response_time
            else:
                tool.avg_response_time = 0.9 * tool.avg_response_time + 0.1 * response_time
        
        logger.debug(f"도구 사용 기록: {tool_name} (성공: {success}, 성공률: {tool.success_rate:.2f})")
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """도구 사용 통계 반환"""
        stats = {
            'total_tools': len(self.tools),
            'categories': {},
            'top_tools': [],
            'low_performance_tools': []
        }
        
        # 카테고리별 통계
        for category in ToolCategory:
            category_tools = self.get_tools_by_category(category)
            if category_tools:
                stats['categories'][category.value] = {
                    'count': len(category_tools),
                    'total_usage': sum(tool.usage_count for tool in category_tools),
                    'avg_success_rate': sum(tool.success_rate for tool in category_tools) / len(category_tools)
                }
        
        # 상위 도구 (사용량 기준)
        all_tools = list(self.tools.values())
        all_tools.sort(key=lambda x: x.usage_count, reverse=True)
        stats['top_tools'] = [
            {'name': tool.name, 'usage': tool.usage_count, 'success_rate': tool.success_rate}
            for tool in all_tools[:10]
        ]
        
        # 성능이 낮은 도구
        low_performance = [tool for tool in all_tools if tool.usage_count > 5 and tool.success_rate < 0.5]
        stats['low_performance_tools'] = [
            {'name': tool.name, 'usage': tool.usage_count, 'success_rate': tool.success_rate}
            for tool in low_performance
        ]
        
        return stats
    
    def export_stats(self, filepath: str):
        """통계를 파일로 내보내기"""
        stats = self.get_tool_stats()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        logger.info(f"도구 통계를 {filepath}에 저장했습니다")
    
    def get_tools_summary(self) -> str:
        """도구 요약 정보 반환"""
        if not self.tools:
            return "등록된 도구가 없습니다."
        
        summary = [f"📊 총 {len(self.tools)}개 도구 등록됨\n"]
        
        for category in ToolCategory:
            category_tools = self.get_tools_by_category(category)
            if category_tools:
                summary.append(f"📦 {category.value.upper()}: {len(category_tools)}개")
                
                # 상위 3개 도구만 표시
                top_tools = sorted(category_tools, key=lambda x: x.usage_count, reverse=True)[:3]
                for tool in top_tools:
                    usage_info = f" (사용: {tool.usage_count}회)" if tool.usage_count > 0 else ""
                    summary.append(f"  🔧 {tool.name.split('_')[1]}: {tool.description[:50]}...{usage_info}")
                
                if len(category_tools) > 3:
                    summary.append(f"  ... 및 {len(category_tools) - 3}개 더")
                summary.append("")
        
        return "\n".join(summary)


# 전역 도구 매니저
tool_manager = ToolManager()