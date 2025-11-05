"""
Chat Widget Message Mixin
채팅 위젯 메시지 처리 메서드 분리
"""

from datetime import datetime
from core.logging import get_logger
from core.file_utils import load_last_model
from ui.components.status_display import status_display
from core.simple_token_accumulator import token_accumulator
from ui.styles.theme_manager import theme_manager

logger = get_logger("chat_widget_message")


class ChatWidgetMessageMixin:
    """채팅 위젯 메시지 처리 메서드"""
    
    def _process_new_message(self, user_text):
        """새 메시지 처리"""
        from ui.chat_widget import safe_single_shot
        
        self.request_start_time = datetime.now()
        
        logger.debug(f"[ChatWidget] 사용자 메시지 입력 - 토큰 누적기 상태 확인")
        if not token_accumulator.conversation_active:
            token_accumulator.start_conversation()
        else:
            logger.debug(f"[ChatWidget] 대화가 이미 진행 중 - 토큰 계속 누적")
        
        message_id = self.conversation_history.add_message('user', user_text)
        self.messages.append({'role': 'user', 'content': user_text})
        
        logger.debug(f"[CHAT_WIDGET] 사용자 메시지 저장 시도: {user_text[:50]}...")
        main_window = self._find_main_window()
        if main_window and hasattr(main_window, 'save_message_to_session'):
            main_window.save_message_to_session('user', user_text, 0)
        else:
            logger.debug(f"[CHAT_WIDGET] MainWindow를 찾을 수 없거나 save_message_to_session 메소드 없음")
        
        self.chat_display.append_message('사용자', user_text, message_id=message_id)
        self.input_text.clear()
        
        safe_single_shot(500, self._scroll_to_bottom, self)
        
        from core.file_utils import load_model_api_key
        model = load_last_model()
        api_key = load_model_api_key(model)
        
        if not api_key:
            self.chat_display.append_message('시스템', 'API Key가 설정되어 있지 않습니다. 환경설정에서 입력해 주세요.')
            return
        
        if self.uploaded_file_content:
            if "[IMAGE_BASE64]" in self.uploaded_file_content:
                combined_prompt = f'{user_text}\n\n{self.uploaded_file_content}'
            else:
                combined_prompt = f'업로드된 파일 ({self.uploaded_file_name})에 대한 사용자 요청: {user_text}\n\n파일 내용:\n{self.uploaded_file_content}'
            
            self._start_ai_request(api_key, model, None, combined_prompt)
            self.uploaded_file_content = None
            self.uploaded_file_name = None
        else:
            self._start_ai_request(api_key, model, user_text)
    
    def _start_ai_request(self, api_key, model, user_text, file_prompt=None):
        """AI 요청 시작"""
        from ui.chat_widget import safe_single_shot
        
        self.ui_manager.set_ui_enabled(False)
        self.ui_manager.show_loading(True)
        
        safe_single_shot(0, lambda: self._prepare_and_send_request(api_key, model, user_text, file_prompt), self)
    
    def _prepare_and_send_request(self, api_key, model, user_text, file_prompt=None):
        """요청 준비 및 전송"""
        from ui.chat_widget import safe_single_shot
        
        try:
            if 'logger' not in globals():
                from core.logging import get_logger
                global logger
                logger = get_logger("chat_widget_message")
            
            context_messages = self.conversation_history.get_context_messages()
            
            validated_history = []
            for msg in context_messages:
                if msg.get('content') and msg.get('content').strip():
                    validated_history.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            logger.debug(f"하이브리드 히스토리 로드됨: {len(validated_history)}개 메시지 (모델: {model})")
            
            try:
                mode_value = self.mode_combo.currentData()
                use_agent = mode_value in ["tool", "rag"]
                chat_mode = mode_value
            except Exception as e:
                logger.debug(f"모드 확인 오류: {e}")
                use_agent = False
                chat_mode = "simple"
            
            self.ai_processor.process_request(
                api_key, model, validated_history, user_text,
                agent_mode=use_agent, file_prompt=file_prompt, chat_mode=chat_mode
            )
        except Exception as e:
            try:
                logger.debug(f"AI 요청 준비 오류: {e}")
            except:
                print(f"AI 요청 준비 오류: {e}")
            safe_single_shot(0, lambda: self.on_ai_error(f"요청 준비 중 오류: {e}"), self)
    
    def on_ai_response(self, sender, text, used_tools):
        """AI 응답 처리"""
        from ui.chat_widget import safe_single_shot
        
        logger.debug(f"AI 응답 받음 - 길이: {len(text)}자")
        
        response_time = ""
        if self.request_start_time:
            elapsed = datetime.now() - self.request_start_time
            response_time = f" ({elapsed.total_seconds():.1f}초)"
        
        current_model = load_last_model()
        
        tools_info = ""
        if '에이전트' in sender and used_tools:
            tool_emojis = self._get_tool_emoji_list(used_tools)
            tools_text = ", ".join([f"{emoji} {tool}" for emoji, tool in tool_emojis])
            tools_info = f"\n\n*사용된 도구: {tools_text}*"
        
        token_info = ""
        current_status = status_display.current_status
        input_tokens = current_status.get('input_tokens', 0)
        output_tokens = current_status.get('output_tokens', 0)
        total_tokens = current_status.get('total_tokens', 0)
        
        current_input, current_output, current_total = token_accumulator.get_total()
        if current_total > 0:
            input_tokens = current_input
            output_tokens = current_output
            total_tokens = current_total
        
        if total_tokens > 0:
            if input_tokens > 0 and output_tokens > 0:
                token_info = f" | 📊 {total_tokens:,}토큰 (IN:{input_tokens:,} OUT:{output_tokens:,})"
            else:
                token_info = f" | 📊 {total_tokens:,}토큰"
        
        colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
        is_light = not theme_manager.material_manager.is_dark_theme() if theme_manager.use_material_theme else False
        text_color = colors.get('on_surface', colors.get('text_primary', '#1a1a1a' if is_light else '#ffffff'))
        text_dim = colors.get('text_secondary', '#666666' if is_light else '#a0a0a0')
        
        enhanced_text = f"{text}{tools_info}\n\n<div class='ai-footer'>\n<div class='ai-info' style='color: {text_dim};'>🤖 {current_model}{response_time}{token_info}</div>\n<div class='ai-warning' style='color: {text_dim};'>⚠️ AI 답변은 부정확할 수 있습니다. 중요한 정보는 반드시 검증하세요.</div>\n</div>"
        
        display_sender = '에이전트' if '에이전트' in sender else 'AI'
        
        current_status = status_display.current_status
        input_tokens = current_status.get('input_tokens', 0)
        output_tokens = current_status.get('output_tokens', 0)
        total_tokens = current_status.get('total_tokens', 0)
        
        current_input, current_output, current_total = token_accumulator.get_total()
        if current_total > 0:
            input_tokens = current_input
            output_tokens = current_output
            total_tokens = current_total
        
        ai_message_id = self.conversation_history.add_message(
            'assistant', text, current_model, 
            input_tokens=input_tokens if input_tokens > 0 else None,
            output_tokens=output_tokens if output_tokens > 0 else None,
            total_tokens=total_tokens if total_tokens > 0 else None
        )
        self.messages.append({'role': 'assistant', 'content': text})
        
        logger.debug(f"[CHAT_WIDGET] AI 메시지 저장 시도: {text[:50]}...")
        main_window = self._find_main_window()
        if main_window and hasattr(main_window, 'save_message_to_session'):
            main_window.save_message_to_session('assistant', text, total_tokens, enhanced_text)
        else:
            logger.debug(f"[CHAT_WIDGET] MainWindow를 찾을 수 없거나 save_message_to_session 메소드 없음")
        
        self.chat_display.append_message(display_sender, enhanced_text, original_sender=sender, progressive=True, message_id=ai_message_id)
        
        safe_single_shot(800, self._scroll_to_bottom, self)
        
        self.ui_manager.set_ui_enabled(True)
        self.ui_manager.show_loading(False)
    
    def on_ai_error(self, msg):
        """AI 오류 처리"""
        from ui.chat_widget import safe_single_shot
        
        error_time = ""
        if self.request_start_time:
            elapsed = datetime.now() - self.request_start_time
            error_time = f" (오류발생시간: {elapsed.total_seconds():.1f}초)"
        
        token_info = ""
        current_status = status_display.current_status
        if current_status.get('total_tokens', 0) > 0:
            total_tokens = current_status['total_tokens']
            input_tokens = current_status.get('input_tokens', 0)
            output_tokens = current_status.get('output_tokens', 0)
            if input_tokens > 0 and output_tokens > 0:
                token_info = f" | 📊 {total_tokens:,}토큰 (IN:{input_tokens:,} OUT:{output_tokens:,})"
            else:
                token_info = f" | 📊 {total_tokens:,}토큰"
        
        current_model = load_last_model()
        enhanced_msg = f"{msg}{error_time}\n\n---\n*🤖 {current_model}{token_info}*\n⚠️ *AI 답변은 부정확할 수 있습니다. 중요한 정보는 반드시 검증하세요.*" if token_info else f"{msg}{error_time}"
        
        self.chat_display.append_message('시스템', enhanced_msg)
        
        safe_single_shot(300, self._scroll_to_bottom, self)
        
        self.ui_manager.set_ui_enabled(True)
        self.ui_manager.show_loading(False)
    
    def _get_tool_emoji_list(self, used_tools):
        """사용된 도구 이모티콘 목록"""
        if not used_tools:
            return []
        
        emoji_map = {
            'search': '🔍', 'web': '🌐', 'url': '🌐', 'fetch': '📄',
            'database': '🗄️', 'mysql': '🗄️', 'sql': '🗄️',
            'travel': '✈️', 'tour': '✈️', 'hotel': '🏨', 'flight': '✈️',
            'map': '🗺️', 'location': '📍', 'geocode': '📍',
            'weather': '🌤️', 'email': '📧', 'file': '📁',
            'excel': '📊', 'chart': '📈', 'image': '🖼️',
            'translate': '🌐', 'api': '🔧'
        }
        
        result = []
        for tool in used_tools:
            tool_name = str(tool).lower()
            emoji = "⚡"
            
            for keyword, e in emoji_map.items():
                if keyword in tool_name:
                    emoji = e
                    break
            
            display_name = str(tool)
            if '.' in display_name:
                display_name = display_name.split('.')[-1]
            
            result.append((emoji, display_name))
        
        return result[:5]
