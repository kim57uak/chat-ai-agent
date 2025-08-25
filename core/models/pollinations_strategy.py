from typing import List, Dict, Any, Optional
from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models.llms import LLM
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from .base_model_strategy import BaseModelStrategy
from ui.prompts import prompt_manager, ModelType
from core.token_logger import TokenLogger
import requests
import base64
import logging
import json

logger = logging.getLogger(__name__)


class PollinationsLLM(LLM):
    """Pollinations API 클라이언트 - 텍스트 및 이미지 생성 지원"""
    
    api_key: Optional[str] = None
    model_name: str = "pollinations"
    model_id: str = "pollinations"
    is_image_model: bool = False
    text_base_url: str = "https://text.pollinations.ai"
    image_base_url: str = "https://image.pollinations.ai/prompt"
    
    def __init__(self, api_key: str = None, model_name: str = "pollinations", **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.model_name = model_name
        self.model_id = self._extract_model_id(model_name)
        self.is_image_model = self.model_id == "image"
        self.text_base_url = "https://text.pollinations.ai"
        self.image_base_url = "https://image.pollinations.ai/prompt"
    
    def _extract_model_id(self, model_name: str) -> str:
        """모델명에서 실제 모델 ID 추출"""
        if model_name.startswith("pollinations-"):
            return model_name.replace("pollinations-", "")
        return model_name
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """텍스트 생성"""
        try:
            clean_prompt = self._extract_clean_prompt(prompt)
            
            # 기본 페이로드 (최소한의 파라미터만 사용)
            payload = {
                "messages": [
                    {"role": "user", "content": clean_prompt}
                ],
                "model": self.model_id
            }
            
            # 선택적 파라미터 추가 (모델에 따라 다르게 처리)
            if kwargs.get('seed') is not None:
                payload["seed"] = kwargs['seed']
            
            response = requests.post(
                self.text_base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.text.strip()
            logger.info(f"Pollinations 텍스트 생성 완료: {self.model_id}")
            return result
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Pollinations 타임아웃 ({self.model_id}): {e}")
            raise Exception(f"Pollinations {self.model_id} 모델 응답 시간이 초과되었습니다. 더 간단한 요청으로 다시 시도해주세요.")
        except requests.exceptions.HTTPError as e:
            if "500" in str(e):
                logger.error(f"Pollinations 서버 오류 ({self.model_id}): {e}")
                raise Exception(f"Pollinations {self.model_id} 모델이 일시적으로 사용할 수 없습니다. 다른 모델을 시도해보세요.")
            else:
                logger.error(f"Pollinations HTTP 오류 ({self.model_id}): {e}")
                raise Exception(f"Pollinations API 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Pollinations 연결 오류 ({self.model_id}): {e}")
            raise Exception(f"Pollinations 서버에 연결할 수 없습니다. 네트워크를 확인해주세요.")
        except Exception as e:
            logger.error(f"Pollinations 텍스트 생성 실패 ({self.model_id}): {e}")
            raise Exception(f"텍스트 생성 중 오류가 발생했습니다: {str(e)[:100]}")
    
    def generate_image(self, prompt: str, **kwargs) -> str:
        """이미지 생성 및 URL 반환"""
        try:
            clean_prompt = self._extract_clean_prompt(prompt)
            
            import urllib.parse
            encoded_prompt = urllib.parse.quote(clean_prompt)
            image_url = f"{self.image_base_url}/{encoded_prompt}"
            
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
            raise Exception(f"이미지 생성 중 오류가 발생했습니다: {str(e)[:100]}")
    
    def _extract_clean_prompt(self, prompt: str) -> str:
        """깨끗한 프롬프트 추출"""
        # 메시지 형식인지 확인
        if '[SystemMessage(' in prompt or 'HumanMessage(' in prompt:
            # 마지막 HumanMessage에서 content 추출
            import re
            matches = re.findall(r"HumanMessage\(content='([^']+)'", prompt)
            if matches:
                return matches[-1]  # 마지막 사용자 메시지
        
        # 일반 텍스트면 그대로 반환 (길이 제한 제거)
        return prompt.strip()
    
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
        if self.is_image_model:
            return self.generate_image(prompt, **kwargs)
        else:
            return self.generate_text(prompt, **kwargs)
    
    def invoke(self, input_data, config=None, **kwargs) -> str:
        """LangChain v0.1+ 호환성을 위한 invoke 메서드"""
        if isinstance(input_data, str):
            prompt = input_data
        elif hasattr(input_data, 'content'):
            prompt = input_data.content
        else:
            prompt = str(input_data)
        
        if self.is_image_model:
            return self.generate_image(prompt, **kwargs)
        else:
            return self.generate_text(prompt, **kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "pollinations"
    



class PollinationsStrategy(BaseModelStrategy):
    """Pollinations AI 전략 - 텍스트 및 이미지 생성 지원"""
    
    def create_llm(self):
        """Pollinations LLM 생성"""
        return PollinationsLLM(self.api_key, self.model_name)
    
    def create_messages(self, user_input: str, system_prompt: str = None, conversation_history: List[Dict] = None) -> List[BaseMessage]:
        """메시지 형식 생성 - 다른 모델과 동일한 패턴"""
        messages = []
        
        # 시스템 프롬프트 생성 (다른 모델과 동일한 패턴)
        if system_prompt:
            if self.llm.is_image_model:
                enhanced_prompt = "Generate high-quality images based on user descriptions."
            else:
                enhanced_prompt = self.enhance_prompt_with_format(system_prompt)
        else:
            enhanced_prompt = self.get_default_system_prompt()
        
        messages.append(SystemMessage(content=enhanced_prompt))
        
        # 대화 히스토리를 실제 메시지로 변환
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user" and content.strip():
                    messages.append(HumanMessage(content=content))
                elif role in ["assistant", "agent"] and content.strip():
                    messages.append(AIMessage(content=content))
        
        # 현재 사용자 입력 추가
        messages.append(HumanMessage(content=user_input))
        return messages
    
    def process_image_input(self, user_input: str) -> BaseMessage:
        """이미지 입력 처리 - Pollinations는 텍스트만 처리"""
        import re
        cleaned_input = re.sub(r'\[IMAGE_BASE64\].*?\[/IMAGE_BASE64\]', '', user_input, flags=re.DOTALL)
        
        if self.llm.is_image_model:
            return HumanMessage(content=cleaned_input.strip() or "Create a beautiful image")
        else:
            return HumanMessage(content=cleaned_input.strip() or "Please describe what you see in the image.")
    
    def should_use_tools(self, user_input: str) -> bool:
        """도구 사용 여부 결정 - 순수 AI 컨텍스트 기반 판단"""
        if self.llm.is_image_model:
            return self._is_image_generation_request(user_input)
        
        try:
            # 사용 가능한 도구 정보 수집
            available_tools_info = ""
            if hasattr(self, 'tools') and self.tools:
                try:
                    if isinstance(self.tools, list):
                        tool_names = [tool.name for tool in self.tools[:10]]
                    else:
                        tool_names = [str(tool) for tool in list(self.tools)[:10]]
                    available_tools_info = f"Available tools: {', '.join(tool_names)}"
                except Exception as e:
                    logger.warning(f"Tool names extraction failed: {e}")
                    available_tools_info = f"Available tools: {len(self.tools)} tools"
            
            # 컨텍스트 기반 판단 프롬프트
            context_prompt = f"""Analyze the user's intent and determine if external tools are needed.

User request: "{user_input}"
{available_tools_info}

Does this request require using external tools/APIs to fulfill? 
Consider the user's intent, not just keywords.

If the user wants to:
- Get information from external sources
- Search or retrieve data
- Perform actions beyond conversation
- Use specific tools or APIs
Answer: YES

If it's just:
- General conversation
- Explanations or discussions
- Questions about concepts
Answer: NO

Analyze the intent and answer: YES or NO"""

            response = self.llm.generate_text(context_prompt)
            decision = str(response).strip().upper()
            
            # 첫 번째 YES 또는 NO 찾기
            import re
            match = re.search(r'\b(YES|NO)\b', decision)
            if match:
                result = match.group(1) == "YES"
            else:
                # YES가 NO보다 먼저 나오면 True
                yes_pos = decision.find("YES")
                no_pos = decision.find("NO")
                if yes_pos != -1 and (no_pos == -1 or yes_pos < no_pos):
                    result = True
                else:
                    result = False
            
            decision_str = str(decision)
            logger.info(f"Pollinations 컨텍스트 기반 판단: '{user_input}' -> {decision_str[:100]} -> {result}")
            return result

        except Exception as e:
            logger.error(f"Pollinations tool usage decision error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_agent_executor(self, tools: List) -> Optional[AgentExecutor]:
        """에이전트 실행기 생성 - Pollinations 전용 파싱 오류 처리"""
        if self.llm.is_image_model or not tools:
            return None
        
        # 중앙관리 시스템에서 에이전트 시스템 프롬프트 가져오기
        system_message = prompt_manager.get_agent_system_prompt(ModelType.POLLINATIONS.value)
        
        # ReAct 프롬프트 템플릿
        react_template = prompt_manager.get_react_template(ModelType.POLLINATIONS.value)
        if not react_template:
            react_template = prompt_manager.get_prompt(ModelType.COMMON.value, "react_format")
        
        react_prompt = PromptTemplate.from_template(react_template)
        
        agent = create_react_agent(self.llm, tools, react_prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            max_execution_time=60,
            early_stopping_method="force",
            handle_parsing_errors=self._handle_parsing_errors,  # 커스텀 파싱 오류 처리
            return_intermediate_steps=True,
        )
    
    def _handle_parsing_errors(self, error) -> str:
        """Pollinations 전용 파싱 오류 처리 - 한글 지원"""
        error_str = str(error)
        logger.warning(f"Pollinations 파싱 오류: {error_str}")
        
        # 일반적인 파싱 오류 패턴 처리 - 한글로 응답
        if "Missing 'Action:'" in error_str:
            return "Thought: 적절한 응답 형식을 제공해야 합니다.\nFinal Answer: 요청을 이해했습니다. 사용 가능한 정보를 바탕으로 직접적인 답변을 드리겠습니다."
        elif "Invalid Format" in error_str:
            return "Thought: 올바른 형식을 따라야 합니다.\nFinal Answer: 질문에 대한 포괄적인 답변을 드리겠습니다."
        else:
            return "Thought: 형식 문제가 있었습니다.\nFinal Answer: 도움이 되는 답변을 드리겠습니다."
    
    def generate_response(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """응답 생성 - 이미지 또는 텍스트"""
        try:
            if self.llm.is_image_model:
                return self._generate_image_response(user_input)
            else:
                return self._generate_text_response(user_input, conversation_history)
        except Exception as e:
            logger.error(f"Pollinations 응답 생성 오류 ({self.llm.model_id}): {e}")
            
            # 사용자 친화적 오류 메시지
            if "timeout" in str(e).lower() or "timed out" in str(e).lower():
                return f"⏰ **{self.llm.model_id} 모델 응답 시간 초과**\n\n요청이 너무 복잡하거나 서버가 바쁘습니다.\n\n**해결 방법:**\n• 더 간단한 질문으로 나눠서 요청\n• 다른 Pollinations 모델 사용 (`pollinations-llama-roblox`)\n• 잠시 후 다시 시도\n\n예: '동남아 여행 상품 찾아줘' → '태국 여행 상품 찾아줘'"
            elif "500" in str(e) or "Internal Server Error" in str(e):
                return f"🚨 **{self.llm.model_id} 모델 일시 오류**\n\n현재 이 모델이 불안정합니다. 다른 Pollinations 모델을 시도해보세요:\n\n• `pollinations-llama-roblox` (추천)\n• `pollinations-mistral`\n• `pollinations-openai`\n\n또는 잠시 후 다시 시도해주세요."
            else:
                return f"⚠️ **오류 발생**: {str(e)[:200]}..."
    
    def _generate_image_response(self, user_input: str) -> str:
        """이미지 생성 및 응답 생성"""
        prompt = self._extract_image_prompt(user_input)
        if not prompt or len(prompt.strip()) < 3:
            prompt = "beautiful artwork"
        
        logger.info(f"Pollinations 이미지 생성 프롬프트: {prompt}")
        image_url = self.llm.generate_image(prompt)
        
        return f"""🎨 **이미지가 생성되었습니다!**

**모델**: {self.llm.model_id}
**프롬프트**: {prompt}

{image_url}

이미지를 클릭하면 원본 크기로 볼 수 있습니다."""
    
    def _generate_text_response(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """텍스트 응답 생성 - ReAct 형식 강제"""
        logger.info(f"Pollinations 텍스트 생성: {self.llm.model_id}")
        
        # 언어 감지 및 강화된 시스템 프롬프트
        is_korean = self._contains_korean(user_input)
        language_instruction = "한글로 응답하세요. 모든 답변은 반드시 한국어로 작성해야 합니다." if is_korean else "Respond in English."
        
        system_prompt = (
            f"LANGUAGE RULE: {language_instruction}\n\n"
            "You MUST follow this EXACT format for ALL responses:\n\n"
            "If you need to use tools:\n"
            "Thought: [your reasoning]\n"
            "Action: [exact_tool_name]\n"
            "Action Input: {{\"param\": \"value\"}}\n"
            "\n"
            "If you don't need tools or after getting tool results:\n"
            "Thought: [your reasoning]\n"
            "Final Answer: [your complete response]\n\n"
            "CRITICAL: NEVER output text without starting with 'Thought:' first.\n"
            "CRITICAL: After 'Thought:' you MUST use either 'Action:' or 'Final Answer:'.\n"
            f"CRITICAL: ALL text including Thought and Final Answer MUST be in {'Korean (한국어)' if is_korean else 'English'}."
        )
        
        # 대화 히스토리를 포함한 전체 프롬프트 구성
        full_prompt = system_prompt
        
        # 대화 히스토리 추가
        if conversation_history:
            full_prompt += "\n\nPrevious conversation:\n"
            for msg in conversation_history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user" and content.strip():
                    full_prompt += f"User: {content}\n"
                elif role in ["assistant", "agent"] and content.strip():
                    full_prompt += f"Assistant: {content}\n"
        
        # 현재 사용자 입력 추가
        language_reminder = "한국어로 답변" if is_korean else "in English"
        full_prompt += f"\n\nCurrent request: {user_input}\n\nYour response (MUST start with 'Thought:' and be {language_reminder}):"
        
        response = self.llm.generate_text(full_prompt)
        
        # 응답 형식 검증 및 수정
        if not response.strip().startswith("Thought:"):
            logger.warning(f"Pollinations 응답 형식 오류, 수정 중: {response[:100]}")
            if is_korean:
                response = f"Thought: 도움이 되는 응답을 제공해야 합니다.\nFinal Answer: {response}"
            else:
                response = f"Thought: I need to provide a helpful response.\nFinal Answer: {response}"
        
        return response
    
    def _extract_image_prompt(self, user_input: str) -> str:
        """사용자 입력에서 이미지 프롬프트 추출 및 영어 번역"""
        cleaned = self._clean_user_input(user_input)
        
        if self._contains_korean(cleaned):
            translated = self._translate_with_google_api(cleaned)
            if translated and not self._contains_korean(translated):
                return self._enhance_for_image_generation(translated)
        
        return self._enhance_for_image_generation(cleaned)
    
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
        if self.llm.is_image_model:
            return "Generate images based on user descriptions. Focus on creating detailed, high-quality visual content."
        else:
            base_prompt = prompt_manager.get_system_prompt(ModelType.COMMON.value, use_tools=False)
            return base_prompt + "\n\nCRITICAL: ALWAYS respond in the SAME language as the user's input. Korean input = Korean response (한글 입력 = 한글 응답)."
    
    def supports_streaming(self) -> bool:
        """Pollinations는 스트리밍 미지원"""
        return False