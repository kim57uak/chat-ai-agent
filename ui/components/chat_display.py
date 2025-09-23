from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer, QUrl, QObject, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from ui.components.progressive_display import ProgressiveDisplay
import json
import uuid


class ChatDisplay:
    """채팅 표시를 담당하는 클래스 (SRP)"""

    def __init__(self, web_view: QWebEngineView):
        self.web_view = web_view
        self.progressive_display = ProgressiveDisplay(web_view)
        self._load_ui_settings()
        self._setup_link_handler()
        self.init_web_view()

    def _load_ui_settings(self):
        """UI 설정 로드"""
        try:
            from core.file_utils import load_config

            config = load_config()
            ui_settings = config.get("ui_settings", {})
            progressive_settings = ui_settings.get("progressive_display", {})

            self.progressive_enabled = progressive_settings.get("enabled", True)
            self.delay_per_line = progressive_settings.get("delay_per_line", 30)
            self.initial_delay = progressive_settings.get("initial_delay", 100)
        except Exception as e:
            # 설정 로드 실패 시 기본값 사용
            self.progressive_enabled = True
            self.delay_per_line = 30
            self.initial_delay = 100

    def init_web_view(self):
        """웹 브라우저 초기화 - 고급 다크 테마"""
        from ui.styles.theme_manager import theme_manager

        # 웹 보안 설정 완화 (PyQt6 호환)
        settings = self.web_view.settings()
        settings.setAttribute(
            settings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)

        # PyQt6에서 지원하는 속성만 사용
        try:
            settings.setAttribute(
                settings.WebAttribute.AllowRunningInsecureContent, True
            )
        except AttributeError:
            pass
        try:
            settings.setAttribute(
                settings.WebAttribute.PlaybackRequiresUserGesture, False
            )
        except AttributeError:
            pass

        # 웹뷰 배경 투명 설정 및 스크롤 최적화
        self.web_view.page().setBackgroundColor(
            self.web_view.palette().color(self.web_view.palette().ColorRole.Window)
        )
        
        # 스크롤바 스타일 적용
        self._apply_scrollbar_style()
    
    def _apply_scrollbar_style(self):
        """PyQt6 스크롤바 스타일 적용"""
        from ui.styles.theme_manager import theme_manager
        
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            primary_color = colors.get('primary', '#bb86fc')
            surface_color = colors.get('surface', '#1e1e1e')
            
            scrollbar_style = f"""
            QScrollBar:vertical {{
                background: {surface_color};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(255,255,255,0.3), 
                    stop:1 {primary_color});
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {primary_color};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            """
            
            self.web_view.setStyleSheet(scrollbar_style)

        # 스크롤 성능 향상을 위한 추가 설정
        from PyQt6.QtCore import QUrl

        self.web_view.page().profile().setHttpCacheType(
            self.web_view.page().profile().HttpCacheType.MemoryHttpCache
        )
        self.web_view.page().profile().setHttpCacheMaximumSize(
            50 * 1024 * 1024
        )  # 50MB 캐시

        # 콘솔 메시지 캡처
        self.web_view.page().javaScriptConsoleMessage = self.handle_console_message

        # HTML 템플릿 로드
        self._load_html_template()

    def handle_console_message(self, level, message, line_number, source_id):
        """자바스크립트 콘솔 메시지 처리"""
        print(f"[JS Console] {message} (line: {line_number})")

    def _load_html_template(self):
        """HTML 템플릿 로드"""
        theme_css = self._get_current_theme_css()
        mermaid_theme = "dark" if self.is_dark_theme() else "default"

        # 현재 테마의 배경색 가져오기
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            body_bg_color = colors.get("background", "#121212")
        else:
            from ui.styles.flat_theme import FlatTheme

            colors = FlatTheme.get_theme_colors()
            body_bg_color = colors.get("background", "#1a1a1a")

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <script src="https://unpkg.com/mermaid@11.12.0/dist/mermaid.min.js"></script>
            <style id="theme-style">
                {theme_css}
                
                html, body {{
                    background: {body_bg_color} !important;
                    color: {colors.get('text_primary', '#ffffff')} !important;
                    margin: 0;
                    padding: 0;
                    font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
                    font-size: 15px !important;
                    line-height: 1.6 !important;
                }}
                
                #messages {{
                    height: auto;
                    overflow-y: visible;
                }}
                
                .message {{
                    margin: 16px 0;
                    padding: 24px;
                    background: {colors.get('surface', 'rgba(255, 255, 255, 0.05)')};
                    border: 1px solid {colors.get('divider', 'rgba(255, 255, 255, 0.1)')};
                    border-radius: 16px;
                    position: relative;
                    color: {colors.get('text_primary', '#ffffff')} !important;
                }}
                
                .message * {{
                    color: {colors.get('text_primary', '#ffffff')} !important;
                }}
            </style>
        </head>
        <body>
            <div id="messages"></div>
            <script>
                console.log('HTML 로드 완료');
                
                var pyqt_bridge = null;
                
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    pyqt_bridge = channel.objects.pyqt_bridge;
                }});
                
                function copyMessage(messageId) {{
                    try {{
                        var contentDiv = document.getElementById(messageId + '_content');
                        if (!contentDiv) {{
                            return;
                        }}
                        
                        var textContent = contentDiv.innerText || contentDiv.textContent;
                        
                        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {{
                            pyqt_bridge.copyToClipboard(textContent);
                            showToast('텍스트가 복사되었습니다!');
                        }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
                            navigator.clipboard.writeText(textContent).then(function() {{
                                showToast('텍스트가 복사되었습니다!');
                            }});
                        }}
                    }} catch (error) {{
                        console.error('Message copy failed:', error);
                        showToast('복사에 실패했습니다.');
                    }}
                }}
                
                function copyHtmlMessage(messageId) {{
                    try {{
                        var contentDiv = document.getElementById(messageId + '_content');
                        if (!contentDiv) {{
                            return;
                        }}
                        
                        var htmlContent = contentDiv.innerHTML;
                        
                        if (pyqt_bridge && pyqt_bridge.copyHtmlToClipboard) {{
                            pyqt_bridge.copyHtmlToClipboard(htmlContent);
                            showToast('HTML이 복사되었습니다!');
                        }} else {{
                            var textArea = document.createElement('textarea');
                            textArea.value = htmlContent;
                            document.body.appendChild(textArea);
                            textArea.select();
                            document.execCommand('copy');
                            document.body.removeChild(textArea);
                            showToast('HTML이 복사되었습니다!');
                        }}
                    }} catch (error) {{
                        console.error('HTML copy failed:', error);
                        showToast('HTML 복사에 실패했습니다.');
                    }}
                }}
                
                function showToast(message) {{
                    var toast = document.createElement('div');
                    toast.textContent = message;
                    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; background: rgba(139, 92, 246, 0.9); color: white; padding: 12px 20px; border-radius: 8px; z-index: 10000; font-size: 14px; font-weight: 600;';
                    document.body.appendChild(toast);
                    
                    setTimeout(function() {{
                        if (toast.parentNode) {{
                            toast.parentNode.removeChild(toast);
                        }}
                    }}, 2000);
                }}
                
                function copyCode(codeElement) {{
                    try {{
                        var codeText = codeElement.textContent || codeElement.innerText;
                        
                        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {{
                            pyqt_bridge.copyToClipboard(codeText);
                            showToast('코드가 복사되었습니다!');
                        }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
                            navigator.clipboard.writeText(codeText).then(function() {{
                                showToast('코드가 복사되었습니다!');
                            }});
                        }}
                    }} catch (error) {{
                        console.error('Code copy failed:', error);
                        showToast('코드 복사에 실패했습니다.');
                    }}
                }}
                
                function deleteMessage(messageId) {{
                    try {{
                        if (pyqt_bridge && pyqt_bridge.deleteMessage) {{
                            pyqt_bridge.deleteMessage(messageId);
                        }}
                    }} catch (error) {{
                        console.error('Message delete failed:', error);
                    }}
                }}
                
                function removeMessageFromDOM(messageId) {{
                    try {{
                        var messageElements = document.querySelectorAll('[data-message-id="' + messageId + '"]');
                        for (var i = 0; i < messageElements.length; i++) {{
                            messageElements[i].remove();
                        }}
                    }} catch (error) {{
                        console.error('DOM message removal failed:', error);
                    }}
                }}
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html_template)

    def _get_current_theme_css(self) -> str:
        """현재 테마 CSS 반환"""
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            css = theme_manager.material_manager.generate_web_css()
            return css
        else:
            from ui.styles.flat_theme import FlatTheme
            css = FlatTheme.get_chat_display_css()
            return css

    def is_dark_theme(self) -> bool:
        """현재 테마가 다크 테마인지 확인"""
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            return theme_manager.material_manager.is_dark_theme()
        else:
            return True  # 기본 테마는 다크 테마로 간주

    def update_theme(self):
        """테마 업데이트 - HTML 템플릿 완전 재로드"""
        try:
            from ui.styles.theme_manager import theme_manager
            print(f"테마 업데이트 시작: {theme_manager.material_manager.current_theme_key}")
            
            # 기존 메시지 내용 백업
            backup_js = """
            try {
                var messages = [];
                var messageElements = document.querySelectorAll('.message');
                for (var i = 0; i < messageElements.length; i++) {
                    var msg = messageElements[i];
                    messages.push({
                        id: msg.id,
                        innerHTML: msg.innerHTML
                    });
                }
                window.messageBackup = messages;
                console.log('메시지 백업 완료:', messages.length);
            } catch(e) {
                console.error('메시지 백업 오류:', e);
                window.messageBackup = [];
            }
            """
            
            self.web_view.page().runJavaScript(backup_js)
            
            # 100ms 후 HTML 템플릿 재로드
            QTimer.singleShot(100, self._reload_with_backup)
            
        except Exception as e:
            print(f"채팅 디스플레이 테마 업데이트 오류: {e}")
    
    def _reload_with_backup(self):
        """백업된 메시지와 함께 HTML 재로드"""
        try:
            # HTML 템플릿 재로드
            self._load_html_template()
            
            # 200ms 후 메시지 복원
            QTimer.singleShot(200, self._restore_messages)
            
        except Exception as e:
            print(f"HTML 재로드 오류: {e}")
    
    def _restore_messages(self):
        """백업된 메시지 복원"""
        restore_js = """
        try {
            if (window.messageBackup && window.messageBackup.length > 0) {
                var messagesDiv = document.getElementById('messages');
                if (messagesDiv) {
                    for (var i = 0; i < window.messageBackup.length; i++) {
                        var msgData = window.messageBackup[i];
                        var messageDiv = document.createElement('div');
                        messageDiv.id = msgData.id;
                        messageDiv.className = 'message';
                        messageDiv.innerHTML = msgData.innerHTML;
                        messagesDiv.appendChild(messageDiv);
                    }
                    console.log('메시지 복원 완료:', window.messageBackup.length);
                    // 스크롤을 맨 아래로
                    setTimeout(function() {
                        window.scrollTo(0, document.body.scrollHeight);
                    }, 50);
                }
            }
        } catch(e) {
            console.error('메시지 복원 오류:', e);
        }
        """
        
        self.web_view.page().runJavaScript(restore_js)
        print("채팅 디스플레이 테마 업데이트 완료")

    def _setup_link_handler(self):
        """링크 클릭 핸들러 설정"""
        from PyQt6.QtWebChannel import QWebChannel

        # 웹 채널 설정
        self.channel = QWebChannel()
        self.link_handler = LinkHandler()
        self.channel.registerObject("pyqt_bridge", self.link_handler)
        self.web_view.page().setWebChannel(self.channel)

    def set_chat_widget(self, chat_widget):
        """채팅 위젯 참조 설정"""
        self.link_handler.chat_widget = chat_widget

    def append_message(
        self,
        sender,
        text,
        original_sender=None,
        progressive=False,
        message_id=None,
        prepend=False,
    ):
        """메시지 추가 - progressive=True시 점진적 출력, prepend=True시 상단에 추가"""
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
            console.log('테마 색상: {default_text_color}');
            
            var messagesDiv = document.getElementById('messages');
            
            var messageDiv = document.createElement('div');
            messageDiv.id = '{display_message_id}';
            messageDiv.setAttribute('data-message-id', '{message_id or display_message_id}');
            messageDiv.className = 'message';
            
            var headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'margin: 0 0 12px 0; font-weight: 600; color: {default_text_color} !important; font-size: 13px; display: flex; align-items: center; gap: 8px;';
            headerDiv.innerHTML = '<span style="font-size:16px;">{icon}</span><span>{sender}</span>';
            
            // 버튼 컨테이너 생성
            var buttonContainer = document.createElement('div');
            buttonContainer.style.cssText = 'position: absolute !important; top: 16px !important; right: 16px !important; display: flex !important; gap: 6px !important; opacity: 1 !important; z-index: 999999 !important; pointer-events: auto !important;';
            
            // 복사 버튼
            var copyBtn = document.createElement('button');
            copyBtn.innerHTML = '📋';
            copyBtn.title = '텍스트 복사';
            copyBtn.style.cssText = 'background: {colors.get("primary", "#bb86fc")}; color: {colors.get("on_primary", "#000000")}; border: 1px solid {colors.get("primary", "#bb86fc")}; padding: 8px 10px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s ease;';
            copyBtn.onclick = function() {{ copyMessage('{display_message_id}'); }};
            
            // HTML 복사 버튼
            var htmlCopyBtn = document.createElement('button');
            htmlCopyBtn.innerHTML = '🏷️';
            htmlCopyBtn.title = 'HTML 복사';
            htmlCopyBtn.style.cssText = 'background: {colors.get("secondary", "#03dac6")}; color: {colors.get("on_secondary", "#000000")}; border: 1px solid {colors.get("secondary", "#03dac6")}; padding: 8px 10px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s ease;';
            htmlCopyBtn.onclick = function() {{ copyHtmlMessage('{display_message_id}'); }};
            
            // 삭제 버튼
            var deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = '메시지 삭제';
            deleteBtn.style.cssText = 'background: {colors.get("error", "#cf6679")}; color: {colors.get("on_error", "#000000")}; border: 1px solid {colors.get("error", "#cf6679")}; padding: 8px 10px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s ease;';
            deleteBtn.onclick = function() {{ 
                if (confirm('이 메시지를 삭제하시겠습니까?')) {{
                    deleteMessage('{message_id or display_message_id}'); 
                }}
            }};
            
            // 버튼들을 컨테이너에 추가
            buttonContainer.appendChild(copyBtn);
            buttonContainer.appendChild(htmlCopyBtn);
            buttonContainer.appendChild(deleteBtn);
            
            // 버튼 항상 표시 (호버 효과 제거)
            
            var contentDiv = document.createElement('div');
            contentDiv.id = '{display_message_id}_content';
            contentDiv.style.cssText = 'margin: 0; padding-right: 180px; line-height: 1.6; color: {default_text_color} !important; font-size: 15px; word-wrap: break-word;';
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(buttonContainer);
            messageDiv.appendChild(contentDiv);
            
            if ({str(prepend).lower()}) {{
                messagesDiv.insertBefore(messageDiv, messagesDiv.firstChild);
            }} else {{
                messagesDiv.appendChild(messageDiv);
            }}
            
            contentDiv.innerHTML = {safe_content};
            
            // 색상 강제 적용
            contentDiv.style.color = '{default_text_color}';
            var allElements = contentDiv.getElementsByTagName('*');
            for (var i = 0; i < allElements.length; i++) {{
                var el = allElements[i];
                if (el.tagName !== 'CODE' && el.tagName !== 'PRE') {{
                    el.style.color = '{default_text_color}';
                }}
            }}
            
            console.log('메시지 생성 완료: {display_message_id}');
            
            // 스크롤 조정
            setTimeout(function() {{
                if (!{str(prepend).lower()}) {{
                    window.scrollTo(0, document.body.scrollHeight);
                }}
            }}, 10);
            
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

    def clear_messages(self):
        """메시지 초기화"""
        self.progressive_display.cancel_current_display()
        self.init_web_view()

    def cancel_progressive_display(self):
        """점진적 출력 취소"""
        self.progressive_display.cancel_current_display()


