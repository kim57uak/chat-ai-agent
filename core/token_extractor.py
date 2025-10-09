"""AI 응답에서 토큰 사용량 추출 유틸리티"""

from core.logging import get_logger
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = get_logger("token_extractor")


@dataclass
class TokenUsage:
    """토큰 사용량 정보"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    
    def __add__(self, other):
        """토큰 사용량 누적"""
        if not isinstance(other, TokenUsage):
            return self
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            model=self.model or other.model
        )
    
    def __format__(self, format_spec):
        """포맷 지원"""
        if format_spec == '':
            return str(self.total_tokens)
        elif format_spec == ',d' or format_spec == ',':
            return f"{self.total_tokens:,}"
        else:
            return str(self.total_tokens)


class TokenExtractor:
    """다양한 AI 모델 응답에서 토큰 사용량 추출"""
    
    @staticmethod
    def extract_from_response(response: Any, model_name: str = "") -> Optional[TokenUsage]:
        """응답 객체에서 토큰 사용량 추출"""
        try:
            # LangChain AIMessage 객체
            if hasattr(response, 'response_metadata'):
                return TokenExtractor._extract_from_langchain(response, model_name)
            
            # OpenAI 직접 응답
            elif hasattr(response, 'usage'):
                return TokenExtractor._extract_from_openai(response, model_name)
            
            # 딕셔너리 형태 응답
            elif isinstance(response, dict):
                return TokenExtractor._extract_from_dict(response, model_name)
            
            # 문자열 응답 (토큰 정보 없음)
            elif isinstance(response, str):
                logger.debug(f"문자열 응답 - 토큰 정보 없음: {model_name}")
                return None
            
            else:
                logger.debug(f"알 수 없는 응답 타입: {type(response)} - {model_name}")
                return None
                
        except Exception as e:
            logger.error(f"토큰 추출 오류 ({model_name}): {e}")
            return None
    
    @staticmethod
    def _extract_from_langchain(response, model_name: str) -> Optional[TokenUsage]:
        """LangChain 응답에서 토큰 추출"""
        try:
            metadata = response.response_metadata
            
            # OpenAI 스타일
            if 'token_usage' in metadata:
                usage = metadata['token_usage']
                return TokenUsage(
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0),
                    model=model_name
                )
            
            # Google/Gemini 스타일
            elif 'usage_metadata' in metadata:
                usage = metadata['usage_metadata']
                return TokenUsage(
                    prompt_tokens=usage.get('prompt_token_count', 0),
                    completion_tokens=usage.get('candidates_token_count', 0),
                    total_tokens=usage.get('total_token_count', 0),
                    model=model_name
                )
            
            # Anthropic/Claude 스타일
            elif 'usage' in metadata:
                usage = metadata['usage']
                return TokenUsage(
                    prompt_tokens=usage.get('input_tokens', 0),
                    completion_tokens=usage.get('output_tokens', 0),
                    total_tokens=usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
                    model=model_name
                )
            
            logger.debug(f"LangChain 메타데이터에서 토큰 정보 없음: {model_name}")
            return None
            
        except Exception as e:
            logger.error(f"LangChain 토큰 추출 오류: {e}")
            return None
    
    @staticmethod
    def _extract_from_openai(response, model_name: str) -> Optional[TokenUsage]:
        """OpenAI 직접 응답에서 토큰 추출"""
        try:
            usage = response.usage
            return TokenUsage(
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                model=model_name
            )
        except Exception as e:
            logger.error(f"OpenAI 토큰 추출 오류: {e}")
            return None
    
    @staticmethod
    def _extract_from_dict(response: dict, model_name: str) -> Optional[TokenUsage]:
        """딕셔너리 응답에서 토큰 추출"""
        try:
            # OpenAI API 스타일
            if 'usage' in response:
                usage = response['usage']
                return TokenUsage(
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0),
                    model=model_name
                )
            
            # Google API 스타일
            elif 'usageMetadata' in response:
                usage = response['usageMetadata']
                return TokenUsage(
                    prompt_tokens=usage.get('promptTokenCount', 0),
                    completion_tokens=usage.get('candidatesTokenCount', 0),
                    total_tokens=usage.get('totalTokenCount', 0),
                    model=model_name
                )
            
            # Anthropic API 스타일
            elif 'usage' in response:
                usage = response['usage']
                return TokenUsage(
                    prompt_tokens=usage.get('input_tokens', 0),
                    completion_tokens=usage.get('output_tokens', 0),
                    total_tokens=usage.get('input_tokens', 0) + usage.get('output_tokens', 0),
                    model=model_name
                )
            
            logger.debug(f"딕셔너리에서 토큰 정보 없음: {model_name}")
            return None
            
        except Exception as e:
            logger.error(f"딕셔너리 토큰 추출 오류: {e}")
            return None
    
    @staticmethod
    def estimate_tokens(text: str, model_name: str = "") -> TokenUsage:
        """텍스트에서 토큰 수 추정 (실제 사용량이 없을 때)"""
        try:
            # 간단한 추정: 영어는 4자당 1토큰, 한글은 2자당 1토큰
            import re
            
            # 한글 문자 수
            korean_chars = len(re.findall(r'[가-힣]', text))
            # 영어/숫자/기호 문자 수
            other_chars = len(text) - korean_chars
            
            # 추정 토큰 수
            estimated_tokens = (korean_chars // 2) + (other_chars // 4)
            estimated_tokens = max(1, estimated_tokens)  # 최소 1토큰
            
            return TokenUsage(
                prompt_tokens=0,
                completion_tokens=estimated_tokens,
                total_tokens=estimated_tokens,
                model=model_name
            )
            
        except Exception as e:
            logger.error(f"토큰 추정 오류: {e}")
            return TokenUsage(model=model_name)