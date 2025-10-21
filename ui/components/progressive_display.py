from PyQt6.QtCore import QTimer, QObject, pyqtSignal
import json
import uuid


class ProgressiveDisplay(QObject):
    """점진적 텍스트 출력을 담당하는 클래스"""
    
    display_complete = pyqtSignal()
    
    def __init__(self, web_view):
        super().__init__()
        self.web_view = web_view
        self.current_timer = None
        self.is_displaying = False
        
    def display_text_progressively(self, message_id, text, delay_per_line=50):
        """텍스트를 한 줄씩 점진적으로 출력 - 마크다운 파싱 보장"""
        if self.is_displaying:
            self.cancel_current_display()
        
        self.is_displaying = True
        
        # 원본 텍스트의 줄 구분으로 점진적 출력
        lines = text.split('\n')
        
        # 빈 컨테이너 생성
        self._create_empty_content(message_id)
        
        # 줄별로 순차적 렌더링
        self._display_lines_sequentially(message_id, lines, 0, delay_per_line, None)
    
    def _create_empty_content(self, message_id):
        """빈 컨텐츠 컨테이너 생성"""
        js_code = f"""
        try {{
            var contentDiv = document.getElementById('{message_id}_content');
            if (contentDiv) {{
                contentDiv.innerHTML = '';
            }}
        }} catch(e) {{
            console.log('Create empty content error:', e);
        }}
        """
        self.web_view.page().runJavaScript(js_code)
    
    def _display_lines_sequentially(self, message_id, lines, current_index, delay, full_formatted_text):
        """줄을 순차적으로 표시 - 전체 포맷팅 유지"""
        if not self.is_displaying or current_index >= len(lines):
            self.is_displaying = False
            self.display_complete.emit()
            return
        
        # 원본 텍스트의 현재까지 부분만 렌더링
        current_text = '\n'.join(lines[:current_index + 1])
        
        # 현재 텍스트를 다시 렌더링
        from ui.renderers import ContentRenderer
        renderer = ContentRenderer()
        current_formatted = renderer.render(current_text)
        
        # 컨텐츠 업데이트
        safe_content = json.dumps(current_formatted, ensure_ascii=False)
        js_code = f"""
        try {{
            var contentDiv = document.getElementById('{message_id}_content');
            if (contentDiv) {{
                contentDiv.innerHTML = {safe_content};
                
                // MathJax 렌더링
                if (window.MathJax && MathJax.typesetPromise) {{
                    MathJax.typesetPromise([contentDiv]).catch(err => console.error('MathJax error:', err));
                }}
                
                // Mermaid 렌더링
                setTimeout(() => {{
                    if (typeof mermaid !== 'undefined') {{
                        try {{
                            mermaid.run();
                        }} catch (e) {{
                            console.error('Mermaid error:', e);
                        }}
                    }}
                }}, 100);
                
                window.scrollTo(0, document.body.scrollHeight);
            }}
        }} catch(e) {{
            console.log('Update content error:', e);
        }}
        """
        self.web_view.page().runJavaScript(js_code)
        
        # 다음 줄 예약
        self.current_timer = QTimer()
        self.current_timer.setSingleShot(True)
        self.current_timer.timeout.connect(
            lambda: self._display_lines_sequentially(message_id, lines, current_index + 1, delay, full_formatted_text)
        )
        self.current_timer.start(delay)
    
    def cancel_current_display(self):
        """현재 진행 중인 출력 취소"""
        if self.current_timer:
            self.current_timer.stop()
            self.current_timer = None
        self.is_displaying = False
    
    def is_currently_displaying(self):
        """현재 출력 중인지 확인"""
        return self.is_displaying