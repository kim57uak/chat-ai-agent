"""범용적인 완전 출력 포맷터"""
from typing import List, Any, Dict
from .tool_result_formatter import ToolResultFormatter
from ui.prompts import prompt_manager
from core.logging import get_logger
import json
import re

logger = get_logger("complete_output_formatter")


class CompleteOutputFormatter(ToolResultFormatter):
    """다중 페이지/섹션 데이터의 완전 출력을 보장하는 범용 포맷터"""
    
    def format_tool_results(self, used_tools: List, tool_results: List, user_input: str, llm: Any = None) -> str:
        """도구 결과를 완전히 포맷팅"""
        try:
            if not tool_results:
                return None
            
            # 다중 페이지 데이터인지 확인
            if not self._has_multi_part_data(tool_results):
                return self._fallback_format(used_tools, tool_results)
            
            # 완전 출력 프롬프트 적용
            complete_prompt = prompt_manager.get_complete_output_prompt()
            
            # 결과 분석
            analysis = self._analyze_results(tool_results)
            
            format_prompt = f"""{complete_prompt}

사용자 요청: {user_input}
사용된 도구: {', '.join([getattr(tool, '__name__', str(tool)) for tool in used_tools])}

도구 실행 결과:
{self._format_results_for_prompt(tool_results)}

결과 분석:
- 총 섹션/페이지 수: {analysis.get('total_sections', 'N/A')}
- 데이터 타입: {analysis.get('data_type', 'N/A')}
- 다중 파트 여부: {analysis.get('is_multi_part', False)}

**중요**: 모든 섹션/페이지의 데이터를 빠짐없이 완전히 출력하세요."""
            
            if llm:
                from langchain.schema import HumanMessage
                messages = [HumanMessage(content=format_prompt)]
                response = llm.invoke(messages)
                return response.content
            
            return self._direct_format_results(tool_results, analysis)
            
        except Exception as e:
            logger.error(f"완전 출력 포맷팅 오류: {e}")
            return self._fallback_format(used_tools, tool_results)
    
    def _has_multi_part_data(self, tool_results: List) -> bool:
        """다중 파트 데이터인지 확인"""
        multi_part_indicators = [
            r'\d+/\d+',  # 페이지 표시 (1/7, 2/5 등)
            r'페이지\s*\d+',  # 페이지 언급
            r'page\s*\d+',  # 영어 페이지
            r'섹션\s*\d+',  # 섹션 언급
            r'section\s*\d+',  # 영어 섹션
            r'총\s*\d+.*페이지',  # 총 페이지 수
            r'total.*pages?',  # 영어 총 페이지
        ]
        
        for result in tool_results:
            result_str = str(result).lower()
            if any(re.search(pattern, result_str) for pattern in multi_part_indicators):
                return True
        
        return False
    
    def _analyze_results(self, tool_results: List) -> Dict[str, Any]:
        """결과 분석"""
        analysis = {
            'total_sections': 0,
            'data_type': 'unknown',
            'is_multi_part': False,
            'has_pagination': False
        }
        
        try:
            for result in tool_results:
                result_str = str(result)
                
                # 페이지/섹션 정보 추출
                page_matches = re.findall(r'(\d+)/(\d+)', result_str)
                if page_matches:
                    analysis['has_pagination'] = True
                    analysis['is_multi_part'] = True
                    analysis['total_sections'] = max(int(match[1]) for match in page_matches)
                
                # 데이터 타입 확인
                if result_str.strip().startswith(('{', '[')):
                    analysis['data_type'] = 'json'
                elif '<' in result_str and '>' in result_str:
                    analysis['data_type'] = 'html'
                else:
                    analysis['data_type'] = 'text'
                    
        except Exception as e:
            logger.warning(f"결과 분석 중 오류: {e}")
        
        return analysis
    
    def _format_results_for_prompt(self, tool_results: List) -> str:
        """프롬프트용 결과 포맷팅"""
        formatted_results = []
        
        for i, result in enumerate(tool_results, 1):
            result_str = str(result)
            # 긴 결과는 요약하되 완전 출력 필요성 강조
            if len(result_str) > 2000:
                result_str = result_str[:2000] + "... (결과가 길어 일부만 표시, 전체 내용을 모두 출력하세요)"
            
            formatted_results.append(f"도구 결과 {i}:\n{result_str}")
        
        return "\n\n".join(formatted_results)
    
    def _direct_format_results(self, tool_results: List, analysis: Dict) -> str:
        """직접 결과 포맷팅 (LLM 없이)"""
        output = ["# 📊 검색 결과\n"]
        
        if analysis['total_sections'] > 0:
            output.append(f"📋 **총 {analysis['total_sections']}개 섹션 결과**\n")
        
        for i, result in enumerate(tool_results, 1):
            output.append(f"## 섹션 {i}/{len(tool_results)}\n")
            output.append(str(result))
            output.append("\n---\n")
        
        output.append("✅ **모든 섹션 출력 완료**")
        
        return "\n".join(output)
    
    def _fallback_format(self, used_tools: List, tool_results: List) -> str:
        """폴백 포맷팅"""
        tool_names = [getattr(tool, '__name__', str(tool)) for tool in used_tools]
        return f"✅ 작업 완료 (사용된 도구: {', '.join(tool_names)})\n\n" + "\n\n".join([str(result) for result in tool_results])