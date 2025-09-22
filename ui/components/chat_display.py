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

        # JavaScript 코드를 별도로 생성
        javascript_code = f"""
                console.log('HTML 로드 시작');
                
                window.MathJax = {{
                    tex: {{
                        inlineMath: [['$', '$'], ['\\(', '\\)']],
                        displayMath: [['$$', '$$'], ['\\[', '\\]']],
                        processEscapes: true,
                        processEnvironments: true
                    }},
                    options: {{
                        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'],
                        ignoreHtmlClass: 'tex2jax_ignore',
                        processHtmlClass: 'tex2jax_process'
                    }},
                    svg: {{
                        fontCache: 'global'
                    }},
                    startup: {{
                        ready: () => {{
                            console.log('MathJax 준비 완료');
                            MathJax.startup.defaultReady();
                        }}
                    }}
                }};
                
                document.addEventListener('DOMContentLoaded', function() {{
                    console.log('DOM 로드 완료');
                    if (typeof mermaid !== 'undefined') {{
                        mermaid.initialize({{
                            startOnLoad: true,
                            theme: 'dark',
                            securityLevel: 'loose',
                            flowchart: {{ useMaxWidth: true, htmlLabels: true }},
                            sequence: {{ useMaxWidth: true, wrap: true }},
                            gantt: {{ useMaxWidth: true, gridLineStartPadding: 350 }},
                            journey: {{ useMaxWidth: true }},
                            class: {{ useMaxWidth: true }},
                            state: {{ useMaxWidth: true }},
                            er: {{ useMaxWidth: true, layoutDirection: 'TB' }},
                            pie: {{ useMaxWidth: true }},
                            requirement: {{ useMaxWidth: true }},
                            gitgraph: {{ useMaxWidth: true }},
                            c4: {{ useMaxWidth: true }},
                            mindmap: {{ useMaxWidth: true }},
                            timeline: {{ useMaxWidth: true }},
                            sankey: {{ 
                                useMaxWidth: true,
                                config: {{
                                    sankey: {{
                                        width: 600,
                                        height: 400,
                                        nodeLabel: {{
                                            fontSize: 12,
                                            fontWeight: 'bold'
                                        }}
                                    }}
                                }}
                            }},
                            xyChart: {{ useMaxWidth: true }},
                            block: {{ useMaxWidth: true }},
                            packet: {{ useMaxWidth: true }},
                            architecture: {{ useMaxWidth: true }}
                        }});
                        console.log('Mermaid v11.12.0 모든 다이어그램 유형 초기화 완료');
                    }}
                }});
                
                function rerenderMermaid() {{
                    if (typeof mermaid !== 'undefined') {{
                        try {{
                            const mermaidElements = document.querySelectorAll('.mermaid:not([data-processed="true"])');
                            mermaidElements.forEach(element => {{
                                let content = element.textContent || element.innerHTML;
                                
                                // HTML 엔티티 디코딩
                                content = content.replace(/&amp;/g, '&')
                                               .replace(/&lt;/g, '<')
                                               .replace(/&gt;/g, '>')
                                               .replace(/&quot;/g, '"')
                                               .replace(/&#39;/g, "'")
                                               .replace(/&#45;/g, '-');
                                
                                // Mermaid 구문 정리
                                content = content.replace(/--&gt;/g, '-->')
                                               .replace(/&#45;&#45;&#45;/g, '---')
                                               .replace(/-&gt;&gt;/g, '->')
                                               .trim();
                                
                                // Sankey 다이어그램 형식 자동 감지 및 변환
                                if (content.includes('sankey-beta') || 
                                    (content.includes(',') && content.split('\n').length > 1 && 
                                     content.split('\n')[1].split(',').length === 3)) {{
                                    // CSV 형식의 sankey-beta 다이어그램
                                    if (!content.startsWith('sankey-beta')) {{
                                        content = 'sankey-beta\n' + content;
                                    }}
                                }}
                                
                                // 빈 내용이거나 유효하지 않은 구문 체크
                                if (!content || content.length < 5) {{
                                    console.warn('Empty or invalid mermaid content');
                                    return;
                                }}
                                
                                element.textContent = content;
                                element.setAttribute('data-processed', 'false');
                            }});
                            
                            if (mermaidElements.length > 0) {{
                                mermaid.run();
                                console.log('Mermaid 재렌더링 완료');
                            }}
                        }} catch (error) {{
                            console.error('Mermaid 렌더링 오류:', error);
                        }}
                    }}
                }}
                
                window.addEventListener('load', function() {{
                    console.log('페이지 로드 완료');
                    setTimeout(rerenderMermaid, 100);
                }});
        """

        # 웹채널 JavaScript 코드 (중괄호 이스케이프 없이)
        webchannel_js = """
                var pyqt_bridge = null;
                
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    pyqt_bridge = channel.objects.pyqt_bridge;
                });
                
                document.addEventListener('click', function(e) {
                    if (e.target.tagName === 'A' && e.target.href) {
                        e.preventDefault();
                        if (pyqt_bridge) {
                            pyqt_bridge.openUrl(e.target.href);
                        } else {
                            console.log('Bridge not ready, opening in same window');
                            window.location.href = e.target.href;
                        }
                    }
                    
                    // 이미지 저장 버튼 클릭 처리
                    if (e.target.classList.contains('save-image-btn')) {
                        e.preventDefault();
                        const imageUrl = e.target.getAttribute('data-image-url');
                        if (pyqt_bridge && imageUrl) {
                            pyqt_bridge.saveImage(imageUrl);
                        }
                    }
                });
                
                function copyMessage(messageId) {
                    try {
                        const contentDiv = document.getElementById(messageId + '_content');
                        if (!contentDiv) return;
                        
                        const textContent = contentDiv.innerText || contentDiv.textContent;
                        
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            navigator.clipboard.writeText(textContent).then(() => {
                                showMessageCopyFeedback(messageId);
                            }).catch(() => {
                                fallbackCopyMessage(textContent, messageId);
                            });
                        } else {
                            fallbackCopyMessage(textContent, messageId);
                        }
                    } catch (error) {
                        console.error('Message copy failed:', error);
                    }
                }
                
                function fallbackCopyMessage(text, messageId) {
                    try {
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.select();
                        
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textArea);
                        
                        if (successful) {
                            showMessageCopyFeedback(messageId);
                        }
                    } catch (err) {
                        console.error('Fallback message copy error:', err);
                    }
                }
                
                function copyHtmlMessage(messageId) {
                    try {
                        const contentDiv = document.getElementById(messageId + '_content');
                        if (!contentDiv) return;
                        
                        const htmlContent = contentDiv.innerHTML;
                        
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            navigator.clipboard.writeText(htmlContent).then(() => {
                                showHtmlCopyFeedback(messageId);
                            }).catch(() => {
                                fallbackCopyHtml(htmlContent, messageId);
                            });
                        } else {
                            fallbackCopyHtml(htmlContent, messageId);
                        }
                    } catch (error) {
                        console.error('HTML copy failed:', error);
                    }
                }
                
                function fallbackCopyHtml(html, messageId) {
                    try {
                        const textArea = document.createElement('textarea');
                        textArea.value = html;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.select();
                        
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textArea);
                        
                        if (successful) {
                            showHtmlCopyFeedback(messageId);
                        }
                    } catch (err) {
                        console.error('Fallback HTML copy error:', err);
                    }
                }
                
                function showMessageCopyFeedback(messageId) {
                    const messageDiv = document.getElementById(messageId);
                    if (messageDiv) {
                        const copyBtn = messageDiv.querySelector('button[title="메시지 복사"]');
                        if (copyBtn) {
                            const originalText = copyBtn.innerHTML;
                            copyBtn.innerHTML = '✓';
                            copyBtn.style.background = 'rgba(40,167,69,0.5)';
                            copyBtn.style.borderColor = 'rgba(40,167,69,0.4)';
                            copyBtn.style.opacity = '0.75';
                            copyBtn.style.transform = 'scale(1.05)';
                            
                            setTimeout(() => {
                                copyBtn.innerHTML = originalText;
                                copyBtn.style.background = 'rgba(95,95,100,0.45)';
                                copyBtn.style.borderColor = 'rgba(160,160,165,0.3)';
                                copyBtn.style.opacity = '0.5';
                                copyBtn.style.transform = 'scale(1)';
                            }, 2000);
                        }
                    }
                }
                
                function showHtmlCopyFeedback(messageId) {
                    const messageDiv = document.getElementById(messageId);
                    if (messageDiv) {
                        const copyBtn = messageDiv.querySelector('button[title="HTML 코드 복사"]');
                        if (copyBtn) {
                            const originalText = copyBtn.innerHTML;
                            copyBtn.innerHTML = '✓';
                            copyBtn.style.background = 'rgba(40,167,69,0.5)';
                            copyBtn.style.borderColor = 'rgba(40,167,69,0.4)';
                            copyBtn.style.opacity = '0.75';
                            copyBtn.style.transform = 'scale(1.05)';
                            
                            setTimeout(() => {
                                copyBtn.innerHTML = originalText;
                                copyBtn.style.background = 'rgba(75,85,99,0.45)';
                                copyBtn.style.borderColor = 'rgba(140,150,160,0.3)';
                                copyBtn.style.opacity = '0.5';
                                copyBtn.style.transform = 'scale(1)';
                            }, 2000);
                        }
                    }
                }
                
                function deleteMessage(messageId) {
                    try {
                        if (pyqt_bridge && pyqt_bridge.deleteMessage) {
                            pyqt_bridge.deleteMessage(messageId);
                        } else {
                            console.error('Delete message bridge not available');
                        }
                    } catch (error) {
                        console.error('Message delete failed:', error);
                    }
                }
                
                function removeMessageFromDOM(messageId) {
                    try {
                        const messageElements = document.querySelectorAll('[data-message-id="' + messageId + '"]');
                        messageElements.forEach(element => {
                            element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                            element.style.opacity = '0';
                            element.style.transform = 'translateX(-20px)';
                            setTimeout(() => {
                                element.remove();
                            }, 300);
                        });
                    } catch (error) {
                        console.error('DOM message removal failed:', error);
                    }
                }
                                
                function copyCode(codeId) {
                    try {
                        const codeElement = document.getElementById(codeId);
                        if (!codeElement) {
                            console.error('Code element not found:', codeId);
                            return;
                        }
                        
                        const codeText = codeElement.innerText || codeElement.textContent;
                        
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            navigator.clipboard.writeText(codeText).then(() => {
                                showCodeCopyFeedback(codeId);
                            }).catch(() => {
                                fallbackCopyCode(codeText, codeId);
                            });
                        } else {
                            fallbackCopyCode(codeText, codeId);
                        }
                    } catch (error) {
                        console.error('Code copy failed:', error);
                    }
                }
                
                function fallbackCopyCode(text, codeId) {
                    try {
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.select();
                        
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textArea);
                        
                        if (successful) {
                            showCodeCopyFeedback(codeId);
                        }
                    } catch (err) {
                        console.error('Fallback code copy error:', err);
                    }
                }
                
                function showCodeCopyFeedback(codeId) {
                    try {
                        const codeElement = document.getElementById(codeId);
                        if (codeElement) {
                            const codeContainer = codeElement.closest('div');
                            if (codeContainer) {
                                const copyBtn = codeContainer.querySelector('button');
                                if (copyBtn) {
                                    const originalText = copyBtn.innerHTML;
                                    copyBtn.innerHTML = '✓';
                                    copyBtn.style.background = '#28a745';
                                    copyBtn.style.opacity = '1';
                                    
                                    setTimeout(() => {
                                        copyBtn.innerHTML = originalText;
                                        copyBtn.style.background = '#444';
                                        copyBtn.style.opacity = '0.7';
                                    }, 2000);
                                }
                            }
                        }
                    } catch (error) {
                        console.error('Code copy feedback error:', error);
                    }
                }

        """

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
            <script>
            {javascript_code}
            </script>
            <style id="theme-style">
                {theme_css}
                
                /* 실제 성능 최적화 */
                * {{
                    box-sizing: border-box;
                }}
                
                html, body {{
                    background-color: {body_bg_color} !important;
                    scroll-behavior: smooth;
                    overflow-x: hidden;
                    -webkit-font-smoothing: antialiased;
                    -moz-osx-font-smoothing: grayscale;
                    margin: 0;
                    padding: 0;
                }}
                
                #messages {{
                    /* 가상화를 위한 최적화 */
                    height: auto;
                    overflow-y: visible;
                }}
                
                .message {{
                    /* GPU 레이어 생성 */
                    -webkit-transform: translate3d(0,0,0);
                    transform: translate3d(0,0,0);
                    /* 렌더링 최적화 */
                    -webkit-backface-visibility: hidden;
                    backface-visibility: hidden;
                    /* 레이아웃 최적화 */
                    contain: layout;
                }}
                
                /* Mermaid v10 다이어그램 전용 스타일 */
                .mermaid {{
                    background: {body_bg_color} !important;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 16px 0;
                    text-align: center;
                    overflow-x: auto;
                    min-height: 100px;
                }}
                
                .copy-btn {{
                    position: absolute;
                    top: 8px;
                    right: 8px;
                    background: #444;
                    color: #fff;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                    font-weight: 500;
                    z-index: 9999;
                    transition: all 0.2s ease;
                }}
            </style>
            <script>
                function showLoadedImage(imageId, imageUrl) {{
                    var loadingDiv = document.getElementById(imageId + '_loading');
                    var img = document.getElementById(imageId);
                    if (loadingDiv) loadingDiv.style.display = 'none';
                    if (img) img.style.display = 'block';
                }}
                
                function showImageError(imageId) {{
                    var loadingDiv = document.getElementById(imageId + '_loading');
                    if (loadingDiv) {{
                        loadingDiv.innerHTML = '<div style="color:#ff6b6b;text-align:center;">이미지 로드 실패</div>';
                    }}
                }}
                
                {webchannel_js}
            </script>
        </head>
        <body>
            <div id="messages"></div>
        </body>
        </html>
        """.replace(
            "{webchannel_js}", webchannel_js
        )
        self.web_view.setHtml(html_template)
        print("HTML 템플릿 로드 완료")

    def _get_current_theme_css(self) -> str:
        """현재 테마 CSS 반환"""
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            return theme_manager.material_manager.generate_web_css()
        else:
            from ui.styles.flat_theme import FlatTheme

            return FlatTheme.get_chat_display_css()

    def is_dark_theme(self) -> bool:
        """현재 테마가 다크 테마인지 확인"""
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            return theme_manager.material_manager.is_dark_theme()
        else:
            return True  # 기본 테마는 다크 테마로 간주

    def update_theme(self):
        """테마 업데이트 - 실시간 CSS 업데이트"""
        try:
            from ui.styles.theme_manager import theme_manager

            print(
                f"테마 업데이트 시작: {theme_manager.material_manager.current_theme_key}"
            )

            # 새로운 테마 CSS 가져오기
            theme_css = self._get_current_theme_css()

            # 배경색 가져오기
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                body_bg_color = colors.get("background", "#121212")
            else:
                from ui.styles.flat_theme import FlatTheme

                colors = FlatTheme.get_theme_colors()
                body_bg_color = colors.get("background", "#1a1a1a")

            # JavaScript로 실시간 테마 업데이트
            # f-string에서 백슬래시 사용을 피하기 위해 변수로 분리
            escaped_theme_css = theme_css.replace('`', r'\`')
            update_js = f"""
            try {{
                console.log('테마 업데이트 시작');
                
                // 배경색 업데이트
                document.body.style.backgroundColor = '{body_bg_color}';
                document.documentElement.style.backgroundColor = '{body_bg_color}';
                
                // 기존 테마 스타일 제거
                var existingStyle = document.getElementById('theme-style');
                if (existingStyle) {{
                    existingStyle.remove();
                }}
                
                // 새로운 테마 스타일 추가
                var newStyle = document.createElement('style');
                newStyle.id = 'theme-style';
                newStyle.textContent = `{escaped_theme_css}`;
                document.head.appendChild(newStyle);
                
                // Mermaid 다이어그램 배경색 업데이트
                var mermaidElements = document.querySelectorAll('.mermaid');
                mermaidElements.forEach(function(element) {{
                    element.style.backgroundColor = '{body_bg_color}';
                }});
                
                console.log('테마 업데이트 완료');
            }} catch(e) {{
                console.error('테마 업데이트 오류:', e);
            }}
            """

            self.web_view.page().runJavaScript(update_js)
            print("채팅 디스플레이 테마 업데이트 완료")

        except Exception as e:
            print(f"채팅 디스플레이 테마 업데이트 오류: {e}")

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

        # 발신자별 스타일
        if sender == "사용자":
            bg_color = colors.get("user_bg", "rgba(26, 26, 26, 0.3)")
            icon = "💬"
            sender_color = colors.get("text_secondary", "#cccccc")
            content_color = colors.get("text_primary", "#ffffff")
        elif sender in ["AI", "에이전트"] or "에이전트" in sender:
            bg_color = colors.get("ai_bg", "rgba(26, 26, 26, 0.3)")
            icon = "🤖"
            sender_color = colors.get("text_secondary", "#cccccc")
            content_color = colors.get("text_primary", "#ffffff")
        else:
            bg_color = colors.get("system_bg", "rgba(26, 26, 26, 0.3)")
            icon = "⚙️"
            sender_color = colors.get("text_secondary", "#999999")
            content_color = colors.get("text_secondary", "#b3b3b3")

        # 렌더링 확실히 보장하는 포맷터 사용
        from ui.fixed_formatter import FixedFormatter

        formatter = FixedFormatter()
        formatted_text = formatter.format_basic_markdown(text)

        # 이미지 URL 감지 및 렌더링 처리
        formatted_text = self._process_image_urls(formatted_text)

        display_message_id = message_id or f"msg_{uuid.uuid4().hex[:8]}"

        # 메시지 컨테이너 생성과 콘텐츠 설정을 한 번에 처리
        safe_content = json.dumps(formatted_text, ensure_ascii=False)

        # 삭제 버튼 HTML (시스템 메시지가 아닌 경우에만)
        delete_button_js = ""
        if sender != "시스템":
            # message_id가 없으면 display_message_id 사용
            delete_id = message_id if message_id else display_message_id
            delete_button_js = f"""
            var deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = '메시지 삭제';
            deleteBtn.style.cssText = 'position:absolute;top:18px;right:18px;background:rgba(220,53,69,0.6);color:#ffffff;border:1px solid rgba(220,53,69,0.8);padding:8px 10px;border-radius:8px;cursor:pointer;font-size:14px;font-weight:700;opacity:0.7;transition:all 0.2s ease;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;z-index:20;';
            deleteBtn.onclick = function() {{ 
                deleteMessage('{delete_id}'); 
            }};
            deleteBtn.onmouseenter = function() {{ 
                this.style.background = 'rgba(220,53,69,0.8)';
                this.style.borderColor = 'rgba(220,53,69,1.0)';
                this.style.opacity = '1.0';
                this.style.transform = 'scale(1.1)';
                /*this.style.boxShadow = '0 4px 12px rgba(220,53,69,0.5)';*/
            }};
            deleteBtn.onmouseleave = function() {{ 
                this.style.background = 'rgba(220,53,69,0.6)';
                this.style.borderColor = 'rgba(220,53,69,0.8)';
                this.style.opacity = '0.7';
                this.style.transform = 'scale(1)';
                /*this.style.boxShadow = '0 2px 8px rgba(220,53,69,0.3)';*/
            }};
            messageDiv.appendChild(deleteBtn);
            """

        combined_js = f"""
        try {{
            console.log('메시지 생성 및 콘텐츠 설정 시작: {display_message_id}');
            
            var messagesDiv = document.getElementById('messages');
            
            // 메시지 수 제한 (성능 최적화)
            var messageCount = messagesDiv.children.length;
            var maxMessages = 50; // 최대 50개 유지
            
            if (messageCount >= maxMessages) {{
                // 오래된 메시지 10개 제거
                for (var i = 0; i < 10 && messagesDiv.firstChild; i++) {{
                    var oldMsg = messagesDiv.firstChild;
                    messagesDiv.removeChild(oldMsg);
                    oldMsg = null; // 메모리 해제
                }}
                // 강제 가비지 콜렉션
                if (window.gc) window.gc();
            }}
            
            var messageDiv = document.createElement('div');
            messageDiv.id = '{display_message_id}';
            messageDiv.setAttribute('data-message-id', '{message_id or display_message_id}');
            messageDiv.className = 'message';
            messageDiv.style.cssText = 'margin:24px 0;padding:20px 20px;background:transparent;border-radius:4px;position:relative;border:none;';
            messageDiv.onmouseenter = function() {{ }};
            messageDiv.onmouseleave = function() {{ }};
            
            var headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'margin:0 0 8px 0;font-weight:600;color:{sender_color};font-size:12px;display:flex;align-items:center;gap:8px;opacity:0.8;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;';
            headerDiv.innerHTML = '<span style="font-size:16px;">{icon}</span><span>{sender}</span>';
            
            var copyBtn = document.createElement('button');
            copyBtn.innerHTML = '📋';
            copyBtn.title = '메시지 복사';
            copyBtn.style.cssText = 'position:absolute;top:18px;right:140px;background:rgba(95,95,100,0.45);color:rgba(208,208,208,0.7);border:1px solid rgba(160,160,165,0.3);padding:8px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700;opacity:0.5;transition:all 0.25s ease;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;z-index:15;';
            copyBtn.onclick = function() {{ copyMessage('{display_message_id}'); }};
            copyBtn.onmouseenter = function() {{ 
                this.style.background = 'rgba(105,105,110,0.475)';
                this.style.borderColor = 'rgba(180,180,185,0.4)';
                this.style.color = 'rgba(240,240,240,0.85)';
                this.style.opacity = '0.75';
                this.style.transform = 'scale(1.05)';
                /*this.style.boxShadow = '0 3px 6px rgba(0,0,0,0.175)';*/
            }};
            copyBtn.onmouseleave = function() {{ 
                this.style.background = 'rgba(95,95,100,0.45)';
                this.style.borderColor = 'rgba(160,160,165,0.3)';
                this.style.color = 'rgba(208,208,208,0.7)';
                this.style.opacity = '0.5';
                this.style.transform = 'scale(1)';
                /*this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.125)';*/
            }};
            
            var copyHtmlBtn = document.createElement('button');
            copyHtmlBtn.innerHTML = '🔗';
            copyHtmlBtn.title = 'HTML 코드 복사';
            copyHtmlBtn.style.cssText = 'position:absolute;top:18px;right:80px;background:rgba(75,85,99,0.45);color:rgba(168,178,188,0.7);border:1px solid rgba(140,150,160,0.3);padding:8px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700;opacity:0.5;transition:all 0.25s ease;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;z-index:15;/*box-shadow:0 2px 4px rgba(0,0,0,0.125);*/';
            copyHtmlBtn.onclick = function() {{ copyHtmlMessage('{display_message_id}'); }};
            copyHtmlBtn.onmouseenter = function() {{ 
                this.style.background = 'rgba(85,95,109,0.475)';
                this.style.borderColor = 'rgba(160,170,180,0.4)';
                this.style.color = 'rgba(200,210,220,0.85)';
                this.style.opacity = '0.75';
                this.style.transform = 'scale(1.05)';
                /*this.style.boxShadow = '0 3px 6px rgba(0,0,0,0.175)';*/
            }};
            copyHtmlBtn.onmouseleave = function() {{ 
                this.style.background = 'rgba(75,85,99,0.45)';
                this.style.borderColor = 'rgba(140,150,160,0.3)';
                this.style.color = 'rgba(168,178,188,0.7)';
                this.style.opacity = '0.5';
                this.style.transform = 'scale(1)';
                /*this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.125)';*/
            }};
            
            {delete_button_js}
            
            var contentDiv = document.createElement('div');
            contentDiv.id = '{display_message_id}_content';
            contentDiv.style.cssText = 'margin:0;padding-left:8px;padding-right:160px;line-height:1.6;color:{content_color};font-size:14px;word-wrap:break-word;font-weight:400;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;';
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(copyBtn);
            messageDiv.appendChild(copyHtmlBtn);
            messageDiv.appendChild(contentDiv);
            
            // prepend 옵션에 따라 상단 또는 하단에 추가
            if ({str(prepend).lower()}) {{
                messagesDiv.insertBefore(messageDiv, messagesDiv.firstChild);
            }} else {{
                messagesDiv.appendChild(messageDiv);
            }}
            
            // 콘텐츠 즉시 설정
            contentDiv.innerHTML = {safe_content};
            console.log('콘텐츠 설정 완료: {display_message_id}');
            
            // 렌더링 처리 (성능 최적화)
            requestAnimationFrame(() => {{
                console.log('렌더링 시작: {display_message_id}');
                
                // Mermaid 렌더링 (비동기) - ERD 전용 처리
                if (typeof mermaid !== 'undefined') {{
                    setTimeout(() => {{
                        try {{
                            console.log('Mermaid 렌더링 시도');
                            
                            // ERD 전용 초기화
                            const erdElements = contentDiv.querySelectorAll('.mermaid');
                            erdElements.forEach(element => {{
                                const content = element.textContent || element.innerHTML;
                                if (content.includes('erDiagram')) {{
                                    console.log('ERD 요소 발견, 재초기화');
                                    mermaid.initialize({{
                                        startOnLoad: false,
                                        theme: 'dark',
                                        securityLevel: 'loose',
                                        er: {{ useMaxWidth: true, layoutDirection: 'TB' }}
                                    }});
                                }}
                            }});
                            
                            mermaid.run();
                            console.log('Mermaid 렌더링 완료');
                        }} catch (e) {{
                            console.error('Mermaid 렌더링 오류:', e);
                        }}
                    }}, 100);
                }}
                
                // MathJax 렌더링 (비동기)
                if (window.MathJax && MathJax.typesetPromise) {{
                    setTimeout(() => {{
                        console.log('MathJax 렌더링 시도');
                        MathJax.typesetPromise([contentDiv])
                            .then(() => console.log('MathJax 렌더링 성공'))
                            .catch((err) => console.error('MathJax 렌더링 오류:', err));
                    }}, 100);
                }}
            }});
            
            // 스크롤 위치 조정 (prepend 옵션에 따라)
            setTimeout(() => {{
                if ({str(prepend).lower()}) {{
                    // prepend시 스크롤 위치 유지
                    var currentScrollY = window.scrollY;
                    var messageHeight = messageDiv.offsetHeight + 20; // 마진 포함
                    window.scrollTo(0, currentScrollY + messageHeight);
                }} else {{
                    // 일반 추가시 하단으로 스크롤
                    window.scrollTo(0, document.body.scrollHeight);
                }}
            }}, 10);
            console.log('메시지 생성 완료: {display_message_id}');
            
            // 메모리 정리
            if (messageCount > 40) {{
                setTimeout(() => {{
                    if (window.gc) window.gc();
                }}, 500);
            }}
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

    def _process_image_urls(self, text):
        """이미지 URL 및 유튜브 링크 감지 및 렌더링 처리"""
        import re
        import uuid

        # Pollination 이미지 URL 패턴 감지
        pollination_pattern = r"https://image\.pollinations\.ai/prompt/[^\s)]+"

        # 유튜브 URL 패턴 감지 (더 정확한 패턴)
        youtube_pattern = r'https?://(?:www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})(?:[^\s<>"]*)?'

        def replace_image_url(match):
            url = match.group(0)
            image_id = f"img_{uuid.uuid4().hex[:8]}"

            # CSS 애니메이션을 별도 문자열로 분리
            css_animation = """
            <style>
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            </style>
            """

            # HTML 콘텐츠
            html_content = f"""
            <div id="{image_id}_container" style="position: relative; display: inline-block; margin: 10px 0; min-height: 200px;">
                <div id="{image_id}_loading" style="
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    min-height: 200px; 
                    background: rgba(40,40,40,0.8); 
                    border-radius: 8px; 
                    border: 2px dashed #666;
                ">
                    <div style="text-align: center; color: #ccc;">
                        <div style="font-size: 24px; margin-bottom: 10px;">🎨</div>
                        <div style="font-size: 14px; margin-bottom: 5px;">이미지 생성 중...</div>
                        <div style="font-size: 12px; opacity: 0.7;">잠시만 기다려주세요</div>
                        <div class="loading-spinner" style="
                            margin: 10px auto;
                            width: 20px;
                            height: 20px;
                            border: 2px solid #666;
                            border-top: 2px solid #87CEEB;
                            border-radius: 50%;
                            animation: spin 1s linear infinite;
                        "></div>
                    </div>
                </div>
                
                <img id="{image_id}" src="{url}" alt="Generated Image" 
                     style="display: none; max-width: 100%; height: auto; border-radius: 8px; /*box-shadow: 0 4px 8px rgba(0,0,0,0.3);*/" 
                     onload="if(typeof showLoadedImage === 'function') showLoadedImage('{image_id}', '{url}')" 
                     onerror="if(typeof showImageError === 'function') showImageError('{image_id}')" />
            </div>
            """

            return css_animation + html_content

        def replace_youtube_url(match):
            full_url = match.group(0)
            video_id = match.group(2)

            # 전체화면 지원을 위한 완전한 iframe 설정
            return f'\n\n<div style="margin:10px 0;padding:10px;background:rgba(40,40,40,0.5);border-radius:8px;"><p style="color:#87CEEB;margin:0 0 10px 0;font-size:14px;">📺 YouTube: <a href="{full_url}" target="_blank" style="color:#87CEEB;">{video_id}</a></p><iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}?enablejsapi=1&fs=1&modestbranding=1&rel=0&showinfo=0" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen webkitallowfullscreen mozallowfullscreen></iframe></div>\n\n'

        # 유튜브 URL을 먼저 처리 (더 긴 패턴이므로)
        processed_text = re.sub(youtube_pattern, replace_youtube_url, text)

        # 이미지 URL을 이미지 태그로 변환
        processed_text = re.sub(pollination_pattern, replace_image_url, processed_text)

        return processed_text


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
    def saveImage(self, image_url):
        """이미지 저장"""
        try:
            from PyQt6.QtWidgets import QFileDialog, QApplication
            from PyQt6.QtCore import QThread, pyqtSignal
            import requests
            import os

            # 파일 저장 대화상자
            filename, _ = QFileDialog.getSaveFileName(
                None,
                "이미지 저장",
                "pollination_image.png",
                "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
            )

            if filename:
                # 백그라운드에서 이미지 다운로드
                self.download_thread = ImageDownloadThread(image_url, filename)
                self.download_thread.finished.connect(self.on_download_finished)
                self.download_thread.error.connect(self.on_download_error)
                self.download_thread.start()

        except Exception as e:
            print(f"이미지 저장 오류: {e}")

    def on_download_finished(self, filename):
        """다운로드 완료 처리"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            None, "저장 완료", f"이미지가 저장되었습니다:\n{filename}"
        )

    def on_download_error(self, error_msg):
        """다운로드 오류 처리"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(
            None, "저장 실패", f"이미지 저장 중 오류가 발생했습니다:\n{error_msg}"
        )

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

    @pyqtSlot()
    def onScrollToTop(self):
        """스크롤이 상단에 도달했을 때 호출"""
        try:
            print("[SCROLL] 상단 도달 - 더 많은 메시지 로드 시도")
            if self.chat_widget and hasattr(self.chat_widget, "load_more_messages"):
                self.chat_widget.load_more_messages()
        except Exception as e:
            print(f"[SCROLL] 오류: {e}")


class ImageDownloadThread(QThread):
    """이미지 다운로드 스레드"""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, filename):
        super().__init__()
        self.url = url
        self.filename = filename

    def run(self):
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()

            with open(self.filename, "wb") as f:
                f.write(response.content)

            self.finished.emit(self.filename)
        except Exception as e:
            self.error.emit(str(e))
