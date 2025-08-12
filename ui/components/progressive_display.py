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
        
        # 전체 텍스트를 먼저 완전히 포맷팅
        from ui.markdown_formatter import MarkdownFormatter
        from ui.table_formatter import TableFormatter
        from ui.intelligent_formatter import IntelligentContentFormatter
        
        if '|' in text:
            formatter = IntelligentContentFormatter()
            full_formatted_text = formatter.format_content(text, 'AI')
        else:
            markdown_formatter = MarkdownFormatter()
            full_formatted_text = markdown_formatter.format_basic_markdown(text)
        
        # 원본 텍스트의 줄 구분으로 점진적 출력
        lines = text.split('\n')
        
        # 빈 컨테이너 생성
        self._create_empty_content(message_id)
        
        # 전체 포맷팅된 텍스트를 전달하여 점진적 출력
        self._display_lines_sequentially(message_id, lines, 0, delay_per_line, full_formatted_text)
    
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
        
        # 현재까지 표시할 줄 수 계산
        display_lines = current_index + 1
        
        # 전체 포맷팅된 텍스트에서 현재까지 표시할 부분만 추출
        formatted_lines = full_formatted_text.split('\n')
        current_formatted = '\n'.join(formatted_lines[:min(display_lines, len(formatted_lines))])
        
        # 컨텐츠 업데이트
        safe_content = json.dumps(current_formatted, ensure_ascii=False)
        js_code = f"""
        try {{
            var contentDiv = document.getElementById('{message_id}_content');
            if (contentDiv) {{
                contentDiv.innerHTML = {safe_content};
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