class LinkHandler(QObject):
    """링크 클릭 및 이미지 저장 처리를 위한 핸들러"""

    def __init__(self, chat_widget=None):
        super().__init__()
        self.chat_widget = chat_widget

    @pyqtSlot(str)
    def openUrl(self, url):
        """URL을 기본 브라우저에서 열기"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"URL 열기 오류: {e}")

    @pyqtSlot(str)
    def copyToClipboard(self, text):
        """텍스트를 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
            
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.clear()
                clipboard.setText(text)
                
                # 복사 확인을 위해 잠시 후 다시 확인
                def verify_copy():
                    copied_text = clipboard.text()
                    if copied_text == text:
                        print(f"[COPY] 클립보드 복사 성공 확인: {len(text)}자")
                    else:
                        print(f"[COPY] 클립보드 복사 실패 - 예상: {len(text)}자, 실제: {len(copied_text)}자")
                
                QTimer.singleShot(100, verify_copy)
                print(f"[COPY] 클립보드 복사 시도: {len(text)}자")
            else:
                print(f"[COPY] QApplication 인스턴스 없음")
        except Exception as e:
            print(f"[COPY] 클립보드 복사 오류: {e}")
            import traceback
            traceback.print_exc()
    
    @pyqtSlot(str)
    def copyHtmlToClipboard(self, html):
        """HTML을 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QMimeData, QTimer
            
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.clear()
                
                mime_data = QMimeData()
                mime_data.setHtml(html)
                mime_data.setText(html)  # 텍스트 버전도 함께 저장
                clipboard.setMimeData(mime_data)
                
                # 복사 확인
                def verify_html_copy():
                    copied_html = clipboard.mimeData().html()
                    if copied_html:
                        print(f"[COPY_HTML] HTML 클립보드 복사 성공 확인: {len(html)}자")
                    else:
                        print(f"[COPY_HTML] HTML 클립보드 복사 실패")
                
                QTimer.singleShot(100, verify_html_copy)
                print(f"[COPY_HTML] HTML 클립보드 복사 시도: {len(html)}자")
            else:
                print(f"[COPY_HTML] QApplication 인스턴스 없음")
        except Exception as e:
            print(f"[COPY_HTML] HTML 클립보드 복사 오류: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(str)
    def deleteMessage(self, message_id):
        """메시지 삭제"""
        try:
            print(f"[DELETE] 삭제 요청: {message_id}")

            # 먼저 DOM에서 제거 (즉시 시각적 피드백)
            if (
                hasattr(self, "chat_widget")
                and self.chat_widget
                and hasattr(self.chat_widget, "chat_display")
            ):
                self.chat_widget.chat_display.web_view.page().runJavaScript(
                    f"removeMessageFromDOM('{message_id}')"
                )
                print(f"[DELETE] DOM에서 제거 완료: {message_id}")

            # 데이터에서 삭제
            if self.chat_widget and hasattr(self.chat_widget, "delete_message"):
                success = self.chat_widget.delete_message(message_id)
                print(f"[DELETE] 데이터 삭제 결과: {success}")
            else:
                print(f"[DELETE] delete_message 메소드 없음")

        except Exception as e:
            print(f"[DELETE] 오류: {e}")
            import traceback

            traceback.print_exc()