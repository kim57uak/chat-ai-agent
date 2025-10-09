"""
from core.logging import get_logger

logger = get_logger("pdf_exporter")
PDF Export functionality for chat conversations
HTML 대화 내용을 PDF로 변환하는 기능
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPageLayout, QPageSize
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QMarginsF
import tempfile


class PDFExportWorker(QObject):
    """PDF 내보내기 작업을 처리하는 워커"""
    
    finished = pyqtSignal(bool, str)  # 성공 여부, 메시지
    progress = pyqtSignal(str)  # 진행 상황
    
    def __init__(self, html_content: str, output_path: str):
        super().__init__()
        self.html_content = html_content
        self.output_path = output_path
    
    def export_pdf(self):
        """PDF 내보내기 실행"""
        try:
            self.progress.emit("PDF 생성 준비 중...")
            
            # 임시 HTML 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(self.html_content)
                temp_html_path = temp_file.name
            
            self.progress.emit("웹 엔진 초기화 중...")
            
            # QWebEngineView를 사용하여 PDF 생성
            web_view = QWebEngineView()
            
            def on_load_finished(success):
                if success:
                    self.progress.emit("PDF 변환 중...")
                    
                    # PDF 프린터 설정
                    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                    printer.setOutputFileName(self.output_path)
                    
                    # 페이지 설정
                    page_layout = QPageLayout()
                    page_layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                    page_layout.setOrientation(QPageLayout.Orientation.Portrait)
                    page_layout.setMargins(QMarginsF(20, 20, 20, 20))
                    printer.setPageLayout(page_layout)
                    
                    # PDF로 직접 출력
                    def on_pdf_finished(pdf_data):
                        try:
                            with open(self.output_path, 'wb') as f:
                                f.write(pdf_data)
                            self._on_print_finished(True, temp_html_path)
                        except Exception as e:
                            logger.debug(f"PDF 저장 오류: {e}")
                            self._on_print_finished(False, temp_html_path)
                    
                    # PyQt6에서는 printToPdf 사용
                    web_view.page().printToPdf(on_pdf_finished)
                else:
                    self._cleanup_and_finish(False, "HTML 로드 실패", temp_html_path)
            
            web_view.loadFinished.connect(on_load_finished)
            web_view.load(QUrl.fromLocalFile(temp_html_path))
            
        except Exception as e:
            self.finished.emit(False, f"PDF 생성 오류: {str(e)}")
    
    def _on_print_finished(self, success: bool, temp_html_path: str):
        """인쇄 완료 처리"""
        if success:
            self._cleanup_and_finish(True, "PDF 생성 완료", temp_html_path)
        else:
            self._cleanup_and_finish(False, "PDF 인쇄 실패", temp_html_path)
    
    def _cleanup_and_finish(self, success: bool, message: str, temp_html_path: str):
        """정리 작업 및 완료 처리"""
        try:
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
        except:
            pass
        
        self.finished.emit(success, message)


class PDFExporter:
    """PDF 내보내기 클래스"""
    
    def __init__(self, parent=None):
        self.parent = parent
    
    def export_conversation_to_pdf(self, messages: List[Dict], session_title: str = "대화") -> bool:
        """대화 내용을 PDF로 내보내기"""
        try:
            # 파일 저장 대화상자
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"{session_title}_{timestamp}.pdf"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent,
                "PDF로 내보내기",
                default_filename,
                "PDF 파일 (*.pdf)"
            )
            
            if not file_path:
                return False
            
            # HTML 생성
            html_content = self._generate_html_content(messages, session_title)
            
            # PDF 생성 (동기 방식으로 간단하게 구현)
            return self._create_pdf_sync(html_content, file_path)
            
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "오류", f"PDF 내보내기 실패: {str(e)}")
            return False
    
    def _generate_html_content(self, messages: List[Dict], session_title: str) -> str:
        """대화 내용을 HTML로 변환"""
        html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', '맑은 고딕', Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            color: #333;
            background-color: #fff;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 2px solid #4a90e2;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #4a90e2;
            margin: 0;
            font-size: 28px;
        }}
        
        .export-info {{
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }}
        
        .message {{
            margin-bottom: 25px;
            padding: 15px;
            border-radius: 8px;
            page-break-inside: avoid;
        }}
        
        .message.user {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            margin-left: 20px;
        }}
        
        .message.assistant {{
            background-color: #f5f5f5;
            border-left: 4px solid #4caf50;
            margin-right: 20px;
        }}
        
        .message-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        
        .message-role {{
            color: #4a90e2;
            font-size: 16px;
        }}
        
        .message-time {{
            color: #666;
            font-size: 12px;
            font-weight: normal;
        }}
        
        .message-content {{
            font-size: 14px;
            line-height: 1.7;
            word-wrap: break-word;
        }}
        
        .message-content h1, .message-content h2, .message-content h3 {{
            color: #333;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        .message-content code {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
        }}
        
        .message-content pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 13px;
            line-height: 1.4;
        }}
        
        .message-content ul, .message-content ol {{
            margin-left: 20px;
        }}
        
        .message-content blockquote {{
            border-left: 3px solid #ddd;
            margin-left: 0;
            padding-left: 15px;
            color: #666;
            font-style: italic;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        
        @media print {{
            body {{
                margin: 0;
                padding: 15px;
            }}
            
            .message {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="export-info">
            내보낸 날짜: {export_date}<br>
            총 메시지 수: {message_count}개
        </div>
    </div>
    
    <div class="messages">
        {messages_html}
    </div>
    
    <div class="footer">
        Chat AI Agent에서 생성됨 - {export_date}
    </div>
</body>
</html>
        """
        
        # 메시지를 HTML로 변환
        messages_html = ""
        for i, message in enumerate(messages):
            role = message.get('role', 'unknown')
            content = message.get('content', '')
            timestamp = message.get('timestamp', '')
            
            # 역할 표시명 변경
            role_display = "사용자" if role == "user" else "AI 어시스턴트"
            
            # 시간 포맷팅
            time_display = ""
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        # ISO 형식 파싱 시도
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_display = dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        time_display = str(timestamp)
                except:
                    time_display = str(timestamp)
            
            # HTML 내용 정리 (기본 마크다운 지원)
            content_html = self._format_content_for_pdf(content)
            
            messages_html += f"""
            <div class="message {role}">
                <div class="message-header">
                    <span class="message-role">{role_display}</span>
                    <span class="message-time">{time_display}</span>
                </div>
                <div class="message-content">
                    {content_html}
                </div>
            </div>
            """
        
        # HTML 템플릿 완성
        export_date = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        
        return html_template.format(
            title=session_title,
            export_date=export_date,
            message_count=len(messages),
            messages_html=messages_html
        )
    
    def _format_content_for_pdf(self, content: str) -> str:
        """PDF용 콘텐츠 포맷팅"""
        if not content:
            return ""
        
        # 이미 HTML로 렌더링된 콘텐츠인지 확인
        if content.strip().startswith('<') and ('</p>' in content or '</div>' in content or '</li>' in content or '</ol>' in content or '</ul>' in content):
            # HTML 콘텐츠는 그대로 사용
            return content
        
        # 일반 텍스트인 경우 HTML로 변환
        import html
        content = html.escape(content)
        
        # 기본 마크다운 변환
        lines = content.split('\n')
        formatted_lines = []
        in_code_block = False
        
        for line in lines:
            # 코드 블록 처리
            if line.strip().startswith('```'):
                if in_code_block:
                    formatted_lines.append('</pre>')
                    in_code_block = False
                else:
                    formatted_lines.append('<pre>')
                    in_code_block = True
                continue
            
            if in_code_block:
                formatted_lines.append(line)
                continue
            
            # 제목 처리
            if line.startswith('### '):
                formatted_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('## '):
                formatted_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('# '):
                formatted_lines.append(f'<h1>{line[2:]}</h1>')
            # 불릿 포인트 처리
            elif line.strip().startswith('- '):
                if not formatted_lines or not formatted_lines[-1].startswith('<ul>'):
                    formatted_lines.append('<ul>')
                formatted_lines.append(f'<li>{line.strip()[2:]}</li>')
            elif line.strip().startswith('* '):
                if not formatted_lines or not formatted_lines[-1].startswith('<ul>'):
                    formatted_lines.append('<ul>')
                formatted_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                # 이전 줄이 리스트였다면 닫기
                if formatted_lines and formatted_lines[-1].startswith('<li>'):
                    formatted_lines.append('</ul>')
                
                # 빈 줄이 아니면 문단으로 처리
                if line.strip():
                    # 인라인 코드 처리
                    line = self._process_inline_code(line)
                    formatted_lines.append(f'<p>{line}</p>')
                else:
                    formatted_lines.append('<br>')
        
        # 마지막에 열린 리스트 닫기
        if formatted_lines and formatted_lines[-1].startswith('<li>'):
            formatted_lines.append('</ul>')
        
        # 마지막에 열린 코드 블록 닫기
        if in_code_block:
            formatted_lines.append('</pre>')
        
        return '\n'.join(formatted_lines)
    
    def _process_inline_code(self, text: str) -> str:
        """인라인 코드 처리"""
        import re
        # `code` 형태를 <code>code</code>로 변환
        return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    def _create_pdf_sync(self, html_content: str, output_path: str) -> bool:
        """동기 방식으로 PDF 생성"""
        try:
            # 임시 HTML 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(html_content)
                temp_html_path = temp_file.name
            
            # QWebEngineView를 사용하여 PDF 생성
            web_view = QWebEngineView()
            
            # 로드 완료를 기다리기 위한 플래그
            load_finished = False
            print_success = False
            
            def on_load_finished(success):
                nonlocal load_finished
                load_finished = success
                
                if success:
                    # PDF로 직접 출력
                    def on_pdf_finished(pdf_data):
                        nonlocal print_success
                        try:
                            with open(output_path, 'wb') as f:
                                f.write(pdf_data)
                            print_success = True
                        except Exception as e:
                            logger.debug(f"PDF 저장 오류: {e}")
                            print_success = False
                    
                    # PyQt6에서는 printToPdf 사용
                    web_view.page().printToPdf(on_pdf_finished)
            
            web_view.loadFinished.connect(on_load_finished)
            web_view.load(QUrl.fromLocalFile(temp_html_path))
            
            # 로드 완료까지 대기 (최대 15초)
            from PyQt6.QtCore import QEventLoop, QTimer
            loop = QEventLoop()
            timer = QTimer()
            timer.timeout.connect(loop.quit)
            timer.start(15000)  # 15초 타임아웃
            
            def check_finished():
                if load_finished and print_success:
                    timer.stop()
                    loop.quit()
            
            check_timer = QTimer()
            check_timer.timeout.connect(check_finished)
            check_timer.start(200)  # 200ms마다 체크
            
            loop.exec()
            
            # 정리
            try:
                if os.path.exists(temp_html_path):
                    os.unlink(temp_html_path)
            except:
                pass
            
            if load_finished and print_success:
                if self.parent:
                    QMessageBox.information(self.parent, "완료", f"PDF가 성공적으로 생성되었습니다:\n{output_path}")
                return True
            else:
                if self.parent:
                    QMessageBox.warning(self.parent, "오류", "PDF 생성에 실패했습니다.")
                return False
                
        except Exception as e:
            if self.parent:
                QMessageBox.critical(self.parent, "오류", f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
            return False