"""
Chat Widget Welcome Mixin
채팅 위젯 웰컴/히스토리 로드 메서드 분리
"""

from core.logging import get_logger
from ui.styles.theme_manager import theme_manager

logger = get_logger("chat_widget_welcome")


class ChatWidgetWelcomeMixin:
    """채팅 위젯 웰컴/히스토리 로드 메서드"""
    
    def _load_previous_conversations(self):
        """이전 대화 로드"""
        try:
            self._welcome_shown = True
            self.conversation_history.load_from_file()
            all_messages = self.conversation_history.current_session
            
            if all_messages:
                display_messages = all_messages[-self.initial_load_count:] if len(all_messages) > self.initial_load_count else all_messages
                
                unique_contents = set()
                unique_messages = []
                
                for msg in display_messages:
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    
                    if not content or not content.strip():
                        continue
                    
                    content_key = f"{role}:{content[:50]}"
                    if content_key not in unique_contents:
                        unique_contents.add(content_key)
                        unique_messages.append(msg)
                
                if unique_messages:
                    for msg in unique_messages:
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        model = msg.get('model', '')
                        
                        if role == 'user':
                            self.chat_display.append_message('사용자', content, message_id=msg.get('id'))
                        elif role == 'assistant':
                            token_info = ""
                            input_tokens = msg.get('input_tokens', 0)
                            output_tokens = msg.get('output_tokens', 0)
                            total_tokens = msg.get('total_tokens', 0)
                            
                            if input_tokens > 0 and output_tokens > 0 and total_tokens > 0:
                                token_info = f" | 📊 {total_tokens:,}토큰 (IN:{input_tokens:,} OUT:{output_tokens:,})"
                            elif total_tokens > 0:
                                token_info = f" | 📊 {total_tokens:,}토큰"
                            elif msg.get('token_count', 0) > 0:
                                token_info = f" | 📊 {msg['token_count']:,}토큰"
                            
                            colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
                            is_light = not theme_manager.material_manager.is_dark_theme() if theme_manager.use_material_theme else False
                            text_dim = colors.get('text_secondary', '#666666' if is_light else '#a0a0a0')
                            
                            if model and model != 'unknown':
                                enhanced_content = f"{content}\n\n<div class='ai-footer'>\n<div class='ai-info' style='color: {text_dim};'>🤖 {model}{token_info}</div>\n</div>"
                                self.chat_display.append_message('AI', enhanced_content, original_sender=model, message_id=msg.get('id'))
                            else:
                                enhanced_content = f"{content}\n\n<div class='ai-footer'>\n<div class='ai-info' style='color: {text_dim};'>🤖 AI{token_info}</div>\n</div>" if token_info else content
                                self.chat_display.append_message('AI', enhanced_content, message_id=msg.get('id'))
                    
                    stats = self.conversation_history.get_stats()
                    total_tokens = stats.get('total_tokens', 0)
                    model_stats = stats.get('model_stats', {})
                    
                    token_summary = f"📊 전체 토큰: {total_tokens:,}개"
                    if model_stats:
                        model_breakdown = []
                        for model, data in model_stats.items():
                            if model != 'unknown':
                                model_breakdown.append(f"{model}: {data['tokens']:,}")
                        if model_breakdown:
                            token_summary += f" ({', '.join(model_breakdown)})"
                    
                    welcome_msg = self._generate_welcome_message(len(unique_messages), token_summary)
                    self.chat_display.append_message('시스템', welcome_msg)
                else:
                    stats = self.conversation_history.get_stats()
                    total_tokens = stats.get('total_tokens', 0)
                    welcome_msg = self._generate_welcome_message(0, f"📊 전체 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
                    self.chat_display.append_message('시스템', welcome_msg)
            else:
                stats = self.conversation_history.get_stats()
                total_tokens = stats.get('total_tokens', 0)
                welcome_msg = self._generate_welcome_message(0, f"📊 누적 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
                self.chat_display.append_message('시스템', welcome_msg)
                
        except Exception as e:
            logger.debug(f"대화 기록 로드 오류: {e}")
            try:
                stats = self.conversation_history.get_stats()
                total_tokens = stats.get('total_tokens', 0)
                welcome_msg = self._generate_welcome_message(0, f"📊 전체 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
                self.chat_display.append_message('시스템', welcome_msg)
            except:
                welcome_msg = self._generate_welcome_message(0, None)
                self.chat_display.append_message('시스템', welcome_msg)
    
    def _show_welcome_message(self):
        """웰컴 메시지 표시"""
        try:
            stats = self.conversation_history.get_stats()
            total_tokens = stats.get('total_tokens', 0)
            welcome_msg = self._generate_welcome_message(0, f"📊 누적 토큰: {total_tokens:,}개" if total_tokens > 0 else None)
            self.chat_display.append_message('시스템', welcome_msg)
        except Exception as e:
            logger.debug(f"웰컴 메시지 표시 오류: {e}")
            welcome_msg = self._generate_welcome_message(0, None)
            self.chat_display.append_message('시스템', welcome_msg)
    
    def _ensure_welcome_message(self):
        """웰컴 메시지 보장"""
        try:
            if not hasattr(self, '_welcome_shown'):
                self._welcome_shown = True
                self._show_welcome_message()
        except Exception as e:
            logger.debug(f"웰컴 메시지 보장 오류: {e}")
    
    def _generate_welcome_message(self, message_count=0, token_info=None):
        """테마 색상이 적용된 환영 메시지 생성"""
        try:
            colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
            primary_color = colors.get('primary', '#bb86fc')
            is_light = not theme_manager.material_manager.is_dark_theme() if theme_manager.use_material_theme else False
            text_color = colors.get('on_surface', colors.get('text_primary', '#1a1a1a' if is_light else '#ffffff'))
            
            welcome_parts = [
                f'<div style="color: {primary_color}; font-weight: bold; font-size: 1.2em;">🧞 MyGenie에 오신 것을 환영합니다! ✨</div>',
                '',
                f'<span style="color: {text_color};">💫 당신만을 위한 AI 지니, 원하는 모든 것을 이루어드립니다</span>',
                ''
            ]
            
            if message_count > 0:
                welcome_parts.append(f'🔄 **이전 대화**: {message_count}개 메시지 로드됨')
            
            if token_info:
                welcome_parts.append(token_info)
            
            if message_count > 0 or token_info:
                welcome_parts.append('')
            
            welcome_parts.extend([
                f'<div style="color: {primary_color}; font-weight: bold;">🎯 MyGenie의 능력:</div>',
                f'<span style="color: {text_color};">• 💬 **수다 떨기**: 심심하면 말 걸어주세요</span>',
                f'<span style="color: {text_color};">• 🔧 **만능 해결사**: 검색, DB, API... 못하는 게 뭐예요?</span>',
                f'<span style="color: {text_color};">• 📎 **파일 읽어드림**: 문서, 이미지, 데이터 다 봐드려요</span>',
                f'<span style="color: {text_color};">• ▶️ **코드 돌려드림**: Python, JS, Java 바로 실행</span>',
                '',
                f'<span style="color: {text_color};">⚠️ **솔직 고백**: 완벽하진 않아요. 의심은 미덕입니다!</span>'
            ])
            
            return '\n'.join(welcome_parts)
            
        except Exception as e:
            logger.debug(f"환영 메시지 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return '🧞 **MyGenie에 오신 것을 환영합니다!** ✨\n\n💫 당신만을 위한 AI 지니, 원하는 모든 것을 이루어드립니다'
