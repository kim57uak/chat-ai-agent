from core.ai_agent import AIAgent
import logging

logger = logging.getLogger(__name__)

class AIClient:
    """AI 클라이언트 - 에이전트 기반 채팅"""
    
    def __init__(self, api_key, model_name='gpt-3.5-turbo'):
        self.api_key = api_key
        self.model_name = model_name
        self.agent = AIAgent(api_key, model_name)
        self.conversation_history = []  # 대화 기록 저장
        
        # 설정 파일에서 대화 기록 설정 로드
        from core.file_utils import load_config
        config = load_config()
        conv_settings = config.get('conversation_settings', {})
        
        self.max_history_pairs = conv_settings.get('max_history_pairs', 5)
        self.max_tokens_estimate = conv_settings.get('max_tokens_estimate', 2000)
        self.enable_history = conv_settings.get('enable_history', True)
        self.token_optimization = conv_settings.get('token_optimization', True)
        
        # 유저 프롬프트 설정
        self.user_prompt = self._load_user_prompt()
    
    def chat(self, messages):
        """토큰 최적화된 대화 기록 사용 (할당량 초과 시 청크 분할) - 안정성 개선"""
        try:
            # 입력 검증
            if not messages or not isinstance(messages, list):
                return "유효하지 않은 메시지 형식입니다."
            
            # 마지막 사용자 메시지 추출
            user_message = ""
            for msg in reversed(messages):
                if isinstance(msg, dict) and msg.get('role') == 'user':
                    user_message = msg.get('content', '').strip()
                    if user_message:
                        break
            
            # 유저 프롬프트 추가
            user_prompt = self.get_current_user_prompt()
            print(f"[디버그] 현재 모델: {self.model_name}")
            print(f"[디버그] 유저 프롬프트: {user_prompt}")
            if user_prompt and user_message:
                # 사용자 메시지에 프롬프트 추가
                enhanced_message = f"{user_prompt}\n\n{user_message}"
                # 마지막 사용자 메시지 업데이트
                for i in range(len(messages)-1, -1, -1):
                    if messages[i].get('role') == 'user':
                        messages[i]['content'] = enhanced_message
                        break
                print(f"[디버그] 유저 프롬프트 추가됨")
            
            # 요청 파라미터 로깅
            print(f"[로깅] 요청 파라미터:")
            print(f"  - 모델: {self.model_name}")
            print(f"  - 메시지 수: {len(messages)}")
            for i, msg in enumerate(messages):
                content_preview = msg.get('content', '')[:100] + '...' if len(msg.get('content', '')) > 100 else msg.get('content', '')
                print(f"  - [{i}] {msg.get('role', 'unknown')}: {content_preview}")
            
            if not user_message:
                return "처리할 메시지를 찾을 수 없습니다."
            
            logger.info(f"채팅 요청 처리 시작: {user_message[:50]}...")
            
            # 대화 기록 사용 여부 확인
            if not self.enable_history:
                return self._process_with_quota_handling(user_message, [])
            
            # 대화 기록 업데이트 및 최적화
            self.conversation_history = [msg for msg in messages if isinstance(msg, dict)]
            optimized_history = self._optimize_conversation_history() if self.token_optimization else self.conversation_history.copy()
            
            return self._process_with_quota_handling(user_message, optimized_history)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI 클라이언트 채팅 오류: {error_msg}")
            return f"채팅 처리 중 오류가 발생했습니다: {error_msg[:100]}..."
    
    def _process_with_quota_handling(self, user_message: str, history: list):
        """할당량 초과 시 청크 분할 처리 - 단순화"""
        import time
        
        try:
            start_time = time.time()
            logger.info(f"AI 요청 시작: {self.model_name} (히스토리: {len(history)}개)")
            
            response, used_tools = self.agent.process_message_with_history(user_message, history)
            
            elapsed_time = time.time() - start_time
            
            if used_tools:
                logger.info(f"도구 사용 응답 완료: {self.model_name} ({elapsed_time:.1f}초)")
            else:
                logger.info(f"일반 채팅 응답 완료: {self.model_name} ({elapsed_time:.1f}초)")
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # 할당량 초과 오류 감지
            if "429" in error_msg and "quota" in error_msg.lower():
                logger.warning(f"할당량 초과 감지, 청크 분할 처리 시도: {self.model_name}")
                return self._handle_quota_exceeded(user_message, history)
            
            # 연결 오류 감지
            elif any(keyword in error_msg.lower() for keyword in ['connection', 'timeout', 'network']):
                logger.error(f"네트워크 오류: {self.model_name} - {error_msg}")
                return "네트워크 연결에 문제가 있습니다. 잠시 후 다시 시도해주세요."
            
            else:
                logger.error(f"AI 클라이언트 오류: {self.model_name} - {error_msg}")
                raise e
    
    def _handle_quota_exceeded(self, user_message: str, history: list):
        """할당량 초과 시 청크 분할 처리"""
        # 긴 메시지를 청크로 분할
        if len(user_message) > 1000:
            chunks = self._split_message_into_chunks(user_message, 800)
            responses = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # 각 청크를 간단한 히스토리로 처리
                    simple_history = history[-2:] if history else []  # 최근 2개만
                    chunk_response, _ = self.agent.process_message_with_history(
                        f"[{i+1}/{len(chunks)}] {chunk}", simple_history
                    )
                    responses.append(chunk_response)
                    
                except Exception as chunk_error:
                    logger.error(f"청크 {i+1} 처리 오류: {chunk_error}")
                    responses.append(f"[청크 {i+1} 처리 실패: {str(chunk_error)[:100]}...]")
            
            return "\n\n".join(responses)
        
        else:
            # 짧은 메시지는 히스토리 없이 처리
            try:
                response, _ = self.agent.process_message(user_message)
                logger.info(f"할당량 초과로 히스토리 없이 처리: {self.model_name}")
                return response
            except Exception as fallback_error:
                return f"할당량 초과 및 대체 처리 실패: {str(fallback_error)[:200]}..."
    
    def _split_message_into_chunks(self, message: str, chunk_size: int = 800):
        """메시지를 청크로 분할"""
        if len(message) <= chunk_size:
            return [message]
        
        chunks = []
        sentences = message.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def agent_chat(self, user_input: str):
        """에이전트 채팅 (할당량 초과 시 청크 분할) - 안정성 개선"""
        try:
            # 입력 검증
            if not user_input or not isinstance(user_input, str):
                return "유효하지 않은 입력입니다."
            
            user_input = user_input.strip()
            if not user_input:
                return "빈 메시지는 처리할 수 없습니다."
            
            logger.info(f"에이전트 채팅 요청: {user_input[:50]}...")
            
            optimized_history = self._optimize_conversation_history()
            return self._process_with_quota_handling(user_input, optimized_history)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"에이전트 채팅 오류: {error_msg}")
            return f"에이전트 채팅 처리 중 오류가 발생했습니다: {error_msg[:100]}..."
    
    def simple_chat(self, user_input: str):
        """단순 채팅 (도구 사용 안함)"""
        try:
            optimized_history = self._optimize_conversation_history()
            return self.agent.simple_chat_with_history(user_input, optimized_history)
        except Exception as e:
            logger.error(f"단순 채팅 오류: {e}")
            return f"오류: {e}"
    
    def _optimize_conversation_history(self):
        """대화 기록 최적화 - 토큰 사용량 절약"""
        if not self.conversation_history:
            return []
        
        # 1. 최근 N개 대화 쌍만 유지
        if len(self.conversation_history) > self.max_history_pairs * 2:
            # 마지막 메시지는 항상 유지
            recent_history = self.conversation_history[-(self.max_history_pairs * 2):]
        else:
            recent_history = self.conversation_history.copy()
        
        # 2. 토큰 수 추정 및 제한
        optimized_history = self._limit_by_tokens(recent_history)
        
        return optimized_history
    
    def _estimate_tokens(self, text: str) -> int:
        """토큰 수 대략 추정 (한글 1자 = 1.5토큰, 영어 1단어 = 1.3토큰)"""
        if not text:
            return 0
        
        # 한글과 영어 분리 계산
        korean_chars = sum(1 for c in text if ord(c) >= 0xAC00 and ord(c) <= 0xD7A3)
        english_words = len([w for w in text.split() if w.isascii()])
        other_chars = len(text) - korean_chars
        
        estimated_tokens = int(korean_chars * 1.5 + english_words * 1.3 + other_chars * 0.8)
        return max(estimated_tokens, len(text) // 4)  # 최소값 보장
    
    def _limit_by_tokens(self, history: list) -> list:
        """토큰 수 기반으로 대화 기록 제한"""
        if not history:
            return []
        
        total_tokens = 0
        limited_history = []
        
        # 마지막부터 역순으로 처리
        for msg in reversed(history):
            content = msg.get('content', '')
            msg_tokens = self._estimate_tokens(content)
            
            if total_tokens + msg_tokens > self.max_tokens_estimate:
                break
            
            limited_history.insert(0, msg)
            total_tokens += msg_tokens
        
        logger.info(f"대화 기록 최적화: {len(history)}개 -> {len(limited_history)}개 (예상 토큰: {total_tokens})")
        return limited_history
    
    def _load_user_prompt(self):
        """유저 프롬프트 로드"""
        try:
            from core.file_utils import load_config
            config = load_config()
            user_prompts = config.get('user_prompt', {
                'gpt': '다음 규칙을 따라 답변해주세요: 1. 구조화된 답변 2. 가독성 우선 3. 명확한 분류 4. 핵심 요약 5. 한국어 사용',
                'gemini': '다음 규칙을 따라 답변해주세요: 1. 구조화된 답변 2. 가독성 우선 3. 명확한 분류 4. 핵심 요약 5. 한국어 사용'
            })
            print(f"[디버그] 로드된 유저 프롬프트: {user_prompts}")
            return user_prompts
        except Exception as e:
            print(f"[디버그] 유저 프롬프트 로드 오류: {e}")
            return {
                'gpt': '다음 규칙을 따라 답변해주세요: 1. 구조화된 답변 2. 가독성 우선 3. 명확한 분류 4. 핵심 요약 5. 한국어 사용',
                'gemini': '다음 규칙을 따라 답변해주세요: 1. 구조화된 답변 2. 가독성 우선 3. 명확한 분류 4. 핵심 요약 5. 한국어 사용'
            }
    
    def get_current_user_prompt(self):
        """현재 모델에 맞는 유저 프롬프트 반환"""
        if 'gemini' in self.model_name.lower():
            return self.user_prompt.get('gemini', '')
        else:
            return self.user_prompt.get('gpt', '')
    
    def update_user_prompt(self, prompt_text, model_type='both'):
        """유저 프롬프트 업데이트"""
        if model_type == 'both':
            self.user_prompt['gpt'] = prompt_text
            self.user_prompt['gemini'] = prompt_text
        elif model_type == 'gpt':
            self.user_prompt['gpt'] = prompt_text
        elif model_type == 'gemini':
            self.user_prompt['gemini'] = prompt_text
        
        # 설정 파일에 저장
        self._save_user_prompt()
    
    def _save_user_prompt(self):
        """유저 프롬프트 저장"""
        try:
            from core.file_utils import load_config, save_config
            config = load_config()
            config['user_prompt'] = self.user_prompt
            save_config(config)
            logger.info(f"유저 프롬프트 저장 완료: {self.user_prompt}")
        except Exception as e:
            logger.error(f"유저 프롬프트 저장 오류: {e}")
            print(f"유저 프롬프트 저장 오류: {e}")

# 기존 호환성을 위한 전역 클라이언트
mcp_client = None

def get_mcp_client():
    global mcp_client
    return mcp_client

def set_mcp_client(client):
    global mcp_client
    mcp_client = client