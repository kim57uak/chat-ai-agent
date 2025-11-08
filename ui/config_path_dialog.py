"""Configuration path selection dialog."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from utils.config_path import config_path_manager
from pathlib import Path


class ConfigPathDialog(QDialog):
    """Dialog for selecting user configuration path."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('설정 파일 경로 설정')
        self.setModal(True)
        self.resize(500, 150)
        self._setup_ui()
        self._load_current_path()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        
        # Description
        desc_label = QLabel(
            "설정 파일들(config.json, mcp.json, news_config.json, prompt_config.json)을\n"
            "저장할 폴더를 선택하세요."
        )
        layout.addWidget(desc_label)
        
        # Path selection
        path_layout = QHBoxLayout()
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("설정 파일 저장 경로를 선택하세요...")
        path_layout.addWidget(self.path_edit)
        
        browse_btn = QPushButton("찾아보기")
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("확인")
        ok_btn.clicked.connect(self._accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        reset_btn = QPushButton("기본값으로 재설정")
        reset_btn.clicked.connect(self._reset_to_default)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
    
    def _load_current_path(self):
        """Load current configuration path."""
        current_path = config_path_manager.get_user_config_path()
        if current_path:
            self.path_edit.setText(str(current_path))
    
    def _browse_path(self):
        """Browse for configuration path."""
        path = QFileDialog.getExistingDirectory(
            self, 
            "설정 파일 저장 폴더 선택",
            str(Path.home())
        )
        if path:
            self.path_edit.setText(path)
    
    def _accept(self):
        """Accept and save the path."""
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "경고", "경로를 선택해주세요.")
            return
        
        try:
            if config_path_manager.set_user_config_path(path):
                QMessageBox.information(
                    self, 
                    "완료", 
                    f"설정 파일 경로가 변경되었습니다:\n{path}\n\n"
                    "애플리케이션을 재시작하면 새 경로의 설정 파일을 사용합니다."
                )
                self.accept()
            else:
                QMessageBox.critical(self, "오류", "경로 설정에 실패했습니다.\n로그를 확인하세요.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"경로 설정 중 오류 발생:\n{str(e)}")
    
    def _reset_to_default(self):
        """Reset to default (no user path)."""
        reply = QMessageBox.question(
            self, 
            "기본값 재설정", 
            "설정 파일 경로를 기본값(프로젝트 폴더)으로 재설정하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove user config path setting
            settings_file = config_path_manager._base_path / 'user_config_path.json'
            if settings_file.exists():
                settings_file.unlink()
            
            config_path_manager._user_config_path = None
            self.path_edit.clear()
            
            QMessageBox.information(
                self, 
                "완료", 
                "설정 파일 경로가 기본값으로 재설정되었습니다.\n"
                "애플리케이션을 재시작하면 프로젝트 폴더의 설정 파일을 사용합니다."
            )