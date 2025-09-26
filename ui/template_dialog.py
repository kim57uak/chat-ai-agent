"""템플릿 관리 대화상자"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QTextEdit, QLineEdit,
                            QComboBox, QLabel, QCheckBox, QSplitter, QGroupBox,
                            QMessageBox, QInputDialog, QFileDialog, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette
from ui.template_manager import template_manager, Template
from ui.styles.theme_manager import theme_manager
import json


class TemplateDialog(QDialog):
    """템플릿 관리 대화상자"""
    
    template_selected = pyqtSignal(str)  # 템플릿 내용 전달
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 템플릿 관리")
        self.setModal(True)
        self.resize(1000, 700)
        self.current_template = None
        self._apply_modern_style()
        self._setup_ui()
        self._load_templates()
        self._connect_signals()
    
    def _apply_modern_style(self):
        """현대적 스타일 적용 - Soft Shadow + Rounded Edge + Gradient Depth"""
        if theme_manager.use_material_theme:
            colors = theme_manager.material_manager.get_theme_colors()
            is_dark = colors.get('background', '#121212') in ['#121212', '#1e1e1e']
            shadow_color = "rgba(0,0,0,0.3)" if is_dark else "rgba(0,0,0,0.15)"
            
            self.setStyleSheet(f"""
                QDialog {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('background', '#121212')}, 
                        stop:1 {colors.get('surface', '#1e1e1e')});
                    color: {colors.get('text_primary', '#ffffff')};
                    border-radius: 20px;
                }}
                QGroupBox {{
                    font-weight: 600;
                    font-size: 14px;
                    color: {colors.get('text_primary', '#ffffff')};
                    border: 2px solid {colors.get('divider', '#333333')};
                    border-radius: 16px;
                    margin-top: 12px;
                    padding-top: 8px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('surface', '#1e1e1e')}, 
                        stop:1 {colors.get('background', '#121212')});
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 16px;
                    padding: 4px 12px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('primary', '#bb86fc')}, 
                        stop:1 {colors.get('primary_variant', '#3700b3')});
                    color: {colors.get('on_primary', '#000000')};
                    border-radius: 8px;
                    font-weight: 800;
                }}
                QListWidget {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('surface', '#1e1e1e')}, 
                        stop:1 {colors.get('background', '#121212')});
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 12px;
                    padding: 8px;
                    font-size: 14px;
                }}
                QListWidget::item {{
                    padding: 12px 16px;
                    margin: 2px 0;
                    border-radius: 10px;
                    border: none;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('background', '#121212')}, 
                        stop:1 {colors.get('surface', '#1e1e1e')});
                    transition: all 0.3s ease;
                }}
                QListWidget::item:selected {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('primary', '#bb86fc')}, 
                        stop:1 {colors.get('primary_variant', '#3700b3')});
                    color: {colors.get('on_primary', '#000000')};
                    transform: translateY(-1px);
                }}
                QListWidget::item:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('user_bg', 'rgba(187, 134, 252, 0.12)')}, 
                        stop:1 {colors.get('surface', '#1e1e1e')});
                    transform: translateY(-1px);
                }}
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('primary', '#bb86fc')}, 
                        stop:1 {colors.get('primary_variant', '#3700b3')});
                    color: {colors.get('on_primary', '#000000')};
                    border: none;
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-weight: 600;
                    font-size: 14px;
                    min-height: 20px;
                    transition: all 0.3s ease;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('secondary', '#03dac6')}, 
                        stop:1 {colors.get('primary', '#bb86fc')});
                    transform: translateY(-2px);
                }}
                QPushButton:pressed {{
                    background: {colors.get('primary_variant', '#3700b3')};
                    transform: translateY(0px);
                }}
                QTextEdit, QLineEdit {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('surface', '#1e1e1e')}, 
                        stop:1 {colors.get('background', '#121212')});
                    color: {colors.get('text_primary', '#ffffff')};
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 12px;
                    padding: 12px;
                    font-size: 14px;
                    transition: all 0.3s ease;
                }}
                QTextEdit:focus, QLineEdit:focus {{
                    border-color: {colors.get('primary', '#bb86fc')};
                    border-width: 2px;
                    transform: translateY(-1px);
                }}
                QComboBox {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('surface', '#1e1e1e')}, 
                        stop:1 {colors.get('background', '#121212')});
                    color: {colors.get('text_primary', '#ffffff')};
                    border: 1px solid {colors.get('divider', '#333333')};
                    border-radius: 12px;
                    padding: 8px 12px;
                    font-size: 14px;
                    min-height: 20px;
                    transition: all 0.3s ease;
                }}
                QComboBox:hover {{
                    border-color: {colors.get('primary', '#bb86fc')};
                    transform: translateY(-1px);
                }}
                QCheckBox {{
                    color: {colors.get('text_primary', '#ffffff')};
                    font-size: 14px;
                    spacing: 8px;
                    background: transparent;
                }}
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {colors.get('primary', '#bb86fc')};
                    border-radius: 6px;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('surface', '#1e1e1e')}, 
                        stop:1 {colors.get('background', '#121212')});
                    transition: all 0.3s ease;
                }}
                QCheckBox::indicator:checked {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 {colors.get('primary', '#bb86fc')}, 
                        stop:1 {colors.get('primary_variant', '#3700b3')});
                    border-color: {colors.get('secondary', '#03dac6')};
                    transform: translateY(-1px);
                }}
                QLabel {{
                    color: {colors.get('text_primary', '#ffffff')};
                    font-size: 14px;
                    font-weight: 500;
                    background: transparent;
                }}
                QSplitter::handle {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 {colors.get('divider', '#333333')}, 
                        stop:1 {colors.get('text_secondary', '#888888')});
                    border-radius: 6px;
                    margin: 2px;
                    transition: all 0.3s ease;
                }}
                QSplitter::handle:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                        stop:0 {colors.get('text_secondary', '#888888')}, 
                        stop:1 {colors.get('primary', '#bb86fc')});
                    transform: translateY(-1px);
                }}
            """)
    
    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 상단 버튼들
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        self.new_btn = QPushButton("➕ 새 템플릿")
        self.import_btn = QPushButton("📁 가져오기")
        self.export_btn = QPushButton("📤 내보내기")
        self.delete_btn = QPushButton("🗑️ 삭제")
        
        top_layout.addWidget(self.new_btn)
        top_layout.addWidget(self.import_btn)
        top_layout.addWidget(self.export_btn)
        top_layout.addWidget(self.delete_btn)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 메인 스플리터 - Soft Shadow + Rounded Edge + Gradient Depth
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 왼쪽: 템플릿 목록
        left_widget = self._create_template_list()
        splitter.addWidget(left_widget)
        
        # 오른쪽: 템플릿 편집
        right_widget = self._create_template_editor()
        splitter.addWidget(right_widget)
        
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)
        
        # 하단 버튼들
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)
        
        self.use_btn = QPushButton("✅ 사용하기")
        self.save_btn = QPushButton("💾 저장")
        self.close_btn = QPushButton("❌ 닫기")
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.use_btn)
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.close_btn)
        
        layout.addLayout(bottom_layout)
    
    def _create_template_list(self):
        """템플릿 목록 위젯 생성"""
        group = QGroupBox("📁 템플릿 목록")
        layout = QVBoxLayout(group)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 24, 20, 20)
        
        # 카테고리 필터
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        filter_layout.addWidget(QLabel("📊 카테고리:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("전체")
        self.category_filter.addItems(template_manager.categories)
        filter_layout.addWidget(self.category_filter)
        layout.addLayout(filter_layout)
        
        # 검색
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        search_layout.addWidget(QLabel("🔍 검색:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("템플릿 이름 또는 내용 검색...")
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # 템플릿 리스트
        self.template_list = QListWidget()
        self.template_list.setMinimumHeight(300)
        layout.addWidget(self.template_list)
        
        return group
    
    def _create_template_editor(self):
        """템플릿 편집 위젯 생성"""
        group = QGroupBox("템플릿 편집")
        layout = QVBoxLayout(group)
        
        # 템플릿 정보
        info_layout = QVBoxLayout()
        
        # 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("이름:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        info_layout.addLayout(name_layout)
        
        # 카테고리
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("카테고리:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(template_manager.categories)
        cat_layout.addWidget(self.category_combo)
        
        # 즐겨찾기
        self.favorite_check = QCheckBox("즐겨찾기")
        cat_layout.addWidget(self.favorite_check)
        info_layout.addLayout(cat_layout)
        
        layout.addLayout(info_layout)
        
        # 내용
        layout.addWidget(QLabel("내용:"))
        self.content_edit = QTextEdit()
        self.content_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(self.content_edit)
        
        # 변수 정보
        var_layout = QHBoxLayout()
        var_layout.addWidget(QLabel("변수:"))
        self.variables_input = QLineEdit()
        self.variables_input.setPlaceholderText("변수명을 쉼표로 구분 (예: 파일명, 목적)")
        var_layout.addWidget(self.variables_input)
        layout.addLayout(var_layout)
        
        return group
    
    def _connect_signals(self):
        """시그널 연결"""
        self.template_list.itemClicked.connect(self._on_template_selected)
        self.category_filter.currentTextChanged.connect(self._filter_templates)
        self.search_input.textChanged.connect(self._search_templates)
        
        self.new_btn.clicked.connect(self._new_template)
        self.delete_btn.clicked.connect(self._delete_template)
        self.import_btn.clicked.connect(self._import_templates)
        self.export_btn.clicked.connect(self._export_templates)
        
        self.use_btn.clicked.connect(self._use_template)
        self.save_btn.clicked.connect(self._save_template)
        self.close_btn.clicked.connect(self.close)
        
        template_manager.templates_changed.connect(self._load_templates)
    
    def _load_templates(self):
        """템플릿 목록 로드"""
        self.template_list.clear()
        templates = template_manager.templates
        
        for template in templates:
            item = QListWidgetItem()
            star = "⭐ " if template.favorite else "📄 "
            category_icon = "📊 "
            item.setText(f"{star}{template.name}\n{category_icon}{template.category}")
            item.setData(Qt.ItemDataRole.UserRole, template.name)
            self.template_list.addItem(item)
    
    def _filter_templates(self):
        """카테고리 필터링"""
        category = self.category_filter.currentText()
        self.template_list.clear()
        
        if category == "전체":
            templates = template_manager.templates
        else:
            templates = template_manager.get_templates_by_category(category)
        
        for template in templates:
            item = QListWidgetItem()
            star = "⭐ " if template.favorite else "📄 "
            category_icon = "📊 "
            item.setText(f"{star}{template.name}\n{category_icon}{template.category}")
            item.setData(Qt.ItemDataRole.UserRole, template.name)
            self.template_list.addItem(item)
    
    def _search_templates(self):
        """템플릿 검색"""
        query = self.search_input.text().strip()
        self.template_list.clear()
        
        if not query:
            self._load_templates()
            return
        
        templates = template_manager.search_templates(query)
        for template in templates:
            item = QListWidgetItem()
            star = "⭐ " if template.favorite else "📄 "
            category_icon = "📊 "
            item.setText(f"{star}{template.name}\n{category_icon}{template.category}")
            item.setData(Qt.ItemDataRole.UserRole, template.name)
            self.template_list.addItem(item)
    
    def _on_template_selected(self, item):
        """템플릿 선택 시"""
        template_name = item.data(Qt.ItemDataRole.UserRole)
        template = template_manager.get_template(template_name)
        
        if template:
            self.current_template = template
            self.name_input.setText(template.name)
            self.category_combo.setCurrentText(template.category)
            self.content_edit.setPlainText(template.content)
            self.favorite_check.setChecked(template.favorite)
            self.variables_input.setText(", ".join(template.variables))
    
    def _new_template(self):
        """새 템플릿 생성"""
        self.current_template = None
        self.name_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.content_edit.clear()
        self.favorite_check.setChecked(False)
        self.variables_input.clear()
    
    def _save_template(self):
        """템플릿 저장"""
        name = self.name_input.text().strip()
        content = self.content_edit.toPlainText().strip()
        
        if not name or not content:
            QMessageBox.warning(self, "경고", "이름과 내용을 입력해주세요.")
            return
        
        # 중복 이름 체크 (현재 편집 중인 템플릿 제외)
        existing = template_manager.get_template(name)
        if existing and (not self.current_template or existing.name != self.current_template.name):
            QMessageBox.warning(self, "경고", "같은 이름의 템플릿이 이미 존재합니다.")
            return
        
        category = self.category_combo.currentText()
        favorite = self.favorite_check.isChecked()
        variables = [v.strip() for v in self.variables_input.text().split(",") if v.strip()]
        
        if self.current_template:
            # 기존 템플릿 수정
            template_manager.remove_template(self.current_template.name)
        
        # 새 템플릿 추가
        template = Template(name, content, category, variables, favorite)
        template_manager.add_template(template)
        
        QMessageBox.information(self, "완료", "템플릿이 저장되었습니다.")
        self._load_templates()
    
    def _delete_template(self):
        """템플릿 삭제"""
        if not self.current_template:
            QMessageBox.warning(self, "경고", "삭제할 템플릿을 선택해주세요.")
            return
        
        reply = QMessageBox.question(
            self, "확인", 
            f"'{self.current_template.name}' 템플릿을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            template_manager.remove_template(self.current_template.name)
            self._new_template()
            QMessageBox.information(self, "완료", "템플릿이 삭제되었습니다.")
    
    def _use_template(self):
        """템플릿 사용"""
        if not self.current_template:
            QMessageBox.warning(self, "경고", "사용할 템플릿을 선택해주세요.")
            return
        
        content = template_manager.use_template(self.current_template.name)
        if content:
            # 변수 치환 처리
            if self.current_template.variables:
                content = self._process_variables(content, self.current_template.variables)
            
            self.template_selected.emit(content)
            self.close()
    
    def _process_variables(self, content: str, variables: list) -> str:
        """변수 치환 처리"""
        for var in variables:
            placeholder = f"{{{var}}}"
            if placeholder in content:
                value, ok = QInputDialog.getText(
                    self, "변수 입력", f"{var}의 값을 입력하세요:"
                )
                if ok and value:
                    content = content.replace(placeholder, value)
        return content
    
    def _import_templates(self):
        """템플릿 가져오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "템플릿 파일 선택", "", "JSON 파일 (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                imported_count = 0
                for item in data:
                    template = Template.from_dict(item)
                    # 중복 이름 체크
                    if not template_manager.get_template(template.name):
                        template_manager.add_template(template)
                        imported_count += 1
                
                QMessageBox.information(
                    self, "완료", f"{imported_count}개의 템플릿을 가져왔습니다."
                )
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일을 가져오는 중 오류가 발생했습니다:\n{e}")
    
    def _export_templates(self):
        """템플릿 내보내기"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "템플릿 저장", "templates.json", "JSON 파일 (*.json)"
        )
        
        if file_path:
            try:
                data = [t.to_dict() for t in template_manager.templates]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(
                    self, "완료", f"템플릿을 {file_path}에 저장했습니다."
                )
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일을 저장하는 중 오류가 발생했습니다:\n{e}")