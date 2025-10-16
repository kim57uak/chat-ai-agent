// Chat Display JavaScript
// 채팅 화면 JavaScript 로직

// Mermaid 초기화 - 오류 완전 차단
function initMermaid(theme) {
    try {
        if (typeof mermaid !== 'undefined') {
            mermaid.initialize({
                startOnLoad: false,
                theme: theme || 'dark',
                securityLevel: 'loose',
                logLevel: 'fatal',
                suppressErrorRendering: true
            });
            renderMermaidDiagrams();
        } else {
            setTimeout(() => initMermaid(theme), 100);
        }
    } catch (error) {
        // 초기화 오류 완전 무시
    }
}

// Mermaid 다이어그램 렌더링
function renderMermaidDiagrams() {
    try {
        var elements = document.querySelectorAll('.mermaid:not([data-processed])');
        elements.forEach(function(element, index) {
            var code = element.textContent.trim();
            if (code && code.length > 10 && (code.includes('graph') || code.includes('sequenceDiagram') || code.includes('flowchart') || code.includes('classDiagram') || code.includes('erDiagram') || code.includes('gitgraph') || code.includes('gitGraph') || code.includes('pie') || code.includes('journey') || code.includes('gantt') || code.includes('mindmap') || code.includes('timeline') || code.includes('sankey') || code.includes('xychart'))) {
                var id = 'mermaid-' + Date.now() + '-' + index;
                element.setAttribute('data-processed', 'true');
                
                try {
                    mermaid.render(id, code).then(function(result) {
                        element.innerHTML = result.svg;
                        element.setAttribute('data-processed', 'success');
                    }).catch(function(error) {
                        element.style.display = 'none';
                        element.remove();
                        setTimeout(function() {
                            var errorElements = document.querySelectorAll('[class*="error"], [id*="error"], .mermaid-error');
                            errorElements.forEach(function(el) { el.remove(); });
                        }, 10);
                    });
                } catch (renderError) {
                    element.style.display = 'none';
                    element.remove();
                }
            } else {
                element.style.display = 'none';
                element.remove();
            }
        });
    } catch (error) {
        // Mermaid 오류 조용히 처리
    }
}

// 초기화 - 중복 실행 방지
var mermaidInitialized = false;
function safeMermaidInit(theme) {
    if (!mermaidInitialized) {
        mermaidInitialized = true;
        initMermaid(theme);
    }
}

// 전역 Mermaid 오류 차단
window.addEventListener('error', function(e) {
    if (e.message && (e.message.includes('mermaid') || e.message.includes('Syntax error'))) {
        e.preventDefault();
        e.stopPropagation();
        return false;
    }
});

// 콘솔 오류 차단
var originalConsoleError = console.error;
console.error = function() {
    var message = Array.prototype.slice.call(arguments).join(' ');
    if (message.includes('mermaid') || message.includes('Syntax error') || message.includes('version 11.12.0')) {
        return;
    }
    originalConsoleError.apply(console, arguments);
};

// PyQt 브릿지
var pyqt_bridge = null;
var currentSelectedMessage = null;

// QWebChannel 초기화
if (typeof qt !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, function(channel) {
        pyqt_bridge = channel.objects.pyqt_bridge;
    });
}

// 외부 링크 클릭 처리
document.addEventListener('click', function(event) {
    var target = event.target;
    while (target && target.tagName !== 'A') {
        target = target.parentNode;
    }
    if (target && target.tagName === 'A' && target.href) {
        event.preventDefault();
        if (pyqt_bridge && pyqt_bridge.openUrl) {
            pyqt_bridge.openUrl(target.href);
        } else {
            window.open(target.href, '_blank');
        }
    }
});

// 메시지 선택 처리
document.addEventListener('click', function(event) {
    var messageElement = event.target.closest('.message');
    if (messageElement) {
        var prevSelected = document.querySelector('.message.selected');
        if (prevSelected) {
            prevSelected.classList.remove('selected');
            prevSelected.style.border = '';
        }
        
        messageElement.classList.add('selected');
        messageElement.style.border = '2px solid #bb86fc';
        currentSelectedMessage = messageElement.id;
        
        var buttonContainer = document.getElementById('global-button-container');
        if (buttonContainer) {
            buttonContainer.style.display = 'flex';
        }
    }
});

// 메시지 복사
function copyMessage(messageId) {
    try {
        var targetId = messageId || currentSelectedMessage;
        if (!targetId) {
            showToast('메시지를 먼저 선택해주세요.');
            return;
        }
        
        var contentDiv = document.getElementById(targetId + '_content');
        if (!contentDiv) return;
        
        var textContent = contentDiv.innerText || contentDiv.textContent;
        
        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {
            pyqt_bridge.copyToClipboard(textContent);
        } else if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(textContent).then(function() {
                showToast('텍스트가 복사되었습니다!');
            });
        }
    } catch (error) {
        console.error('Message copy failed:', error);
        showToast('복사에 실패했습니다.');
    }
}

// HTML 복사
function copyHtmlMessage(messageId) {
    try {
        var targetId = messageId || currentSelectedMessage;
        if (!targetId) {
            showToast('메시지를 먼저 선택해주세요.');
            return;
        }
        
        var contentDiv = document.getElementById(targetId + '_content');
        if (!contentDiv) return;
        
        var htmlContent = contentDiv.innerHTML;
        
        if (pyqt_bridge && pyqt_bridge.copyHtmlToClipboard) {
            pyqt_bridge.copyHtmlToClipboard(htmlContent);
        } else {
            var textArea = document.createElement('textarea');
            textArea.value = htmlContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showToast('HTML이 복사되었습니다!');
        }
    } catch (error) {
        console.error('HTML copy failed:', error);
        showToast('HTML 복사에 실패했습니다.');
    }
}

