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
            ui_settings = config.get('ui_settings', {})
            progressive_settings = ui_settings.get('progressive_display', {})
            
            self.progressive_enabled = progressive_settings.get('enabled', True)
            self.delay_per_line = progressive_settings.get('delay_per_line', 30)
            self.initial_delay = progressive_settings.get('initial_delay', 100)
        except Exception as e:
            # 설정 로드 실패 시 기본값 사용
            self.progressive_enabled = True
            self.delay_per_line = 30
            self.initial_delay = 100
    
    def init_web_view(self):
        """웹 브라우저 초기화 - 고급 다크 테마"""
        from ui.styles.theme_manager import theme_manager
        
        # 웹 보안 설정 완화
        settings = self.web_view.settings()
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(settings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(settings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(settings.WebAttribute.AllowRunningInsecureContent, True)
        
        # 웹뷰 배경 투명 설정
        self.web_view.page().setBackgroundColor(self.web_view.palette().color(self.web_view.palette().ColorRole.Window))
        
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
                            theme: '{mermaid_theme}',
                            securityLevel: 'loose',
                            flowchart: {{ useMaxWidth: true, htmlLabels: true }},
                            sequence: {{ useMaxWidth: true, wrap: true }},
                            gantt: {{ useMaxWidth: true, gridLineStartPadding: 350 }},
                            journey: {{ useMaxWidth: true }},
                            class: {{ useMaxWidth: true }},
                            state: {{ useMaxWidth: true }},
                            er: {{ useMaxWidth: true }},
                            pie: {{ useMaxWidth: true }},
                            requirement: {{ useMaxWidth: true }},
                            gitgraph: {{ useMaxWidth: true }},
                            c4: {{ useMaxWidth: true }},
                            mindmap: {{ useMaxWidth: true }},
                            timeline: {{ useMaxWidth: true }},
                            sankey: {{ useMaxWidth: true }},
                            xyChart: {{ useMaxWidth: true }},
                            block: {{ useMaxWidth: true }},
                            packet: {{ useMaxWidth: true }},
                            architecture: {{ useMaxWidth: true }}
                        }});
                        console.log('Mermaid v10 모든 다이어그램 유형 초기화 완료');
                    }}
                }});
                
                function rerenderMermaid() {{
                    if (typeof mermaid !== 'undefined') {{
                        try {{
                            const mermaidElements = document.querySelectorAll('.mermaid');
                            mermaidElements.forEach(element => {{
                                let content = element.textContent || element.innerHTML;
                                
                                if (content.includes('erDiagram')) {{
                                    content = content.replace(/: "([^"]+)"/g, ': $1');
                                    content = content.replace(/: '([^']+)'/g, ': $1');
                                    element.textContent = content;
                                }}
                                
                                content = content.replace(/--&gt;/g, '-->');
                                content = content.replace(/&#45;&#45;&#45;/g, '---');
                                content = content.replace(/-&gt;&gt;/g, '->');
                                
                                if (element.textContent !== content) {{
                                    element.textContent = content;
                                }}
                            }});
                            
                            mermaid.run();
                            console.log('Mermaid 재렌더링 완료');
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
            <script src="https://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>
            <script>
            {javascript_code}
            </script>
            <style id="theme-style">
                {theme_css}
                
                /* Mermaid v10 다이어그램 전용 스타일 */
                .mermaid {{
                    background: #2a2a2a;
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
        """.replace('{webchannel_js}', webchannel_js)
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
        """테마 업데이트 - 웹뷰 완전 다시 로드"""
        try:
            from ui.styles.theme_manager import theme_manager
            print(f"테마 업데이트 시작: {theme_manager.material_manager.current_theme_key}")
            self.init_web_view()
            print("채팅 디스플레이 테마 업데이트 완료")
        except Exception as e:
            print(f"채팅 디스플레이 테마 업데이트 오류: {e}")
    
    def _setup_link_handler(self):
        """링크 클릭 핸들러 설정"""
        from PyQt6.QtWebChannel import QWebChannel
        
        # 웹 채널 설정
        self.channel = QWebChannel()
        self.link_handler = LinkHandler()
        self.channel.registerObject('pyqt_bridge', self.link_handler)
        self.web_view.page().setWebChannel(self.channel)
    
    def set_chat_widget(self, chat_widget):
        """채팅 위젯 참조 설정"""
        self.link_handler.chat_widget = chat_widget
    
    def append_message(self, sender, text, original_sender=None, progressive=False, message_id=None):
        """메시지 추가 - progressive=True시 점진적 출력"""
        # 테마에 따른 색상 가져오기
        from ui.styles.theme_manager import theme_manager
        colors = theme_manager.material_manager.get_theme_colors() if theme_manager.use_material_theme else {}
        
        # 발신자별 스타일
        if sender == '사용자':
            bg_color = colors.get('user_bg', 'rgba(26, 26, 26, 0.3)')
            icon = '💬'
            sender_color = colors.get('text_secondary', '#cccccc')
            content_color = colors.get('text_primary', '#ffffff')
        elif sender in ['AI', '에이전트'] or '에이전트' in sender:
            bg_color = colors.get('ai_bg', 'rgba(26, 26, 26, 0.3)')
            icon = '🤖'
            sender_color = colors.get('text_secondary', '#cccccc')
            content_color = colors.get('text_primary', '#ffffff')
        else:
            bg_color = colors.get('system_bg', 'rgba(26, 26, 26, 0.3)')
            icon = '⚙️'
            sender_color = colors.get('text_secondary', '#999999')
            content_color = colors.get('text_secondary', '#b3b3b3')
        
        # 렌더링 확실히 보장하는 포맷터 사용
        from ui.fixed_formatter import FixedFormatter
        
        formatter = FixedFormatter()
        formatted_text = formatter.format_basic_markdown(text)
        
        # 이미지 URL 감지 및 렌더링 처리
        formatted_text = self._process_image_urls(formatted_text)
        
        display_message_id = message_id or f"msg_{uuid.uuid4().hex[:8]}"
        
        # 메시지 컨테이너 생성과 콘텐츠 설정을 한 번에 처리
        safe_content = json.dumps(formatted_text, ensure_ascii=False)
        
        # 시스템 메시지가 아닌 경우에만 삭제 버튼 추가
        delete_button_html = ""
        if sender != '시스템' and message_id:
            delete_button_html = f'''
            var deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = '메시지 삭제';
            deleteBtn.style.cssText = 'position:absolute;top:18px;right:18px;background:rgba(220,53,69,0.4);color:rgba(255,255,255,0.7);border:1px solid rgba(220,53,69,0.3);padding:8px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700;opacity:0.5;transition:all 0.25s ease;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;z-index:15;box-shadow:0 2px 4px rgba(0,0,0,0.125);';
            deleteBtn.onclick = function() {{ deleteMessage('{message_id}'); }};
            deleteBtn.onmouseenter = function() {{ 
                this.style.background = 'rgba(220,53,69,0.475)';
                this.style.borderColor = 'rgba(220,53,69,0.4)';
                this.style.color = 'rgba(255,255,255,0.9)';
                this.style.opacity = '0.75';
                this.style.transform = 'scale(1.05)';
                this.style.boxShadow = '0 3px 6px rgba(0,0,0,0.175)';
            }};
            deleteBtn.onmouseleave = function() {{ 
                this.style.background = 'rgba(220,53,69,0.4)';
                this.style.borderColor = 'rgba(220,53,69,0.3)';
                this.style.color = 'rgba(255,255,255,0.7)';
                this.style.opacity = '0.5';
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.125)';
            }};
            messageDiv.appendChild(deleteBtn);
            '''
        
        combined_js = f'''
        try {{
            console.log('메시지 생성 및 콘텐츠 설정 시작: {display_message_id}');
            
            var messagesDiv = document.getElementById('messages');
            var messageDiv = document.createElement('div');
            messageDiv.id = '{display_message_id}';
            messageDiv.setAttribute('data-message-id', '{message_id or ""}');
            messageDiv.style.cssText = 'margin:20px 0;padding:20px 20px;background:{bg_color};border-radius:4px;position:relative;border:none;';
            messageDiv.onmouseenter = function() {{ }};
            messageDiv.onmouseleave = function() {{ }};
            
            var headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'margin:0 0 8px 0;font-weight:600;color:{sender_color};font-size:12px;display:flex;align-items:center;gap:8px;opacity:0.8;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;';
            headerDiv.innerHTML = '<span style="font-size:16px;">{icon}</span><span>{sender}</span>';
            
            var copyBtn = document.createElement('button');
            copyBtn.innerHTML = '📋';
            copyBtn.title = '메시지 복사';
            copyBtn.style.cssText = 'position:absolute;top:18px;right:120px;background:rgba(95,95,100,0.45);color:rgba(208,208,208,0.7);border:1px solid rgba(160,160,165,0.3);padding:8px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700;opacity:0.5;transition:all 0.25s ease;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;z-index:15;box-shadow:0 2px 4px rgba(0,0,0,0.125);';
            copyBtn.onclick = function() {{ copyMessage('{display_message_id}'); }};
            copyBtn.onmouseenter = function() {{ 
                this.style.background = 'rgba(105,105,110,0.475)';
                this.style.borderColor = 'rgba(180,180,185,0.4)';
                this.style.color = 'rgba(240,240,240,0.85)';
                this.style.opacity = '0.75';
                this.style.transform = 'scale(1.05)';
                this.style.boxShadow = '0 3px 6px rgba(0,0,0,0.175)';
            }};
            copyBtn.onmouseleave = function() {{ 
                this.style.background = 'rgba(95,95,100,0.45)';
                this.style.borderColor = 'rgba(160,160,165,0.3)';
                this.style.color = 'rgba(208,208,208,0.7)';
                this.style.opacity = '0.5';
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.125)';
            }};
            
            var copyHtmlBtn = document.createElement('button');
            copyHtmlBtn.innerHTML = '🔗';
            copyHtmlBtn.title = 'HTML 코드 복사';
            copyHtmlBtn.style.cssText = 'position:absolute;top:18px;right:70px;background:rgba(75,85,99,0.45);color:rgba(168,178,188,0.7);border:1px solid rgba(140,150,160,0.3);padding:8px 10px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:700;opacity:0.5;transition:all 0.25s ease;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;z-index:15;box-shadow:0 2px 4px rgba(0,0,0,0.125);';
            copyHtmlBtn.onclick = function() {{ copyHtmlMessage('{display_message_id}'); }};
            copyHtmlBtn.onmouseenter = function() {{ 
                this.style.background = 'rgba(85,95,109,0.475)';
                this.style.borderColor = 'rgba(160,170,180,0.4)';
                this.style.color = 'rgba(200,210,220,0.85)';
                this.style.opacity = '0.75';
                this.style.transform = 'scale(1.05)';
                this.style.boxShadow = '0 3px 6px rgba(0,0,0,0.175)';
            }};
            copyHtmlBtn.onmouseleave = function() {{ 
                this.style.background = 'rgba(75,85,99,0.45)';
                this.style.borderColor = 'rgba(140,150,160,0.3)';
                this.style.color = 'rgba(168,178,188,0.7)';
                this.style.opacity = '0.5';
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 2px 4px rgba(0,0,0,0.125)';
            }};
            
            {delete_button_html}
            
            var contentDiv = document.createElement('div');
            contentDiv.id = '{display_message_id}_content';
            contentDiv.style.cssText = 'margin:0;padding-left:8px;padding-right:130px;line-height:1.6;color:{content_color};font-size:14px;word-wrap:break-word;font-weight:400;font-family:"Malgun Gothic","맑은 고딕","Apple SD Gothic Neo",sans-serif;';
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(copyBtn);
            messageDiv.appendChild(copyHtmlBtn);
            messageDiv.appendChild(contentDiv);
            messagesDiv.appendChild(messageDiv);
            
            // 콘텐츠 즉시 설정
            contentDiv.innerHTML = {safe_content};
            console.log('콘텐츠 설정 완료: {display_message_id}');
            
            // 렌더링 처리
            setTimeout(() => {{
                console.log('렌더링 시작: {display_message_id}');
                
                // Mermaid 렌더링
                if (typeof mermaid !== 'undefined') {{
                    try {{
                        console.log('Mermaid 렌더링 시도');
                        mermaid.run();
                        console.log('Mermaid 렌더링 완료');
                    }} catch (e) {{
                        console.error('Mermaid 렌더링 오류:', e);
                    }}
                }}
                
                // MathJax 강제 렌더링
                setTimeout(() => {{
                    if (window.MathJax && MathJax.typesetPromise) {{
                        console.log('MathJax 강제 렌더링 시도');
                        MathJax.typesetPromise([contentDiv])
                            .then(() => {{
                                console.log('MathJax 강제 렌더링 성공');
                            }})
                            .catch((err) => {{
                                console.error('MathJax 강제 렌더링 오류:', err);
                                // 실패 시 전체 렌더링 시도
                                MathJax.typesetPromise().catch(e => console.error('MathJax 전체 렌더링 실패:', e));
                            }});
                    }} else {{
                        console.log('MathJax 사용 불가');
                    }}
                }}, 200);
            }}, 100);
            
            window.scrollTo(0, document.body.scrollHeight);
            console.log('메시지 생성 완료: {display_message_id}');
        }} catch(e) {{
            console.error('메시지 생성 오류:', e);
        }}
        '''
        
        if progressive and self.progressive_enabled:
            # 점진적 출력 요청 시 - 먼저 빈 컨테이너 생성
            empty_js = combined_js.replace(f'contentDiv.innerHTML = {safe_content};', 'contentDiv.innerHTML = "";')
            self.web_view.page().runJavaScript(empty_js)
            QTimer.singleShot(self.initial_delay, lambda: self.progressive_display.display_text_progressively(
                display_message_id, formatted_text, delay_per_line=self.delay_per_line
            ))
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
        """이미지 URL 감지 및 렌더링 처리"""
        import re
        import uuid
        
        # Pollination 이미지 URL 패턴 감지
        pollination_pattern = r'https://image\.pollinations\.ai/prompt/[^\s)]+'
        
        def replace_image_url(match):
            url = match.group(0)
            image_id = f"img_{uuid.uuid4().hex[:8]}"
            
            # CSS 애니메이션을 별도 문자열로 분리
            css_animation = '''
            <style>
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            </style>
            '''
            
            # HTML 콘텐츠
            html_content = f'''
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
                     style="display: none; max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);" 
                     onload="if(typeof showLoadedImage === 'function') showLoadedImage('{image_id}', '{url}')" 
                     onerror="if(typeof showImageError === 'function') showImageError('{image_id}')" />
            </div>
            '''
            
            return css_animation + html_content
        
        # URL을 이미지 태그로 변환
        processed_text = re.sub(pollination_pattern, replace_image_url, text)
        
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
                "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
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
        QMessageBox.information(None, "저장 완료", f"이미지가 저장되었습니다:\n{filename}")
    
    def on_download_error(self, error_msg):
        """다운로드 오류 처리"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(None, "저장 실패", f"이미지 저장 중 오류가 발생했습니다:\n{error_msg}")
    
    @pyqtSlot(str)
    def deleteMessage(self, message_id):
        """메시지 삭제"""
        try:
            if self.chat_widget and hasattr(self.chat_widget, 'delete_message'):
                success = self.chat_widget.delete_message(message_id)
                if success:
                    # DOM에서 메시지 제거
                    self.chat_widget.chat_display.web_view.page().runJavaScript(
                        f"removeMessageFromDOM('{message_id}')"
                    )
                else:
                    print(f"메시지 삭제 실패: {message_id}")
            else:
                print("메시지 삭제 기능을 사용할 수 없습니다")
        except Exception as e:
            print(f"메시지 삭제 오류: {e}")


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
            
            with open(self.filename, 'wb') as f:
                f.write(response.content)
            
            self.finished.emit(self.filename)
        except Exception as e:
            self.error.emit(str(e))