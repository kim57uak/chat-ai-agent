from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer, QUrl, QObject, pyqtSlot, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from ui.components.progressive_display import ProgressiveDisplay
from ui.performance_optimizer import performance_optimizer
import json
import uuid

from core.logging import get_logger

logger = get_logger("chat_display")

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

        # PyQt6에서 지원하는 속성만 안전하게 사용
        try:
            settings.setAttribute(
                settings.WebAttribute.AllowRunningInsecureContent, True
            )
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"AllowRunningInsecureContent 설정 실패 (무시됨): {e}")
        
        try:
            settings.setAttribute(
                settings.WebAttribute.PlaybackRequiresUserGesture, False
            )
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"PlaybackRequiresUserGesture 설정 실패 (무시됨): {e}")

        # 웹뷰 배경 설정 (안전한 방식으로 변경)
        try:
            # PyQt6에서 setBackgroundColor 호출 시 크래시 방지
            from PyQt6.QtGui import QColor
            from ui.styles.theme_manager import theme_manager
            
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                bg_color = QColor(colors.get('background', '#121212'))
            else:
                bg_color = QColor('#1a1a1a')
            
            # setBackgroundColor 대신 CSS로 배경색 설정
            # self.web_view.page().setBackgroundColor(bg_color)  # 크래시 원인
            
        except Exception as e:
            logger.debug(f"웹뷰 배경 설정 오류 (무시됨): {e}")
        
        # 성능 최적화 적용
        performance_optimizer.optimize_webview(self.web_view)
        
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
        import platform
        
        # 플랫폼별 최적화
        system = platform.system()
        
        # 캐시 설정
        self.web_view.page().profile().setHttpCacheType(
            self.web_view.page().profile().HttpCacheType.MemoryHttpCache
        )
        cache_size = 100 * 1024 * 1024 if system == "Windows" else 50 * 1024 * 1024
        self.web_view.page().profile().setHttpCacheMaximumSize(cache_size)
        
        # 하드웨어 가속 활성화
        try:
            web_settings = self.web_view.settings()
            web_settings.setAttribute(web_settings.WebAttribute.Accelerated2dCanvasEnabled, True)
            web_settings.setAttribute(web_settings.WebAttribute.WebGLEnabled, True)
        except (AttributeError, RuntimeError):
            pass
            
        # 스크롤 최적화
        try:
            web_settings = self.web_view.settings()
            web_settings.setAttribute(web_settings.WebAttribute.ScrollAnimatorEnabled, True)
        except (AttributeError, RuntimeError):
            pass

        # 콘솔 메시지 캡처
        self.web_view.page().javaScriptConsoleMessage = self.handle_console_message

        # HTML 템플릿 로드
        self._load_html_template()

    def handle_console_message(self, level, message, line_number, source_id):
        """자바스크립트 콘솔 메시지 처리 - Mermaid 오류 완전 차단"""
        # Mermaid 관련 모든 오류 메시지 완전 차단
        message_lower = message.lower()
        blocked_keywords = [
            'mermaid', 'syntax error', 'parse error', 'diagram error',
            'version 11.12.0', 'rendering error', 'invalid syntax',
            'diagram syntax', 'mermaid.min.js'
        ]
        
        for keyword in blocked_keywords:
            if keyword in message_lower:
                return  # 완전히 무시
        
        # 일반 메시지만 출력
        logger.debug(f"JS Console] {message} (line: {line_number})")

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
            <script src="https://unpkg.com/mermaid@11.12.0/dist/mermaid.min.js" onerror="console.log('Mermaid 로드 실패 - 무시됨')"></script>
            <script>
                // Mermaid 초기화 - 오류 완전 차단
                function initMermaid() {{
                    try {{
                        if (typeof mermaid !== 'undefined') {{
                            // 오류 로깅 비활성화
                            mermaid.initialize({{
                                startOnLoad: false,
                                theme: '{mermaid_theme}',
                                securityLevel: 'loose',
                                logLevel: 'fatal',  // 오류 로깅 비활성화
                                suppressErrorRendering: true  // 오류 렌더링 비활성화
                            }});
                            renderMermaidDiagrams();
                        }} else {{
                            setTimeout(initMermaid, 100);
                        }}
                    }} catch (error) {{
                        // 초기화 오류 완전 무시
                    }}
                }}
                
                // Mermaid 다이어그램 렌더링 - 오류 완전 차단
                function renderMermaidDiagrams() {{
                    try {{
                        var elements = document.querySelectorAll('.mermaid:not([data-processed])');
                        elements.forEach(function(element, index) {{
                            var code = element.textContent.trim();
                            // 빈 코드나 잘못된 구문 필터링
                            if (code && code.length > 10 && (code.includes('graph') || code.includes('sequenceDiagram') || code.includes('flowchart') || code.includes('classDiagram') || code.includes('erDiagram') || code.includes('gitgraph') || code.includes('gitGraph') || code.includes('pie') || code.includes('journey') || code.includes('gantt') || code.includes('mindmap') || code.includes('timeline') || code.includes('sankey') || code.includes('xychart'))) {{
                                var id = 'mermaid-' + Date.now() + '-' + index;
                                // 처리 중 표시로 즉시 마킹하여 중복 처리 방지
                                element.setAttribute('data-processed', 'true');
                                
                                // 오류 메시지 완전 차단을 위한 래퍼
                                try {{
                                    mermaid.render(id, code).then(function(result) {{
                                        element.innerHTML = result.svg;
                                        element.setAttribute('data-processed', 'success');
                                    }}).catch(function(error) {{
                                        // 오류 시 완전히 제거하고 오류 메시지도 차단
                                        element.style.display = 'none';
                                        element.remove();
                                        // 오류 메시지 DOM에서 제거
                                        setTimeout(function() {{
                                            var errorElements = document.querySelectorAll('[class*="error"], [id*="error"], .mermaid-error');
                                            errorElements.forEach(function(el) {{ el.remove(); }});
                                        }}, 10);
                                    }});
                                }} catch (renderError) {{
                                    // 렌더링 오류 시 완전 제거
                                    element.style.display = 'none';
                                    element.remove();
                                }}
                            }} else {{
                                // 빈 요소나 잘못된 구문은 완전히 제거
                                element.style.display = 'none';
                                element.remove();
                            }}
                        }});
                    }} catch (error) {{
                        // Mermaid 오류 조용히 처리
                    }}
                }}
                
                // 초기화 - 중복 실행 방지
                var mermaidInitialized = false;
                function safeMermaidInit() {{
                    if (!mermaidInitialized) {{
                        mermaidInitialized = true;
                        initMermaid();
                    }}
                }}
                
                // DOM 로드 이벤트 - 오류 처리 포함
                document.addEventListener('DOMContentLoaded', function() {{
                    try {{
                        safeMermaidInit();
                    }} catch (e) {{
                        // 무시
                    }}
                }});
                window.addEventListener('load', function() {{ 
                    setTimeout(function() {{
                        try {{
                            safeMermaidInit();
                        }} catch (e) {{
                            // 무시
                        }}
                    }}, 200); 
                }});
            </script>
            <style id="theme-style">
                {theme_css}
                
                /* 성능 최적화 CSS */
                {performance_optimizer.get_optimized_css()}
                
                html, body {{
                    background: {body_bg_color} !important;
                    color: {colors.get('text_primary', '#ffffff')} !important;
                    margin: 0;
                    padding: 0;
                    font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
                    font-size: 15px !important;
                    line-height: 1.6 !important;
                    /* 스크롤 성능 최적화 */
                    scroll-behavior: smooth;
                    -webkit-overflow-scrolling: touch;
                    transform: translateZ(0);
                    will-change: scroll-position;
                }}
                
                #messages {{
                    min-height: calc(100vh - 120px);
                    height: auto;
                    overflow-y: visible;
                    padding-bottom: 120px;
                    /* 스크롤 성능 최적화 */
                    contain: layout style paint;
                    transform: translateZ(0);
                    backface-visibility: hidden;
                    perspective: 1000px;
                }}
                
                .message {{
                    margin: 16px 0;
                    padding: 24px;
                    background: {colors.get('surface', 'rgba(255, 255, 255, 0.05)')};
                    border: 1px solid {colors.get('divider', 'rgba(255, 255, 255, 0.1)')};
                    border-radius: 16px;
                    position: relative;
                    color: {colors.get('text_primary', '#ffffff')} !important;
                    min-height: auto;
                    height: auto;
                    overflow: visible;
                    /* 렌더링 성능 최적화 */
                    contain: layout style;
                    transform: translateZ(0);
                    will-change: transform;
                    transition: transform 0.2s ease;
                }}
                
                .message:hover {{
                    transform: translateZ(0) translateY(-1px);
                }}
                
                .message * {{
                    color: {colors.get('text_primary', '#ffffff')} !important;
                }}
            </style>
        </head>
        <body>
            <div id="messages"></div>
            <script>
                // 전역 Mermaid 오류 차단
                window.addEventListener('error', function(e) {{
                    if (e.message && (e.message.includes('mermaid') || e.message.includes('Syntax error'))) {{
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }}
                }});
                
                // 콘솔 오류 차단
                var originalConsoleError = console.error;
                console.error = function() {{
                    var message = Array.prototype.slice.call(arguments).join(' ');
                    if (message.includes('mermaid') || message.includes('Syntax error') || message.includes('version 11.12.0')) {{
                        return; // Mermaid 오류 무시
                    }}
                    originalConsoleError.apply(console, arguments);
                }};
                
                console.log('HTML 로드 완료');
                
                // 외부 링크 클릭 시 기본 브라우저로 열기
                document.addEventListener('click', function(event) {{
                    var target = event.target;
                    // 클릭된 요소가 <a> 태그이거나 <a> 태그의 자식인 경우
                    while (target && target.tagName !== 'A') {{
                        target = target.parentNode;
                    }}
                    if (target && target.tagName === 'A' && target.href) {{
                        // 기본 동작 방지 (QWebEngineView 내에서 이동 방지)
                        event.preventDefault();
                        // PyQt 브릿지의 openUrl 함수 호출
                        if (pyqt_bridge && pyqt_bridge.openUrl) {{
                            pyqt_bridge.openUrl(target.href);
                        }} else {{
                            // pyqt_bridge가 없으면 기본 브라우저로 직접 열기 (fallback)
                            window.open(target.href, '_blank');
                        }}
                    }}
                }});
                
                // Mermaid 초기화 (HTML 로드 후) - 중복 실행 방지
                setTimeout(function() {{
                    if (typeof safeMermaidInit === 'function') {{
                        safeMermaidInit();
                    }}
                }}, 300);
                
                var pyqt_bridge = null;
                
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    pyqt_bridge = channel.objects.pyqt_bridge;
                }});
                
                var currentSelectedMessage = null;
                
                // 메시지 클릭 시 선택 상태 변경
                document.addEventListener('click', function(event) {{
                    var messageElement = event.target.closest('.message');
                    if (messageElement) {{
                        // 이전 선택 해제
                        var prevSelected = document.querySelector('.message.selected');
                        if (prevSelected) {{
                            prevSelected.classList.remove('selected');
                            prevSelected.style.border = '';
                        }}
                        
                        // 새로운 메시지 선택
                        messageElement.classList.add('selected');
                        messageElement.style.border = '2px solid #bb86fc';
                        currentSelectedMessage = messageElement.id;
                        
                        // 버튼 표시
                        var buttonContainer = document.getElementById('global-button-container');
                        if (buttonContainer) {{
                            buttonContainer.style.display = 'flex';
                        }}
                    }}
                }});
                
                function copyMessage(messageId) {{
                    try {{
                        var targetId = messageId || currentSelectedMessage;
                        if (!targetId) {{
                            showToast('메시지를 먼저 선택해주세요.');
                            return;
                        }}
                        
                        var contentDiv = document.getElementById(targetId + '_content');
                        if (!contentDiv) {{
                            return;
                        }}
                        
                        var textContent = contentDiv.innerText || contentDiv.textContent;
                        
                        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {{
                            pyqt_bridge.copyToClipboard(textContent);
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
                        var targetId = messageId || currentSelectedMessage;
                        if (!targetId) {{
                            showToast('메시지를 먼저 선택해주세요.');
                            return;
                        }}
                        
                        var contentDiv = document.getElementById(targetId + '_content');
                        if (!contentDiv) {{
                            return;
                        }}
                        
                        var htmlContent = contentDiv.innerHTML;
                        
                        if (pyqt_bridge && pyqt_bridge.copyHtmlToClipboard) {{
                            pyqt_bridge.copyHtmlToClipboard(htmlContent);
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
                    toast.style.cssText = 'position: fixed !important; top: 20px !important; right: 20px !important; background: #4CAF50 !important; color: white !important; padding: 16px 24px !important; border-radius: 8px !important; z-index: 999999 !important; font-size: 16px !important; font-weight: 600 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important; border: 2px solid white !important;';
                    console.log('토스트 생성됨:', message);
                    if (!document.body) {{
                        console.error('document.body is null');
                        return;
                    }}
                    document.body.appendChild(toast);
                    
                    setTimeout(function() {{
                        if (toast.parentNode) {{
                            toast.parentNode.removeChild(toast);
                        }}
                    }}, 2000);
                }}
                
                function searchInDictionary(word) {{
                    try {{
                        if (pyqt_bridge && pyqt_bridge.searchDictionary) {{
                            pyqt_bridge.searchDictionary(word);
                        }}
                    }} catch (error) {{
                        console.error('Dictionary search failed:', error);
                    }}
                }}
                
                function getSelectedText() {{
                    var selection = window.getSelection();
                    return selection.toString().trim();
                }}
                
                // 텍스트 선택 및 더블클릭 이벤트 처리
                document.addEventListener('dblclick', function(event) {{
                    var selectedText = getSelectedText();
                    if (selectedText && selectedText.length > 0 && selectedText.length < 50) {{
                        // 단어만 추출 (공백, 숫자, 특수문자 제거)
                        var cleanWord = selectedText.replace(/[^a-zA-Z가-힣]/g, '');
                        if (cleanWord.length >= 2) {{
                            searchInDictionary(cleanWord);
                            showToast('찾는 단어: ' + cleanWord);
                        }}
                    }}
                }});
                
                // 우클릭 컨텍스트 메뉴 처리
                document.addEventListener('contextmenu', function(event) {{
                    event.preventDefault();
                    
                    var selectedText = getSelectedText();
                    if (selectedText && selectedText.length > 0) {{
                        showContextMenu(event.pageX, event.pageY, selectedText);
                    }}
                }});
                
                function showContextMenu(x, y, selectedText) {{
                    // 기존 컨텍스트 메뉴 제거
                    var existingMenu = document.getElementById('context-menu');
                    if (existingMenu) {{
                        existingMenu.remove();
                    }}
                    
                    var menu = document.createElement('div');
                    menu.id = 'context-menu';
                    menu.style.cssText = 'position: absolute; background: rgba(45, 45, 45, 0.95); border: 1px solid #444444; border-radius: 8px; padding: 8px 0; z-index: 10000; box-shadow: 0 4px 12px rgba(0,0,0,0.3); min-width: 120px; backdrop-filter: blur(10px);';
                    menu.style.left = x + 'px';
                    menu.style.top = y + 'px';
                    
                    // 복사 메뉴 항목
                    var copyItem = document.createElement('div');
                    copyItem.textContent = '📋 복사';
                    copyItem.style.cssText = 'padding: 8px 16px; cursor: pointer; color: #ffffff; font-size: 14px; transition: background 0.2s;';
                    copyItem.onmouseover = function() {{ this.style.background = 'rgba(187, 134, 252, 0.3)'; }};
                    copyItem.onmouseout = function() {{ this.style.background = 'transparent'; }};
                    copyItem.onclick = function() {{
                        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {{
                            pyqt_bridge.copyToClipboard(selectedText);
                            showToast('텍스트가 복사되었습니다!');
                        }}
                        menu.remove();
                    }};
                    
                    // 찾기 메뉴 항목
                    var searchItem = document.createElement('div');
                    searchItem.textContent = '🔍 찾기';
                    searchItem.style.cssText = 'padding: 8px 16px; cursor: pointer; color: #ffffff; font-size: 14px; transition: background 0.2s;';
                    searchItem.onmouseover = function() {{ this.style.background = 'rgba(187, 134, 252, 0.3)'; }};
                    searchItem.onmouseout = function() {{ this.style.background = 'transparent'; }};
                    searchItem.onclick = function() {{
                        var cleanWord = selectedText.replace(/[^a-zA-Z가-힣]/g, '');
                        if (cleanWord.length >= 2) {{
                            searchInDictionary(cleanWord);
                            showToast('찾는 단어: ' + cleanWord);
                        }} else {{
                            searchInDictionary(selectedText);
                            showToast('찾는 단어: ' + selectedText);
                        }}
                        menu.remove();
                    }};
                    
                    menu.appendChild(copyItem);
                    menu.appendChild(searchItem);
                    document.body.appendChild(menu);
                    
                    // 메뉴 외부 클릭 시 닫기
                    setTimeout(function() {{
                        document.addEventListener('click', function closeMenu(e) {{
                            if (!menu.contains(e.target)) {{
                                menu.remove();
                                document.removeEventListener('click', closeMenu);
                            }}
                        }});
                    }}, 10);
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
                
                function copyCodeBlock(codeId) {{
                    try {{
                        var codeElement = document.getElementById(codeId);
                        if (!codeElement) {{
                            showToast('코드 요소를 찾을 수 없습니다.');
                            return;
                        }}
                        
                        var codeText = codeElement.textContent || codeElement.innerText;
                        
                        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {{
                            pyqt_bridge.copyToClipboard(codeText);
                            showToast('✅ 코드가 복사되었습니다!');
                        }} else if (navigator.clipboard && navigator.clipboard.writeText) {{
                            navigator.clipboard.writeText(codeText).then(function() {{
                                showToast('✅ 코드가 복사되었습니다!');
                            }}).catch(function(err) {{
                                console.error('Clipboard write failed:', err);
                            }});
                        }}
                    }} catch (error) {{
                        console.error('Code copy failed:', error);
                        showToast('❌ 코드 복사에 실패했습니다.');
                    }}
                }}
                
                function executeCode(codeId, language) {{
                    try {{
                        var codeElement = document.getElementById(codeId);
                        if (!codeElement) {{
                            showToast('코드 요소를 찾을 수 없습니다.');
                            return;
                        }}
                        
                        var codeText = codeElement.textContent || codeElement.innerText;
                        
                        if (pyqt_bridge && pyqt_bridge.executeCode) {{
                            showToast('⏳ 코드 실행 중...');
                            pyqt_bridge.executeCode(codeText, language);
                        }} else {{
                            showToast('❌ 코드 실행 기능을 사용할 수 없습니다.');
                        }}
                    }} catch (error) {{
                        console.error('Code execution failed:', error);
                        showToast('❌ 코드 실행에 실패했습니다.');
                    }}
                }}
                
                function deleteMessage(messageId) {{
                    try {{
                        var targetId = messageId || currentSelectedMessage;
                        if (!targetId) {{
                            showToast('메시지를 먼저 선택해주세요.');
                            return;
                        }}
                        
                        if (pyqt_bridge && pyqt_bridge.deleteMessage) {{
                            pyqt_bridge.deleteMessage(targetId);
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
            colors = theme_manager.material_manager.get_theme_colors()
            link_color = colors.get('secondary', '#03dac6') # 기본 링크 색상
            hover_color = colors.get('primary', '#bb86fc') # 호버 시 색상
            css += f"""
            a {{
                color: {link_color} !important;
                text-decoration: underline;
                font-weight: bold;
                transition: color 0.2s ease-in-out;
            }}
            a:hover {{
                color: {hover_color} !important;
                text-decoration: none;
            }}
            .message {{
                background-color: {colors.get('surface', '#1e1e1e')} !important;
            }}
            """
            return css
        else:
            from ui.styles.flat_theme import FlatTheme
            css = FlatTheme.get_chat_display_css()
            colors = FlatTheme.get_theme_colors() # Flat 테마 색상 가져오기
            
            link_color = colors.get('primary', '#64c8ff') # Flat 테마의 primary 색상 사용
            hover_color = "#42A5F5" # 호버 시 약간 더 어두운 파란색
            
            css += f"""
            a {{
                color: {link_color} !important;
                text-decoration: underline;
                font-weight: bold;
                transition: color 0.2s ease-in-out;
            }}
            a:hover {{
                color: {hover_color} !important;
                text-decoration: none;
            }}
            .message {{
                background-color: {colors.get('surface', '#4a4a4f')} !important;
            }}
            """
            return css

    def is_dark_theme(self) -> bool:
        """현재 테마가 다크 테마인지 확인"""
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            return theme_manager.material_manager.is_dark_theme()
        else:
            return True  # 기본 테마는 다크 테마로 간주

    def update_theme(self):
        """테마 업데이트 - 화면 깜빡임 없이 CSS만 동적으로 변경"""
        try:
            from ui.styles.theme_manager import theme_manager
            logger.debug(f"테마 업데이트 시작 (깜빡임 없음): {theme_manager.material_manager.current_theme_key}")

            new_theme_css = self._get_current_theme_css()
            
            # 현재 테마의 배경색 가져오기
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                body_bg_color = colors.get("background", "#121212")
            else:
                from ui.styles.flat_theme import FlatTheme
                colors = FlatTheme.get_theme_colors()
                body_bg_color = colors.get("background", "#1a1a1a")

            # JavaScript를 사용하여 <style> 태그와 body 배경색 업데이트
            update_js = f"""
            try {{
                var styleTag = document.getElementById('theme-style');
                if (styleTag) {{
                    styleTag.innerHTML = `{new_theme_css}`;
                }}
                document.body.style.backgroundColor = '{body_bg_color}';
                document.documentElement.style.backgroundColor = '{body_bg_color}';
                console.log('테마 CSS 및 배경색 업데이트 완료');
            }} catch(e) {{
                console.error('테마 CSS 업데이트 오류:', e);
            }}
            """
            self.web_view.page().runJavaScript(update_js)
            
            logger.debug("채팅 디스플레이 테마 업데이트 완료 (깜빡임 없음)")

        except Exception as e:
            logger.debug(f"채팅 디스플레이 테마 업데이트 오류: {e}")
    
    def _reload_with_backup(self):
        """백업된 메시지와 함께 HTML 재로드"""
        try:
            # HTML 템플릿 재로드
            self._load_html_template()
            
            # 200ms 후 메시지 복원
            QTimer.singleShot(200, self._restore_messages)
            
        except Exception as e:
            logger.debug(f"HTML 재로드 오류: {e}")
    
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
        logger.debug("채팅 디스플레이 테마 업데이트 완료")

    def _setup_link_handler(self):
        """링크 클릭 핸들러 안전 설정"""
        try:
            from PyQt6.QtWebChannel import QWebChannel

            # 웹 채널 안전 설정
            self.channel = QWebChannel()
            self.link_handler = LinkHandler()
            self.channel.registerObject("pyqt_bridge", self.link_handler)
            self.web_view.page().setWebChannel(self.channel)
            logger.debug("웹 채널 설정 완료")
            
        except Exception as e:
            logger.debug(f"웹 채널 설정 오류: {e}")
            # 채널 설정 실패 시 기본 핸들러만 생성
            self.link_handler = LinkHandler()

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
        # 타임스탬프 생성
        from datetime import datetime
        now = datetime.now()
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        timestamp = now.strftime(f"%Y-%m-%d %H:%M:%S ({weekdays[now.weekday()]}요일)")
        
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
            messageDiv.style.cssText = 'position: relative; margin: 16px 0; padding: 24px; background: {colors.get("surface", "rgba(255, 255, 255, 0.05)")}; border: 1px solid {colors.get("divider", "rgba(255, 255, 255, 0.1)")}; border-radius: 16px; color: {default_text_color} !important;';
            
            var headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'margin: 0 0 12px 0; font-weight: 600; color: {default_text_color} !important; font-size: 13px; display: flex; align-items: center; justify-content: space-between;';
            
            var senderInfo = document.createElement('div');
            senderInfo.style.cssText = 'display: flex; align-items: center; gap: 8px;';
            senderInfo.innerHTML = '<span style="font-size:16px;">{icon}</span><span>{sender}</span>';
            
            // 개별 메시지 버튼 컨테이너
            var buttonContainer = document.createElement('div');
            buttonContainer.style.cssText = 'display: flex; gap: 4px; opacity: 0.7; transition: opacity 0.2s ease;';
            
            // 복사 버튼
            var copyBtn = document.createElement('button');
            copyBtn.innerHTML = '📋';
            copyBtn.title = '텍스트 복사';
            copyBtn.style.cssText = 'background: {colors.get("primary", "#bb86fc")}; color: {colors.get("on_primary", "#000000")}; border: none; padding: 4px 6px; border-radius: 4px; cursor: pointer; font-size: 10px; transition: all 0.2s ease;';
            copyBtn.onclick = function() {{ copyMessage('{display_message_id}'); }};
            
            // HTML 복사 버튼
            var htmlCopyBtn = document.createElement('button');
            htmlCopyBtn.innerHTML = '🏷️';
            htmlCopyBtn.title = 'HTML 복사';
            htmlCopyBtn.style.cssText = 'background: {colors.get("secondary", "#03dac6")}; color: {colors.get("on_secondary", "#000000")}; border: none; padding: 4px 6px; border-radius: 4px; cursor: pointer; font-size: 10px; transition: all 0.2s ease;';
            htmlCopyBtn.onclick = function() {{ copyHtmlMessage('{display_message_id}'); }};
            
            // 삭제 버튼
            var deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = '메시지 삭제';
            deleteBtn.style.cssText = 'background: {colors.get("error", "#cf6679")}; color: {colors.get("on_error", "#000000")}; border: none; padding: 4px 6px; border-radius: 4px; cursor: pointer; font-size: 10px; transition: all 0.2s ease;';
            deleteBtn.onclick = function() {{ 
                if (confirm('이 메시지를 삭제하시겠습니까?')) {{
                    deleteMessage('{message_id or display_message_id}'); 
                }}
            }};
            
            // 버튼들을 컨테이너에 추가
            buttonContainer.appendChild(copyBtn);
            buttonContainer.appendChild(htmlCopyBtn);
            buttonContainer.appendChild(deleteBtn);
            
            // 호버 효과
            messageDiv.onmouseenter = function() {{ buttonContainer.style.opacity = '1'; }};
            messageDiv.onmouseleave = function() {{ buttonContainer.style.opacity = '0.7'; }};
            
            headerDiv.appendChild(senderInfo);
            headerDiv.appendChild(buttonContainer);
            
            var contentDiv = document.createElement('div');
            contentDiv.id = '{display_message_id}_content';
            contentDiv.style.cssText = 'margin: 0; padding: 0; line-height: 1.6; color: {default_text_color} !important; font-size: 15px; word-wrap: break-word; width: 100%;';
            
            // 타임스탬프 추가
            var timestampDiv = document.createElement('div');
            timestampDiv.style.cssText = 'margin-top: 12px; padding-top: 8px; border-top: 1px solid {colors.get("divider", "rgba(255, 255, 255, 0.1)")}; font-size: 11px; color: {colors.get("text_secondary", "rgba(255, 255, 255, 0.6)")} !important; text-align: right; opacity: 0.7;';
            timestampDiv.textContent = '{timestamp}';
            
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
            
            // Mermaid 다이어그램 렌더링
            setTimeout(function() {{
                if (typeof renderMermaidDiagrams === 'function') {{
                    renderMermaidDiagrams();
                }}
            }}, 50);
            
            // 스크롤 조정 - 강화된 하단 스크롤
            setTimeout(function() {{
                if (!{str(prepend).lower()}) {{
                    // 여러 방법으로 하단 스크롤 시도
                    const scrollToBottom = () => {{
                        const maxScroll = Math.max(
                            document.body.scrollHeight,
                            document.documentElement.scrollHeight,
                            document.body.offsetHeight,
                            document.documentElement.offsetHeight
                        );
                        
                        // 즉시 스크롤
                        window.scrollTo(0, maxScroll);
                        document.documentElement.scrollTop = maxScroll;
                        document.body.scrollTop = maxScroll;
                        
                        // 부드러운 스크롤도 시도
                        window.scrollTo({{
                            top: maxScroll,
                            behavior: 'smooth'
                        }});
                    }};
                    
                    // 즉시 실행
                    scrollToBottom();
                    
                    // 100ms 후 다시 시도
                    setTimeout(scrollToBottom, 100);
                    
                    // 300ms 후 마지막 시도
                    setTimeout(scrollToBottom, 300);
                }}
            }}, 50);
            
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
            logger.debug(f"URL 열기 오류: {e}")

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
                
                # 즉시 토스트 메시지 표시
                logger.debug(f" chat_widget 존재: {hasattr(self, 'chat_widget')}")
                logger.debug(f" chat_widget 값: {self.chat_widget}")
                if hasattr(self, 'chat_widget') and self.chat_widget:
                    logger.debug(f" chat_display 존재: {hasattr(self.chat_widget, 'chat_display')}")
                    if hasattr(self.chat_widget, 'chat_display'):
                        logger.debug(f" JavaScript 실행 시도")
                        # 직접 토스트 생성 (showToast 함수 의존성 제거)
                        toast_js = """
                        try {
                            var toast = document.createElement('div');
                            toast.textContent = '텍스트가 복사되었습니다!';
                            toast.style.cssText = 'position: fixed !important; top: 20px !important; right: 20px !important; background: #4CAF50 !important; color: white !important; padding: 16px 24px !important; border-radius: 8px !important; z-index: 999999 !important; font-size: 16px !important; font-weight: 600 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;';
                            document.body.appendChild(toast);
                            setTimeout(function() { if(toast.parentNode) toast.parentNode.removeChild(toast); }, 2000);
                        } catch(e) { console.error('Toast error:', e); }
                        """
                        self.chat_widget.chat_display.web_view.page().runJavaScript(toast_js)
                    else:
                        logger.debug(f" chat_display 없음")
                else:
                    logger.debug(f" chat_widget 없음 또는 None")
                logger.debug(f"COPY] 클립보드 복사 시도: {len(text)}자")
            else:
                logger.debug(f"COPY] QApplication 인스턴스 없음")
                if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                    self.chat_widget.chat_display.web_view.page().runJavaScript(
                        "showToast('복사에 실패했습니다.');"
                    )
        except Exception as e:
            logger.debug(f"COPY] 클립보드 복사 오류: {e}")
            if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                self.chat_widget.chat_display.web_view.page().runJavaScript(
                    "showToast('복사에 실패했습니다.');"
                )
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
                
                # 즉시 토스트 메시지 표시
                logger.debug(f"DEBUG HTML] chat_widget 존재: {hasattr(self, 'chat_widget')}")
                if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                    logger.debug(f"DEBUG HTML] JavaScript 실행 시도")
                    # 직접 토스트 생성 (showToast 함수 의존성 제거)
                    toast_js = """
                    try {
                        var toast = document.createElement('div');
                        toast.textContent = 'HTML이 복사되었습니다!';
                        toast.style.cssText = 'position: fixed !important; top: 20px !important; right: 20px !important; background: #03DAC6 !important; color: white !important; padding: 16px 24px !important; border-radius: 8px !important; z-index: 999999 !important; font-size: 16px !important; font-weight: 600 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;';
                        document.body.appendChild(toast);
                        setTimeout(function() { if(toast.parentNode) toast.parentNode.removeChild(toast); }, 2000);
                    } catch(e) { console.error('Toast error:', e); }
                    """
                    self.chat_widget.chat_display.web_view.page().runJavaScript(toast_js)
                else:
                    logger.debug(f"DEBUG HTML] chat_widget 또는 chat_display 없음")
                logger.debug(f"COPY_HTML] HTML 클립보드 복사 시도: {len(html)}자")
            else:
                logger.debug(f"COPY_HTML] QApplication 인스턴스 없음")
                if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                    self.chat_widget.chat_display.web_view.page().runJavaScript(
                        "showToast('HTML 복사에 실패했습니다.');"
                    )
        except Exception as e:
            logger.debug(f"COPY_HTML] HTML 클립보드 복사 오류: {e}")
            if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                self.chat_widget.chat_display.web_view.page().runJavaScript(
                    "showToast('HTML 복사에 실패했습니다.');"
                )
            import traceback
            traceback.print_exc()

    @pyqtSlot(str)
    def searchDictionary(self, word):
        """구글에서 단어 검색"""
        try:
            import urllib.parse
            
            encoded_word = urllib.parse.quote(word)
            url = f"https://www.google.com/search?q={encoded_word}+meaning"
            
            logger.debug(f"사전검색] 단어: {word}, URL: {url}")
            QDesktopServices.openUrl(QUrl(url))
            
        except Exception as e:
            logger.debug(f"사전검색] 오류: {e}")
    
    @pyqtSlot(str)
    def deleteMessage(self, message_id):
        """메시지 삭제"""
        try:
            logger.debug(f"DELETE] 삭제 요청: {message_id}")

            # 먼저 DOM에서 제거 (즉시 시각적 피드백)
            if (
                hasattr(self, "chat_widget")
                and self.chat_widget
                and hasattr(self.chat_widget, "chat_display")
            ):
                self.chat_widget.chat_display.web_view.page().runJavaScript(
                    f"removeMessageFromDOM('{message_id}')"
                )
                logger.debug(f"DELETE] DOM에서 제거 완료: {message_id}")

            # 데이터에서 삭제
            if self.chat_widget and hasattr(self.chat_widget, "delete_message"):
                success = self.chat_widget.delete_message(message_id)
                logger.debug(f"DELETE] 데이터 삭제 결과: {success}")
            else:
                logger.debug(f"DELETE] delete_message 메소드 없음")

        except Exception as e:
            logger.debug(f"DELETE] 오류: {e}")
            import traceback

            traceback.print_exc()
    
    @pyqtSlot(str, str)
    def executeCode(self, code, language):
        """코드 실행"""
        try:
            from ui.components.code_executor import CodeExecutor
            
            executor = CodeExecutor()
            executor.execution_finished.connect(self._on_execution_finished)
            executor.executeCode(code, language)
            
        except Exception as e:
            logger.debug(f"EXECUTE] 코드 실행 오류: {e}")
            self._show_execution_result("", f"실행 오류: {str(e)}")
    
    def _on_execution_finished(self, output, error):
        """코드 실행 완료 처리"""
        self._show_execution_result(output, error)
    
    def _show_execution_result(self, output, error):
        """실행 결과 표시"""
        try:
            if hasattr(self, 'chat_widget') and self.chat_widget:
                result_text = ""
                if output:
                    result_text += f"**출력:**\n```\n{output}\n```\n"
                if error:
                    result_text += f"**오류:**\n```\n{error}\n```"
                
                if not result_text:
                    result_text = "실행 완료 (출력 없음)"
                
                # 채팅 위젯에 결과 메시지 추가
                if hasattr(self.chat_widget, 'chat_display'):
                    self.chat_widget.chat_display.append_message(
                        "시스템",
                        result_text,
                        progressive=False
                    )
        except Exception as e:
            logger.debug(f"EXECUTE] 결과 표시 오류: {e}")