from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
import requests
import base64
import logging

logger = logging.getLogger(__name__)


class PollinationsLLM:
    """Pollinations API 클라이언트 - 이미지 생성 전용"""
    
    def __init__(self, api_key: str = None, model_name: str = "pollinations"):
        self.api_key = api_key  # Pollinations는 API 키 불필요
        self.model_name = model_name
        self.base_url = "https://image.pollinations.ai/prompt"
    
    def generate_image(self, prompt: str, **kwargs) -> str:
        """이미지 생성 및 URL 반환"""
        try:
            # 프롬프트 정리 - 메시지 형식이면 내용만 추출
            clean_prompt = self._extract_clean_prompt(prompt)
            
            # URL 인코딩된 프롬프트로 이미지 생성
            import urllib.parse
            encoded_prompt = urllib.parse.quote(clean_prompt)
            image_url = f"{self.base_url}/{encoded_prompt}"
            
            # 옵션 파라미터 추가
            params = []
            if kwargs.get('width'):
                params.append(f"width={kwargs['width']}")
            if kwargs.get('height'):
                params.append(f"height={kwargs['height']}")
            if kwargs.get('seed'):
                params.append(f"seed={kwargs['seed']}")
            
            if params:
                image_url += "?" + "&".join(params)
            
            logger.info(f"Pollinations 이미지 생성: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Pollinations 이미지 생성 실패: {e}")
            raise
    
    def _extract_clean_prompt(self, prompt: str) -> str:
        """깨끗한 프롬프트 추출"""
        # 메시지 형식인지 확인
        if '[SystemMessage(' in prompt or 'HumanMessage(' in prompt:
            # 마지막 HumanMessage에서 content 추출
            import re
            matches = re.findall(r"HumanMessage\(content='([^']+)'", prompt)
            if matches:
                return matches[-1]  # 마지막 사용자 메시지
        
        # 일반 텍스트면 그대로 반환
        return prompt[:100]  # 최대 100자로 제한
    
    def generate_image_data(self, prompt: str, **kwargs) -> bytes:
        """이미지 생성 및 바이너리 데이터 반환"""
        try:
            image_url = self.generate_image(prompt, **kwargs)
            
            # 이미지 다운로드
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Pollinations 이미지 데이터 생성 실패: {e}")
            raise
    
    def _call(self, prompt: str, **kwargs) -> str:
        """LangChain 호환성을 위한 메서드"""
        return self.generate_image(prompt, **kwargs)
    
    def invoke(self, input_data, **kwargs) -> str:
        """LangChain v0.1+ 호환성을 위한 invoke 메서드"""
        if isinstance(input_data, str):
            return self.generate_image(input_data, **kwargs)
        elif hasattr(input_data, 'content'):
            return self.generate_image(input_data.content, **kwargs)
        else:
            return self.generate_image(str(input_data), **kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "pollinations"


class PollinationsStrategy(BaseModelStrategy):
    """Pollinations 이미지 생성 전략"""
    
    def create_llm(self):
        """Pollinations LLM 생성"""
        return PollinationsLLM(self.api_key, self.model_name)
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """메시지 형식 생성 - 다른 모델과 동일한 패턴"""
        messages = []
        
        # 시스템 프롬프트 (간단한 이미지 생성 안내)
        if system_prompt:
            messages.append(SystemMessage(content="Generate images based on user descriptions."))
        
        # 대화 히스토리 추가 (다른 모델과 동일한 패턴)
        if conversation_history:
            for msg in conversation_history:
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
        """이미지 입력 처리 - Pollinations는 텍스트만 처리"""
        import re
        cleaned_input = re.sub(r'\[IMAGE_BASE64\].*?\[/IMAGE_BASE64\]', '', user_input, flags=re.DOTALL)
        return HumanMessage(content=cleaned_input.strip() or "이미지 기반 프롬프트를 텍스트로 변환해주세요.")
    
    def should_use_tools(self, user_input: str) -> bool:
        """도구 사용 여부 결정 - AI가 컨텍스트로 이미지 생성 요청 감지"""
        return self._is_image_generation_request(user_input)
    
    def create_agent_executor(self, tools: List) -> Optional[object]:
        """에이전트 실행기 생성 - Pollinations는 직접 처리"""
        return None
    
    def generate_image_response(self, user_input: str) -> str:
        """이미지 생성 및 응답 생성"""
        try:
            # 프롬프트 추출 및 정리
            prompt = self._extract_image_prompt(user_input)
            
            # 빈 프롬프트 방지
            if not prompt or len(prompt.strip()) < 3:
                prompt = "beautiful artwork"
            
            logger.info(f"Pollination 이미지 생성 프롬프트: {prompt}")
            
            # 이미지 생성
            image_url = self.llm.generate_image(prompt)
            
            # 이미지 URL을 직접 포함하여 렌더링되도록 수정
            response = f"""🎨 **이미지가 생성되었습니다!**

**프롬프트**: {prompt}

{image_url}

이미지를 클릭하면 원본 크기로 볼 수 있습니다."""
            
            return response
            
        except Exception as e:
            logger.error(f"이미지 생성 응답 오류: {e}")
            return f"이미지 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _extract_image_prompt(self, user_input: str) -> str:
        """사용자 입력에서 이미지 프롬프트 추출 및 영어 번역"""
        # AI를 통한 프롬프트 추출 및 번역
        return self._ai_extract_and_translate_prompt(user_input)
    
    def _contains_korean(self, text: str) -> bool:
        """텍스트에 한글이 포함되어 있는지 확인"""
        import re
        return bool(re.search(r'[가-힣]', text))
    
    def _is_image_generation_request(self, user_input: str) -> bool:
        """이미지 생성 요청 감지 - 패턴 매칭 기반"""
        # 한글 이미지 생성 키워드
        korean_keywords = [
            '그림', '이미지', '사진', '그려', '만들어', '생성', '디자인',
            '스케치', '일러스트', '아트', '작품', '캐릭터', '풍경',
            '초상화', '포스터', '로고', '아이콘'
        ]
        
        # 영어 이미지 생성 키워드
        english_keywords = [
            'image', 'picture', 'draw', 'create', 'generate', 'design',
            'sketch', 'illustration', 'art', 'artwork', 'character', 'landscape',
            'portrait', 'poster', 'logo', 'icon', 'paint', 'render'
        ]
        
        # 이미지 생성 동사
        action_words = [
            '그려줘', '만들어줘', '생성해줘', '디자인해줘', '그려봐',
            'draw me', 'create me', 'generate me', 'make me', 'design me'
        ]
        
        user_lower = user_input.lower()
        
        # 키워드 매칭
        has_keyword = any(word in user_lower for word in korean_keywords + english_keywords)
        has_action = any(word in user_lower for word in action_words)
        
        # 이미지 생성 요청으로 판단되는 조건
        return has_keyword or has_action
    
    def _ai_extract_and_translate_prompt(self, user_input: str) -> str:
        """AI를 통한 프롬프트 추출 및 번역"""
        try:
            # 먼저 간단한 정리
            cleaned_input = self._clean_user_input(user_input)
            
            # Google Translate API 시도
            if self._contains_korean(cleaned_input):
                translated = self._translate_with_google_api(cleaned_input)
                if translated and not self._contains_korean(translated):
                    return self._enhance_for_image_generation(translated)
            
            # 이미 영어면 그대로 사용
            return self._enhance_for_image_generation(cleaned_input)
            
        except Exception as e:
            logger.warning(f"AI 프롬프트 추출 실패: {e}")
            return self._fallback_prompt_extraction(user_input)
    
    def _translate_with_google_api(self, korean_text: str) -> str:
        """Google Translate API를 통한 실시간 번역"""
        try:
            from urllib.parse import quote
            
            encoded_text = quote(korean_text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=ko&tl=en&dt=t&q={encoded_text}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated = result[0][0][0]
                    if translated and len(translated.strip()) > 0:
                        return translated.strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Google API 번역 오류: {e}")
            return None
    
    def _enhance_for_image_generation(self, prompt: str) -> str:
        """이미지 생성에 최적화된 프롬프트로 향상"""
        # 기본 품질 키워드가 없으면 추가
        if not any(word in prompt.lower() for word in ['detailed', 'high quality', 'beautiful']):
            prompt = f"detailed, high quality {prompt}"
        
        return prompt.strip()
    
    def _clean_user_input(self, user_input: str) -> str:
        """사용자 입력 정리"""
        import re
        
        # 명령어 제거
        cleaned = re.sub(r'(그림|이미지|사진|그려|만들어|생성|draw|create|generate|image|picture)', '', user_input, flags=re.IGNORECASE)
        cleaned = re.sub(r'[을를이가은는의에서와과줘요해]', '', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _fallback_prompt_extraction(self, user_input: str) -> str:
        """폴백 프롬프트 추출"""
        cleaned = self._clean_user_input(user_input)
        return cleaned if cleaned else "beautiful artwork"
    
    def get_pollinations_system_prompt(self) -> str:
        """Pollinations 전용 시스템 프롬프트"""
        return prompt_manager.get_system_prompt(ModelType.COMMON.value, use_tools=False)
    
    def supports_streaming(self) -> bool:
        """Pollinations는 스트리밍 미지원"""
        return False