// 토스트 메시지
function showToast(message, type) {
    var toast = document.createElement('div');
    toast.textContent = message;
    toast.className = 'toast' + (type ? ' ' + type : '');
    
    if (!document.body) {
        console.error('document.body is null');
        return;
    }
    document.body.appendChild(toast);
    
    setTimeout(function() {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 2000);
}

// 사전 검색
function searchInDictionary(word) {
    try {
        if (pyqt_bridge && pyqt_bridge.searchDictionary) {
            pyqt_bridge.searchDictionary(word);
        }
    } catch (error) {
        console.error('Dictionary search failed:', error);
    }
}

// 선택된 텍스트 가져오기
function getSelectedText() {
    var selection = window.getSelection();
    return selection.toString().trim();
}

// 더블클릭 이벤트
document.addEventListener('dblclick', function(event) {
    var selectedText = getSelectedText();
    if (selectedText && selectedText.length > 0 && selectedText.length < 50) {
        var cleanWord = selectedText.replace(/[^a-zA-Z가-힣]/g, '');
        if (cleanWord.length >= 2) {
            searchInDictionary(cleanWord);
            showToast('찾는 단어: ' + cleanWord);
        }
    }
});

// 컨텍스트 메뉴
document.addEventListener('contextmenu', function(event) {
    event.preventDefault();
    
    var selectedText = getSelectedText();
    if (selectedText && selectedText.length > 0) {
        showContextMenu(event.pageX, event.pageY, selectedText);
    }
});

function showContextMenu(x, y, selectedText) {
    var existingMenu = document.getElementById('context-menu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    var menu = document.createElement('div');
    menu.id = 'context-menu';
    menu.className = 'context-menu';
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    
    var copyItem = document.createElement('div');
    copyItem.textContent = '📋 복사';
    copyItem.className = 'context-menu-item';
    copyItem.onclick = function() {
        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {
            pyqt_bridge.copyToClipboard(selectedText);
            showToast('텍스트가 복사되었습니다!', 'success');
        }
        menu.remove();
    };
    
    var searchItem = document.createElement('div');
    searchItem.textContent = '🔍 찾기';
    searchItem.className = 'context-menu-item';
    searchItem.onclick = function() {
        var cleanWord = selectedText.replace(/[^a-zA-Z가-힣]/g, '');
        if (cleanWord.length >= 2) {
            searchInDictionary(cleanWord);
            showToast('찾는 단어: ' + cleanWord);
        } else {
            searchInDictionary(selectedText);
            showToast('찾는 단어: ' + selectedText);
        }
        menu.remove();
    };
    
    menu.appendChild(copyItem);
    menu.appendChild(searchItem);
    document.body.appendChild(menu);
    
    setTimeout(function() {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target)) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 10);
}

// 코드 복사
function copyCode(codeElement) {
    try {
        var codeText = codeElement.textContent || codeElement.innerText;
        
        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {
            pyqt_bridge.copyToClipboard(codeText);
            showToast('코드가 복사되었습니다!');
        } else if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(codeText).then(function() {
                showToast('코드가 복사되었습니다!');
            });
        }
    } catch (error) {
        console.error('Code copy failed:', error);
        showToast('코드 복사에 실패했습니다.');
    }
}

function copyCodeBlock(codeId) {
    try {
        var codeElement = document.getElementById(codeId);
        if (!codeElement) {
            showToast('코드 요소를 찾을 수 없습니다.');
            return;
        }
        
        var codeText = codeElement.textContent || codeElement.innerText;
        
        if (pyqt_bridge && pyqt_bridge.copyToClipboard) {
            pyqt_bridge.copyToClipboard(codeText);
            showToast('✅ 코드가 복사되었습니다!');
        } else if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(codeText).then(function() {
                showToast('✅ 코드가 복사되었습니다!');
            }).catch(function(err) {
                console.error('Clipboard write failed:', err);
            });
        }
    } catch (error) {
        console.error('Code copy failed:', error);
        showToast('❌ 코드 복사에 실패했습니다.');
    }
}

// 코드 실행
function executeCode(codeId, language) {
    try {
        var codeElement = document.getElementById(codeId);
        if (!codeElement) {
            showToast('코드 요소를 찾을 수 없습니다.');
            return;
        }
        
        var codeText = codeElement.textContent || codeElement.innerText;
        
        if (pyqt_bridge && pyqt_bridge.executeCode) {
            showToast('⏳ 코드 실행 중...');
            pyqt_bridge.executeCode(codeText, language);
        } else {
            showToast('❌ 코드 실행 기능을 사용할 수 없습니다.');
        }
    } catch (error) {
        console.error('Code execution failed:', error);
        showToast('❌ 코드 실행에 실패했습니다.');
    }
}

// 메시지 삭제
function deleteMessage(messageId) {
    try {
        var targetId = messageId || currentSelectedMessage;
        if (!targetId) {
            showToast('메시지를 먼저 선택해주세요.');
            return;
        }
        
        if (pyqt_bridge && pyqt_bridge.deleteMessage) {
            pyqt_bridge.deleteMessage(targetId);
        }
    } catch (error) {
        console.error('Message delete failed:', error);
    }
}

// DOM에서 메시지 제거
function removeMessageFromDOM(messageId) {
    try {
        var messageElements = document.querySelectorAll('[data-message-id="' + messageId + '"]');
        for (var i = 0; i < messageElements.length; i++) {
            messageElements[i].remove();
        }
    } catch (error) {
        console.error('DOM message removal failed:', error);
    }
}
