"""
HTML Template Builder
HTML 템플릿 생성 전담
"""

from core.logging import get_logger

logger = get_logger("html_template_builder")


class HtmlTemplateBuilder:
    """HTML 템플릿 빌더"""
    
    def __init__(self, web_view):
        self.web_view = web_view
    
    def load_html_template(self):
        """HTML 템플릿 로드 - CSS 변수 기반"""
        from ui.components.chat_theme_vars import generate_css_variables, generate_base_css
        from ui.styles.theme_manager import theme_manager
        
        # 테마 색상 가져오기
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
        else:
            from ui.styles.flat_theme import FlatTheme
            colors = FlatTheme.get_theme_colors()
        
        # CSS 변수 생성
        is_dark = self.is_dark_theme()
        css_variables = generate_css_variables(colors, is_dark)
        base_css = generate_base_css()
        
        # Mermaid 테마 결정
        
        # Performance optimizer
        from ui.performance_optimizer import performance_optimizer
        perf_css = performance_optimizer.get_optimized_css()
        mermaid_theme = "dark" if is_dark else "default"

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
                                logLevel: 'fatal',
                                suppressErrorRendering: true,
                                themeVariables: {{
                                    darkMode: {str(is_dark).lower()},
                                    background: '{colors.get("surface", "#1e1e1e" if is_dark else "#ffffff")}',
                                    primaryColor: '{colors.get("primary", "#bb86fc" if is_dark else "#5b21b6")}',
                                    primaryTextColor: '{colors.get("text_primary", "#ffffff" if is_dark else "#1a1a1a")}',
                                    primaryBorderColor: '{colors.get("primary", "#bb86fc" if is_dark else "#5b21b6")}',
                                    lineColor: '{colors.get("text_secondary", "#a0a0a0" if is_dark else "#666666")}',
                                    secondaryColor: '{colors.get("surface", "#1e1e1e" if is_dark else "#f8fafc")}',
                                    tertiaryColor: '{colors.get("background", "#121212" if is_dark else "#ffffff")}',
                                    mainBkg: '{colors.get("surface", "#1e1e1e" if is_dark else "#ffffff")}',
                                    textColor: '{colors.get("text_primary", "#ffffff" if is_dark else "#1a1a1a")}',
                                    nodeBorder: '{colors.get("primary", "#bb86fc" if is_dark else "#5b21b6")}',
                                    clusterBkg: '{colors.get("surface", "#1e1e1e" if is_dark else "#f8fafc")}',
                                    clusterBorder: '{colors.get("divider", "rgba(255,255,255,0.12)" if is_dark else "rgba(0,0,0,0.12)")}',
                                    edgeLabelBackground: '{colors.get("surface", "#1e1e1e" if is_dark else "#ffffff")}'
                                }}
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
                /* CSS 변수 정의 */
                {css_variables}
                
                /* 기본 스타일 */
                {base_css}
                
                /* 성능 최적화 CSS */
                {perf_css}
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
                
                // 코드 블록 관련 함수 정의 (CRITICAL: 패키징 환경 호환성 - 즉시 실행)
                (function() {{
                    window.copyCodeBlock = function(codeId) {{
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
                }};
                
                window.executeCode = function(codeId, language) {{
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
                    }};
                    
                    console.log('[INIT] 코드 블록 함수 등록 완료');
                }})();
                
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
                
                function showToast(message, type) {{
                    var toast = document.createElement('div');
                    toast.textContent = message;
                    toast.className = 'toast' + (type ? ' ' + type : '');
                    
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
                    var existingMenu = document.getElementById('context-menu');
                    if (existingMenu) {{
                        existingMenu.remove();
                    }}
                    
                    var menu = document.createElement('div');
                    menu.id = 'context-menu';
                    menu.className = 'context-menu';
                    menu.style.left = x + 'px';
                    menu.style.top = y + 'px';
                    
                    var copyItem = document.createElement('div');
                    copyItem.textContent = '📋 복사';
                    copyItem.className = 'context-menu-item';
                    copyItem.onclick = function() {{
                        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {{
                            pyqt_bridge.copyToClipboard(selectedText);
                            showToast('텍스트가 복사되었습니다!', 'success');
                        }}
                        menu.remove();
                    }};
                    
                    var searchItem = document.createElement('div');
                    searchItem.textContent = '🔍 찾기';
                    searchItem.className = 'context-menu-item';
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
                    
                    setTimeout(function() {{
                        document.addEventListener('click', function closeMenu(e) {{
                            if (!menu.contains(e.target)) {{
                                menu.remove();
                                document.removeEventListener('click', closeMenu);
                            }}
                        }});
                    }}, 10);
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




    def is_dark_theme(self) -> bool:
        """현재 테마가 다크 테마인지 확인"""
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            return theme_manager.material_manager.is_dark_theme()
        else:
            return True
