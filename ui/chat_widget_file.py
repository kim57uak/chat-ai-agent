"""
Chat Widget File Mixin
채팅 위젯 파일 처리 메서드 분리
"""

from PyQt6.QtWidgets import QFileDialog
from ui.components.file_handler import FileHandler
from ui.components.ai_processor import AIProcessor
from core.logging import get_logger

logger = get_logger("chat_widget_file")


class ChatWidgetFileMixin:
    """채팅 위젯 파일 처리 메서드"""
    
    def upload_file(self):
        """파일 업로드"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '파일 선택', '', 
            '모든 파일 (*);;텍스트 파일 (*.txt);;PDF 파일 (*.pdf);;Word 파일 (*.docx *.doc);;Excel 파일 (*.xlsx *.xls);;PowerPoint 파일 (*.pptx *.ppt);;JSON 파일 (*.json);;이미지 파일 (*.jpg *.jpeg *.png *.gif *.bmp *.webp);;CSV 파일 (*.csv)'
        )
        if not file_path:
            return
        
        self.ai_processor.cancel()
        self.ai_processor = AIProcessor(self)
        self.ai_processor.finished.connect(self.on_ai_response)
        self.ai_processor.error.connect(self.on_ai_error)
        self.ai_processor.streaming.connect(self.on_ai_streaming)
        self.ai_processor.conversation_completed.connect(self._on_conversation_completed)
        
        self._process_file_upload(file_path)
    
    def _process_file_upload(self, file_path):
        """파일 업로드 처리"""
        from ui.chat_widget import safe_single_shot
        
        try:
            content, filename = FileHandler.process_file(file_path)
            
            self.chat_display.append_message('사용자', f'📎 파일 업로드: {filename}')
            
            if "[IMAGE_BASE64]" not in content and len(content) > 5000:
                content = content[:5000] + "...(내용 생략)"
            
            self.uploaded_file_content = content
            self.uploaded_file_name = filename
            
            self.chat_display.append_message('시스템', f'파일이 업로드되었습니다. 이제 파일에 대해 무엇을 알고 싶은지 메시지를 입력해주세요.')
            
            safe_single_shot(300, self._scroll_to_bottom, self)
            safe_single_shot(700, self._scroll_to_bottom, self)
            self.input_text.setPlaceholderText(f"{filename}에 대해 무엇을 알고 싶으신가요? (Enter로 전송)")
            
        except Exception as e:
            self.chat_display.append_message('시스템', f'파일 처리 오류: {e}')
            self.uploaded_file_content = None
            self.uploaded_file_name = None
            self.input_text.setPlaceholderText("메시지를 입력하세요... (Enter로 전송, Shift+Enter로 줄바꿈)")
