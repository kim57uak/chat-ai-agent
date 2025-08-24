"""첨부파일 처리 UI 컴포넌트"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
import os


class AttachmentPreview(QFrame):
    """첨부파일 미리보기 위젯"""
    
    remove_requested = pyqtSignal(str)  # 파일 제거 요청
    
    def __init__(self, file_path, file_name, file_size, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = file_name
        self.file_size = file_size
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """UI 구성"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # 파일 아이콘
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setText(self._get_file_icon())
        layout.addWidget(self.icon_label)
        
        # 파일 정보
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self.name_label = QLabel(self.file_name)
        self.name_label.setFont(QFont("SF Pro Display", 13, QFont.Weight.DemiBold))
        
        self.size_label = QLabel(self._format_file_size())
        self.size_label.setFont(QFont("SF Pro Display", 11))
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.size_label)
        layout.addLayout(info_layout, 1)
        
        # 제거 버튼
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setFixedSize(28, 28)
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.file_path))
        layout.addWidget(self.remove_btn)
    
    def _apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet("""
            AttachmentPreview {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(59, 130, 246, 0.1), 
                    stop:1 rgba(37, 99, 235, 0.1));
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 10px;
                margin: 4px 0;
            }
            
            AttachmentPreview:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 rgba(59, 130, 246, 0.15), 
                    stop:1 rgba(37, 99, 235, 0.15));
                border-color: rgba(59, 130, 246, 0.4);
            }
            
            QLabel {
                color: #f3f4f6;
                background: transparent;
                border: none;
            }
            
            QPushButton {
                background: rgba(239, 68, 68, 0.8);
                color: #ffffff;
                border: none;
                border-radius: 14px;
                font-weight: 600;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background: rgba(239, 68, 68, 1.0);
                transform: scale(1.1);
            }
        """)
        
        # 파일명 색상
        self.name_label.setStyleSheet("color: #60a5fa; font-weight: 600;")
        self.size_label.setStyleSheet("color: #9ca3af; font-weight: 400;")
        
        # 아이콘 스타일
        self.icon_label.setStyleSheet("""
            background: rgba(59, 130, 246, 0.2);
            border-radius: 20px;
            color: #60a5fa;
            font-size: 18px;
            font-weight: 600;
        """)
    
    def _get_file_icon(self):
        """파일 타입별 아이콘 반환"""
        ext = os.path.splitext(self.file_name)[1].lower()
        
        icon_map = {
            '.pdf': '📄', '.doc': '📝', '.docx': '📝',
            '.xls': '📊', '.xlsx': '📊', '.csv': '📊',
            '.ppt': '📊', '.pptx': '📊',
            '.txt': '📄', '.md': '📄',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', 
            '.gif': '🖼️', '.bmp': '🖼️', '.webp': '🖼️',
            '.json': '⚙️', '.xml': '⚙️', '.yaml': '⚙️',
            '.zip': '📦', '.rar': '📦', '.7z': '📦'
        }
        
        return icon_map.get(ext, '📁')
    
    def _format_file_size(self):
        """파일 크기 포맷팅"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"


class AttachmentArea(QWidget):
    """첨부파일 영역 위젯"""
    
    files_changed = pyqtSignal(list)  # 파일 목록 변경 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.attached_files = []  # 첨부된 파일 목록
        
        self._setup_ui()
        self._apply_styles()
        self.hide()  # 초기에는 숨김
    
    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 헤더
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("📎 첨부파일")
        self.title_label.setFont(QFont("SF Pro Display", 12, QFont.Weight.DemiBold))
        
        self.clear_all_btn = QPushButton("모두 제거")
        self.clear_all_btn.clicked.connect(self.clear_all_files)
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(header_layout)
        
        # 스크롤 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumHeight(200)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 파일 목록 컨테이너
        self.files_container = QWidget()
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setContentsMargins(0, 0, 0, 0)
        self.files_layout.setSpacing(4)
        
        self.scroll_area.setWidget(self.files_container)
        layout.addWidget(self.scroll_area)
    
    def _apply_styles(self):
        """스타일 적용"""
        self.setStyleSheet("""
            AttachmentArea {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 rgba(31, 41, 55, 0.8), 
                    stop:1 rgba(17, 24, 39, 0.8));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 16px;
                margin: 8px 0;
            }
            
            QLabel {
                color: #f3f4f6;
                background: transparent;
            }
            
            QPushButton {
                background: rgba(239, 68, 68, 0.8);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
            }
            
            QPushButton:hover {
                background: rgba(239, 68, 68, 1.0);
            }
            
            QScrollArea {
                background: transparent;
                border: none;
            }
            
            QScrollBar:vertical {
                background: rgba(55, 65, 81, 0.5);
                width: 8px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(107, 114, 128, 0.8);
                border-radius: 4px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(156, 163, 175, 0.8);
            }
        """)
    
    def add_file(self, file_path, file_name=None, file_size=None):
        """파일 추가"""
        if not file_name:
            file_name = os.path.basename(file_path)
        
        if not file_size:
            try:
                file_size = os.path.getsize(file_path)
            except:
                file_size = 0
        
        # 중복 확인
        for existing_file in self.attached_files:
            if existing_file['path'] == file_path:
                return False
        
        # 파일 정보 저장
        file_info = {
            'path': file_path,
            'name': file_name,
            'size': file_size
        }
        self.attached_files.append(file_info)
        
        # 미리보기 위젯 생성
        preview = AttachmentPreview(file_path, file_name, file_size)
        preview.remove_requested.connect(self.remove_file)
        
        self.files_layout.addWidget(preview)
        
        # 영역 표시
        self.show()
        self.files_changed.emit(self.attached_files)
        
        return True
    
    def remove_file(self, file_path):
        """파일 제거"""
        # 파일 정보에서 제거
        self.attached_files = [f for f in self.attached_files if f['path'] != file_path]
        
        # 위젯에서 제거
        for i in range(self.files_layout.count()):
            widget = self.files_layout.itemAt(i).widget()
            if isinstance(widget, AttachmentPreview) and widget.file_path == file_path:
                widget.deleteLater()
                break
        
        # 파일이 없으면 영역 숨김
        if not self.attached_files:
            self.hide()
        
        self.files_changed.emit(self.attached_files)
    
    def clear_all_files(self):
        """모든 파일 제거"""
        self.attached_files.clear()
        
        # 모든 위젯 제거
        while self.files_layout.count():
            child = self.files_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.hide()
        self.files_changed.emit(self.attached_files)
    
    def get_files(self):
        """첨부된 파일 목록 반환"""
        return self.attached_files.copy()