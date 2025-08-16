from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer, QUrl, QObject, pyqtSlot
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
        """웹 브라우저 초기화"""
        from ui.styles.theme_manager import theme_manager
        
        theme_css = theme_manager.generate_theme_css()
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
            <script>
                window.MathJax = {
                    tex: {
                        inlineMath: [['$', '$'], ['\\(', '\\)']],
                        displayMath: [['$$', '$$'], ['\\[', '\\]']],
                        processEscapes: true,
                        processEnvironments: true
                    },
                    options: {
                        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
                        ignoreHtmlClass: 'tex2jax_ignore',
                        processHtmlClass: 'tex2jax_process'
                    },
                    startup: {
                        ready: () => {
                            MathJax.startup.defaultReady();
                            console.log('MathJax is loaded and ready.');
                        }
                    }
                };
            </script>
            <style>
                * { box-sizing: border-box; }
                
                body {
                    background-color: #1a1a1a;
                    color: #e8e8e8;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    margin: 8px;
                    padding: 0;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                }
                
                pre {
                    background: #1e1e1e;
                    color: #f8f8f2;
                    padding: 20px;
                    border-radius: 8px;
                    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, Monaco, monospace;
                    font-size: 13px;
                    line-height: 1.5;
                    overflow-x: auto;
                    white-space: pre;
                    tab-size: 4;
                    border: 1px solid #444;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    position: relative;
                }
                
                code {
                    background-color: #2d2d2d;
                    color: #f8f8f2;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
                    font-size: 12px;
                    border: 1px solid #444;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    margin-top: 24px;
                    margin-bottom: 12px;
                    font-weight: 600;
                    line-height: 1.25;
                }
                
                h1 { font-size: 24px; color: #ffffff; border-bottom: 2px solid #444; padding-bottom: 8px; }
                h2 { font-size: 20px; color: #eeeeee; border-bottom: 1px solid #333; padding-bottom: 6px; }
                h3 { font-size: 18px; color: #dddddd; }
                h4 { font-size: 16px; color: #cccccc; }
                h5 { font-size: 14px; color: #bbbbbb; }
                h6 { font-size: 13px; color: #aaaaaa; }
                
                a {
                    color: #87CEEB;
                    text-decoration: none;
                    border-bottom: 1px dotted #87CEEB;
                    transition: all 0.2s ease;
                }
                
                a:hover {
                    color: #B0E0E6;
                    border-bottom: 1px solid #B0E0E6;
                }
                
                ul, ol {
                    padding-left: 20px;
                    margin: 12px 0;
                }
                
                li {
                    margin: 4px 0;
                    color: #cccccc;
                }
                
                blockquote {
                    margin: 16px 0;
                    padding: 12px 16px;
                    border-left: 4px solid #87CEEB;
                    background-color: rgba(135, 206, 235, 0.1);
                    color: #dddddd;
                    font-style: italic;
                }
                
                table {
                    border-collapse: collapse;
                    width: auto;
                    margin: 16px 0;
                    background-color: #2a2a2a;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
                
                th, td {
                    padding: 12px 16px;
                    text-align: left;
                    border: 1px solid #444;
                    white-space: normal;
                    word-wrap: break-word;
                    vertical-align: top;
                }
                
                th {
                    background: linear-gradient(135deg, #3a3a3a, #4a4a4a);
                    color: #ffffff;
                    font-weight: 700;
                    font-size: 13px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                tr:nth-child(even) {
                    background-color: #252525;
                }
                
                tr:hover {
                    background-color: #333333;
                }
                
                hr {
                    border: none;
                    height: 2px;
                    background: linear-gradient(to right, transparent, #444, transparent);
                    margin: 20px 0;
                }
                
                strong {
                    color: #ffffff;
                    font-weight: 600;
                }
                
                em {
                    color: #dddddd;
                    font-style: italic;
                }
                
                del {
                    color: #888888;
                    text-decoration: line-through;
                }
                
                .message {
                    margin: 16px 0;
                    padding: 16px;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }
                
                .user { background: rgba(163,135,215,0.15); border-left: 4px solid rgb(163,135,215); }
                .ai { background: rgba(135,163,215,0.15); border-left: 4px solid rgb(135,163,215); }
                .system { background: rgba(215,163,135,0.15); border-left: 4px solid rgb(215,163,135); }
                
                ::-webkit-scrollbar {
                    width: 8px;
                    height: 8px;
                }
                
                ::-webkit-scrollbar-track {
                    background: #2a2a2a;
                    border-radius: 4px;
                }
                
                ::-webkit-scrollbar-thumb {
                    background: #555;
                    border-radius: 4px;
                }
                
                ::-webkit-scrollbar-thumb:hover {
                    background: #666;
                }
                
                .copy-btn {
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
                }
                
                .copy-btn:hover {
                    background: #555;
                }
                
                .copy-btn:active {
                    background: #666;
                }
            </style>
            <script>
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
                });
                
                function copyCode(codeId) {
                    try {
                        const codeElement = document.getElementById(codeId);
                        if (!codeElement) {
                            console.error('Code element not found:', codeId);
                            return;
                        }
                        
                        const textContent = codeElement.textContent || codeElement.innerText;
                        
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            navigator.clipboard.writeText(textContent).then(() => {
                                showCopyFeedback(codeId);
                            }).catch(err => {
                                console.error('Clipboard API failed:', err);
                                fallbackCopyText(textContent, codeId);
                            });
                        } else {
                            fallbackCopyText(textContent, codeId);
                        }
                    } catch (error) {
                        console.error('Copy failed:', error);
                    }
                }
                
                function fallbackCopyText(text, codeId) {
                    try {
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        textArea.style.top = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textArea);
                        
                        if (successful) {
                            showCopyFeedback(codeId);
                        } else {
                            console.error('Fallback copy failed');
                        }
                    } catch (err) {
                        console.error('Fallback copy error:', err);
                    }
                }
                
                function showCopyFeedback(codeId) {
                    const button = document.querySelector(`button[onclick="copyCode('${codeId}')"]`);
                    if (button) {
                        const originalText = button.textContent;
                        button.textContent = '복사됨!';
                        button.style.background = '#28a745';
                        
                        setTimeout(() => {
                            button.textContent = originalText;
                            button.style.background = '#444';
                        }, 2000);
                    }
                }
                
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
                
                function showMessageCopyFeedback(messageId) {
                    const messageDiv = document.getElementById(messageId);
                    if (messageDiv) {
                        const copyBtn = messageDiv.querySelector('button');
                        if (copyBtn) {
                            const originalText = copyBtn.textContent;
                            copyBtn.textContent = '✓ 복사됨!';
                            copyBtn.style.background = '#28a745';
                            copyBtn.style.borderColor = '#28a745';
                            copyBtn.style.transform = 'scale(1.05)';
                            
                            setTimeout(() => {
                                copyBtn.textContent = originalText;
                                copyBtn.style.background = 'rgba(0,0,0,0.7)';
                                copyBtn.style.borderColor = 'rgba(255,255,255,0.2)';
                                copyBtn.style.transform = 'scale(1)';
                            }, 2000);
                        }
                    }
                }
                
                function renderMath() {
                    if (window.MathJax && window.MathJax.typesetPromise) {
                        window.MathJax.typesetPromise().catch(function (err) {
                            console.log('MathJax typeset failed: ' + err.message);
                        });
                    }
                }
            </script>
        </head>
        <body>
            <div id="messages"></div>
        </body>
        </html>
        """
        self.web_view.setHtml(html_template)
    
    def _setup_link_handler(self):
        """링크 클릭 핸들러 설정"""
        from PyQt6.QtWebChannel import QWebChannel
        
        # 웹 채널 설정
        self.channel = QWebChannel()
        self.link_handler = LinkHandler()
        self.channel.registerObject('pyqt_bridge', self.link_handler)
        self.web_view.page().setWebChannel(self.channel)
    
    def append_message(self, sender, text, original_sender=None, progressive=False):
        """메시지 추가 - progressive=True시 점진적 출력"""
        # 발신자별 스타일
        if sender == '사용자':
            bg_color = 'rgba(163,135,215,0.15)'
            border_color = 'rgb(163,135,215)'
            icon = '💬'
            sender_color = 'rgb(163,135,215)'
        elif sender in ['AI', '에이전트'] or '에이전트' in sender:
            bg_color = 'rgba(135,163,215,0.15)'
            border_color = 'rgb(135,163,215)'
            icon = '🤖'
            sender_color = 'rgb(135,163,215)'
        else:
            bg_color = 'rgba(215,163,135,0.15)'
            border_color = 'rgb(215,163,135)'
            icon = '⚙️'
            sender_color = 'rgb(215,163,135)'
        
        # 마크다운 처리 - 모든 텍스트에 마크다운 포매팅 적용
        from ui.markdown_formatter import MarkdownFormatter
        from ui.table_formatter import TableFormatter
        
        markdown_formatter = MarkdownFormatter()
        table_formatter = TableFormatter()
        
        # 모든 텍스트에 마크다운 포매팅 적용
        formatted_text = markdown_formatter.format_basic_markdown(text)
        
        # 테이블이 있는 경우 추가로 인텔리전트 포매터 적용
        has_table = '|' in text and table_formatter.is_markdown_table(text)
        has_mixed = table_formatter.has_mixed_content(text)
        
        if has_table or has_mixed:
            from ui.intelligent_formatter import IntelligentContentFormatter
            formatter = IntelligentContentFormatter()
            format_sender = original_sender if original_sender else sender
            formatted_text = formatter.format_content(text, format_sender)
        
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        
        # 메시지 컨테이너 생성
        create_js = f'''
        try {{
            var messagesDiv = document.getElementById('messages');
            var messageDiv = document.createElement('div');
            messageDiv.id = '{message_id}';
            messageDiv.style.cssText = 'margin:8px 0;padding:12px;background:{bg_color};border-radius:8px;border-left:3px solid {border_color};position:relative;transition:all 0.3s cubic-bezier(0.4, 0, 0.2, 1);transform:translateY(0);box-shadow:none;';
            messageDiv.onmouseenter = function() {{ this.style.transform = 'translateY(-1px)'; this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'; }};
            messageDiv.onmouseleave = function() {{ this.style.transform = 'translateY(0)'; this.style.boxShadow = 'none'; }};
            
            var headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'margin:0 0 8px 0;font-weight:600;color:{sender_color};font-size:12px;display:flex;align-items:center;gap:8px;opacity:0.8;';
            headerDiv.innerHTML = '<span style="font-size:16px;">{icon}</span><span>{sender}</span>';
            
            var copyBtn = document.createElement('button');
            copyBtn.innerHTML = '📋 복사';
            copyBtn.style.cssText = 'position:absolute;top:8px;right:8px;background:rgba(0,0,0,0.7);color:white;border:1px solid rgba(255,255,255,0.2);padding:6px 10px;border-radius:6px;cursor:pointer;font-size:11px;font-weight:500;opacity:1;transition:all 0.3s cubic-bezier(0.4, 0, 0.2, 1);transform:scale(1);backdrop-filter:blur(4px);z-index:9999;';
            copyBtn.onclick = function() {{ copyMessage('{message_id}'); }};
            copyBtn.onmouseenter = function() {{ this.style.background = 'rgba(0,0,0,0.8)'; this.style.borderColor = 'rgba(255,255,255,0.3)'; }};
            copyBtn.onmouseleave = function() {{ this.style.background = 'rgba(0,0,0,0.7)'; this.style.borderColor = 'rgba(255,255,255,0.2)'; }};
            
            messageDiv.onmouseenter = function() {{ 
                this.style.transform = 'translateY(-2px) scale(1.01)'; 
                this.style.boxShadow = '0 8px 25px rgba(0,0,0,0.2)'; 
                copyBtn.style.opacity = '1';
                copyBtn.style.transform = 'scale(1.05)';
            }};
            messageDiv.onmouseleave = function() {{ 
                this.style.transform = 'translateY(0) scale(1)'; 
                this.style.boxShadow = 'none'; 
                copyBtn.style.opacity = '0.7';
                copyBtn.style.transform = 'scale(1)';
            }};
            
            var contentDiv = document.createElement('div');
            contentDiv.id = '{message_id}_content';
            contentDiv.style.cssText = 'margin:0;padding-left:4px;line-height:1.6;color:#ffffff;font-size:13px;word-wrap:break-word;';
            
            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(copyBtn);
            messageDiv.appendChild(contentDiv);
            messagesDiv.appendChild(messageDiv);
            window.scrollTo(0, document.body.scrollHeight);
        }} catch(e) {{
            console.log('Create message error:', e);
        }}
        '''
        
        # 콘텐츠 설정
        def set_content():
            safe_content = json.dumps(formatted_text, ensure_ascii=False)
            content_js = f'''
            try {{
                var contentDiv = document.getElementById('{message_id}_content');
                if (contentDiv) {{
                    contentDiv.innerHTML = {safe_content};
                    renderMath();
                    window.scrollTo(0, document.body.scrollHeight);
                }}
            }} catch(e) {{
                console.log('Set content error:', e);
            }}
            '''
            self.web_view.page().runJavaScript(content_js)
        
        self.web_view.page().runJavaScript(create_js)
        
        if progressive and self.progressive_enabled:
            # 점진적 출력 요청 시 - config 설정 사용
            QTimer.singleShot(self.initial_delay, lambda: self.progressive_display.display_text_progressively(
                message_id, formatted_text, delay_per_line=self.delay_per_line
            ))
        else:
            # 일반 출력
            QTimer.singleShot(50, set_content)
    
    def clear_messages(self):
        """메시지 초기화"""
        self.progressive_display.cancel_current_display()
        self.init_web_view()
    
    def cancel_progressive_display(self):
        """점진적 출력 취소"""
        self.progressive_display.cancel_current_display()


class LinkHandler(QObject):
    """링크 클릭 처리를 위한 핸들러"""
    
    def __init__(self):
        super().__init__()
    
    @pyqtSlot(str)
    def openUrl(self, url):
        """URL을 기본 브라우저에서 열기"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            print(f"URL 열기 오류: {e}")