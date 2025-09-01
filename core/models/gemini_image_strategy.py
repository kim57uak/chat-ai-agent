"""Gemini 이미지 생성 전략"""

from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain.agents import AgentExecutor
from .base_model_strategy import BaseModelStrategy
from core.llm.google.gemini_image_llm import GeminiImageLLM
from ui.prompts import prompt_manager, ModelType
import logging
import re

logger = logging.getLogger(__name__)


class GeminiImageStrategy(BaseModelStrategy):
    """Gemini 이미지 생성 전략"""
    
    def create_llm(self):
        """Gemini 이미지 생성 LLM 생성"""
        return GeminiImageLLM(
            api_key=self.api_key,
            model_name=self.model_name,
            timeout=60
        )
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """이미지 생성용 메시지 생성"""
        messages = []
        
        # 시스템 프롬프트
        if system_prompt:
            enhanced_prompt = "Generate high-quality images based on user descriptions."
        else:
            enhanced_prompt = "Create detailed, high-quality images from text descriptions."
        
        messages.append(SystemMessage(content=enhanced_prompt))
        
        # 대화 히스토리 (이미지 생성에서는 제한적으로 사용)
        if conversation_history:
            for msg in conversation_history[-2:]:  # 최근 2개만
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user" and content.strip():
                    messages.append(HumanMessage(content=content))
                elif role in ["assistant", "agent"] and content.strip():
                    messages.append(AIMessage(content=content))
        
        # 현재 사용자 입력
        messages.append(HumanMessage(content=user_input))
        return messages
    
    def process_image_input(self, user_input: str) -> BaseMessage:
        """이미지 입력 처리 - 텍스트만 사용"""
        cleaned_input = re.sub(r'\[IMAGE_BASE64\].*?\[/IMAGE_BASE64\]', '', user_input, flags=re.DOTALL)
        return HumanMessage(content=cleaned_input.strip() or "Create a beautiful image")
    
    def should_use_tools(self, user_input: str, force_agent: bool = False) -> bool:
        """이미지 생성 요청인지 판단"""
        return self._is_image_generation_request(user_input)
    
    def _is_image_generation_request(self, user_input: str) -> bool:
        """이미지 생성 요청 감지"""
        korean_keywords = [
            '그림', '이미지', '사진', '그려', '만들어', '생성', '디자인',
            '스케치', '일러스트', '아트', '작품', '캐릭터', '풍경'
        ]
        
        english_keywords = [
            'image', 'picture', 'draw', 'create', 'generate', 'design',
            'sketch', 'illustration', 'art', 'artwork', 'character', 'landscape'
        ]
        
        user_lower = user_input.lower()
        return any(word in user_lower for word in korean_keywords + english_keywords)
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """이미지 생성은 에이전트 불필요"""
        return None
    
    def generate_response(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """이미지 생성 응답"""
        try:
            prompt = self._extract_image_prompt(user_input)
            logger.info(f"Gemini 이미지 생성 프롬프트: {prompt}")
            
            image_data = self.llm.generate_image(prompt)
            
            return f"""🎨 **Gemini 이미지가 생성되었습니다!**

**모델**: {self.llm.model_name}
**프롬프트**: {prompt}

{image_data}

이미지를 클릭하면 원본 크기로 볼 수 있습니다."""
            
        except Exception as e:
            logger.error(f"Gemini 이미지 생성 오류: {e}")
            return f"⚠️ **이미지 생성 실패**: {str(e)}"
    
    def _extract_image_prompt(self, user_input: str) -> str:
        """이미지 프롬프트 추출 및 영어 번역"""
        cleaned = self._clean_user_input(user_input)
        
        if self._contains_korean(cleaned):
            translated = self._translate_to_english(cleaned)
            if translated:
                return self._enhance_for_image_generation(translated)
        
        return self._enhance_for_image_generation(cleaned)
    
    def _clean_user_input(self, user_input: str) -> str:
        """사용자 입력 정리"""
        cleaned = re.sub(r'(그림|이미지|사진|그려|만들어|생성|draw|create|generate|image|picture)', '', user_input, flags=re.IGNORECASE)
        cleaned = re.sub(r'[을를이가은는의에서와과줘요해]', '', cleaned)
        return cleaned.strip()
    
    def _contains_korean(self, text: str) -> bool:
        """한글 포함 여부 확인"""
        return bool(re.search(r'[가-힣]', text))
    
    def _translate_to_english(self, korean_text: str) -> str:
        """간단한 번역 (Google Translate API 사용)"""
        try:
            import requests
            from urllib.parse import quote
            
            encoded_text = quote(korean_text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ko&tl=en&dt=t&q={encoded_text}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    return result[0][0][0].strip()
            
            return korean_text
            
        except Exception as e:
            logger.warning(f"번역 실패: {e}")
            return korean_text
    
    def _enhance_for_image_generation(self, prompt: str) -> str:
        """이미지 생성 최적화"""
        if not any(word in prompt.lower() for word in ['detailed', 'high quality', 'beautiful']):
            prompt = f"detailed, high quality {prompt}"
        
        return prompt.strip()
    
    def supports_streaming(self) -> bool:
        """스트리밍 미지원"""
        return False