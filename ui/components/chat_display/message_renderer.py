"""
Message Renderer
메시지 렌더링 전담
"""

from PyQt6.QtCore import QTimer
import json
import uuid
from core.logging import get_logger

logger = get_logger("message_renderer")


class MessageRenderer:
    """메시지 렌더링 관리"""
    
    def __init__(self, web_view, progressive_display, progressive_enabled, delay_per_line, initial_delay):
        self.web_view = web_view
        self.progressive_display = progressive_display
        self.progressive_enabled = progressive_enabled
        self.delay_per_line = delay_per_line
        self.initial_delay = initial_delay
    
    def append_message(
        self,
        sender,
        text,
        original_sender=None,
        progressive=False,
        message_id=None,
        prepend=False,
        timestamp=None,
    ):
        """메시지 추가 - progressive=True시 점진적 출력, prepend=True시 상단에 추가"""
        # 타임스탬프 생성 (전달된 timestamp가 없으면 현재 시간 사용)
        from datetime import datetime
        if timestamp:
            # DB에서 로드된 timestamp 사용 (문자열 또는 datetime 객체)
            if isinstance(timestamp, str):
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt = datetime.now()
            else:
                dt = timestamp
        else:
            # 실시간 대화: 현재 시간 사용
            dt = datetime.now()
        
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        timestamp_str = dt.strftime(f"%Y-%m-%d %H:%M:%S ({weekdays[dt.weekday()]}요일)")
        
        # 테마에 따른 색상 가져오기
        from ui.styles.theme_manager import theme_manager

        colors = (
            theme_manager.material_manager.get_theme_colors()
            if theme_manager.use_material_theme
            else {}
        )

        # 테마 타입 확인
        is_light_theme = not theme_manager.material_manager.is_dark_theme()
        
        # 기본 텍스트 색상을 테마에서 가져오기
        default_text_color = colors.get('text_primary', '#0f172a' if is_light_theme else '#ffffff')

        # 렌더링 확실히 보장하는 포맷터 사용
        from ui.fixed_formatter import FixedFormatter

        formatter = FixedFormatter()
        formatted_text = formatter.format_basic_markdown(text)

        display_message_id = message_id or f"msg_{uuid.uuid4().hex[:8]}"

        # 메시지 컨테이너 생성과 콘텐츠 설정을 한 번에 처리
        safe_content = json.dumps(formatted_text, ensure_ascii=False)

        # 발신자별 아이콘
        if sender == "사용자":
            icon = "💬"
        elif sender in ["AI", "에이전트"] or "에이전트" in sender:
            icon = "🤖"
        else:
            icon = "⚙️"

        combined_js = f"""
        try {{
            console.log('=== 메시지 생성 시작 ===');
            console.log('메시지 ID: {display_message_id}');
            console.log('발신자: {sender}');
            
            var messagesDiv = document.getElementById('messages');
            
            var messageDiv = document.createElement('div');
            messageDiv.id = '{display_message_id}';
            messageDiv.setAttribute('data-message-id', '{message_id or display_message_id}');
            messageDiv.className = 'message';
            
            var headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            
            var senderInfo = document.createElement('div');
            senderInfo.className = 'message-sender-info';
            senderInfo.innerHTML = '<span class="message-icon">{icon}</span><span>{sender}</span>';
            
            // 개별 메시지 버튼 컨테이너
            var buttonContainer = document.createElement('div');
            buttonContainer.className = 'message-buttons';
            
            // 복사 버튼
            var copyBtn = document.createElement('button');
            copyBtn.innerHTML = '📋';
            copyBtn.title = '텍스트 복사';
            copyBtn.className = 'btn-primary message-btn';
            copyBtn.onclick = function() {{ copyMessage('{display_message_id}'); }};
            
            // HTML 복사 버튼
            var htmlCopyBtn = document.createElement('button');
            htmlCopyBtn.innerHTML = '🏷️';
            htmlCopyBtn.title = 'HTML 복사';
            htmlCopyBtn.className = 'btn-secondary message-btn';
            htmlCopyBtn.onclick = function() {{ copyHtmlMessage('{display_message_id}'); }};
            
            // 삭제 버튼
            var deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = '메시지 삭제';
            deleteBtn.className = 'btn-error message-btn';
            deleteBtn.onclick = function() {{ 
                if (confirm('이 메시지를 삭제하시겠습니까?')) {{
                    deleteMessage('{message_id or display_message_id}'); 
                }}
            }};
            
            // 버튼들을 컨테이너에 추가
            buttonContainer.appendChild(copyBtn);
            buttonContainer.appendChild(htmlCopyBtn);
            buttonContainer.appendChild(deleteBtn);
            
            headerDiv.appendChild(senderInfo);
            headerDiv.appendChild(buttonContainer);
            
            var contentDiv = document.createElement('div');
            contentDiv.id = '{display_message_id}_content';
            contentDiv.className = 'message-content';
            
            // 타임스탬프 추가
            var timestampDiv = document.createElement('div');
            timestampDiv.className = 'message-timestamp';
            timestampDiv.textContent = '{timestamp_str}';
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timestampDiv);
            
            if ({str(prepend).lower()}) {{
                // prepend 시에는 기존 첫 번째 메시지 앞에 삽입
                messagesDiv.insertBefore(messageDiv, messagesDiv.firstChild);
            }} else {{
                // 일반적인 경우 맨 뒤에 추가
                messagesDiv.appendChild(messageDiv);
            }}
            
            contentDiv.innerHTML = {safe_content};
            
            console.log('메시지 생성 완료: {display_message_id}');
            
            // Mermaid 다이어그램 렌더링
            setTimeout(function() {{
                if (typeof renderMermaidDiagrams === 'function') {{
                    renderMermaidDiagrams();
                }}
            }}, 50);
            
            // 스크롤 조정 - 하단 스크롤
            setTimeout(function() {{
                if (!{str(prepend).lower()}) {{
                    const maxScroll = Math.max(
                        document.body.scrollHeight,
                        document.documentElement.scrollHeight
                    );
                    window.scrollTo(0, maxScroll);
                }}
            }}, 100);
            
        }} catch(e) {{
            console.error('메시지 생성 오류:', e);
        }}
        """

        if progressive and self.progressive_enabled:
            # 점진적 출력 요청 시 - 먼저 빈 컨테이너 생성
            empty_js = combined_js.replace(
                f"contentDiv.innerHTML = {safe_content};", 'contentDiv.innerHTML = "";'
            )
            self.web_view.page().runJavaScript(empty_js)
            QTimer.singleShot(
                self.initial_delay,
                lambda: self.progressive_display.display_text_progressively(
                    display_message_id,
                    formatted_text,
                    delay_per_line=self.delay_per_line,
                ),
            )
        else:
            # 일반 출력 - 한 번에 처리
            self.web_view.page().runJavaScript(combined_js)

        return display_message_id
