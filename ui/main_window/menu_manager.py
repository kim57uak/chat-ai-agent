"""
Menu Manager
메뉴바 관리 전담 클래스
"""

from PyQt6.QtGui import QAction
from ui.styles.theme_manager import theme_manager
from core.logging import get_logger

logger = get_logger("menu_manager")


class MenuManager:
    """메뉴바 관리 전담 클래스"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.main_window.menuBar()
        self._create_file_menu(menubar)
        self._create_settings_menu(menubar)
        self._create_extensions_menu(menubar)
        self._create_view_menu(menubar)
        self._create_tools_menu(menubar)
        self._create_security_menu(menubar)
        self._create_help_menu(menubar)
    
    def _create_file_menu(self, menubar):
        """파일 메뉴 생성"""
        file_menu = menubar.addMenu('📁 파일')
        
        # 새 세션
        new_session_action = QAction('새 세션', self.main_window)
        new_session_action.triggered.connect(self._new_session)
        file_menu.addAction(new_session_action)
        
        file_menu.addSeparator()
        
        # 종료
        exit_action = QAction('종료', self.main_window)
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)
    
    def _create_settings_menu(self, menubar):
        """설정 메뉴 생성"""
        settings_menu = menubar.addMenu('⚙️ 설정')
        
        # 환경설정
        settings_action = QAction('환경설정', self.main_window)
        settings_action.triggered.connect(self.main_window.dialog_manager.open_settings)
        settings_menu.addAction(settings_action)
        
        # 설정 파일 경로
        config_path_action = QAction('설정 파일 경로', self.main_window)
        config_path_action.triggered.connect(self.main_window.dialog_manager.open_config_path_dialog)
        settings_menu.addAction(config_path_action)
        
        settings_menu.addSeparator()
        
        # 유저 프롬프트
        user_prompt_action = QAction('유저 프롬프트', self.main_window)
        user_prompt_action.triggered.connect(self.main_window.dialog_manager.open_user_prompt)
        settings_menu.addAction(user_prompt_action)
    
    def _create_extensions_menu(self, menubar):
        """확장 기능 메뉴 생성"""
        extensions_menu = menubar.addMenu('🔌 확장 기능')
        
        # MCP 서버 관리
        mcp_manager_action = QAction('MCP 서버 관리', self.main_window)
        mcp_manager_action.triggered.connect(self.main_window.dialog_manager.open_mcp_manager)
        extensions_menu.addAction(mcp_manager_action)
        
        # MCP 확장 임포트
        mcp_action = QAction('MCP 확장 임포트', self.main_window)
        mcp_action.triggered.connect(self.main_window.dialog_manager.open_mcp)
        extensions_menu.addAction(mcp_action)
        
        extensions_menu.addSeparator()
        
        # RAG 관리
        rag_manager_action = QAction('RAG 관리', self.main_window)
        rag_manager_action.triggered.connect(self._open_document_manager)
        extensions_menu.addAction(rag_manager_action)
        
        # RAG 설정
        rag_settings_action = QAction('RAG 설정', self.main_window)
        rag_settings_action.triggered.connect(self._open_rag_settings)
        extensions_menu.addAction(rag_settings_action)
    
    def _create_view_menu(self, menubar):
        """보기 메뉴 생성"""
        view_menu = menubar.addMenu('🎨 보기')
        
        # 세션 패널 표시
        self.main_window.session_panel_action = QAction('세션 패널 표시', self.main_window)
        self.main_window.session_panel_action.setCheckable(True)
        self.main_window.session_panel_action.setChecked(True)
        self.main_window.session_panel_action.triggered.connect(
            self.main_window.layout_manager.toggle_session_panel
        )
        view_menu.addAction(self.main_window.session_panel_action)
        
        # 토큰 사용량 표시
        self.main_window.token_usage_action = QAction('토큰 사용량 표시', self.main_window)
        self.main_window.token_usage_action.setCheckable(True)
        self.main_window.token_usage_action.setChecked(True)
        self.main_window.token_usage_action.triggered.connect(
            self.main_window.layout_manager.toggle_token_display
        )
        view_menu.addAction(self.main_window.token_usage_action)
        
        view_menu.addSeparator()
        
        # 글래스모피즘 효과
        self.main_window.glassmorphism_action = QAction('글래스모피즘 효과', self.main_window)
        self.main_window.glassmorphism_action.setCheckable(True)
        self.main_window.glassmorphism_action.setChecked(
            theme_manager.material_manager.is_glassmorphism_enabled()
        )
        self.main_window.glassmorphism_action.triggered.connect(self._toggle_glassmorphism)
        view_menu.addAction(self.main_window.glassmorphism_action)
        
        view_menu.addSeparator()
        
        # 레이아웃 초기화
        reset_layout_action = QAction('레이아웃 초기화', self.main_window)
        reset_layout_action.triggered.connect(self.main_window.layout_manager.reset_layout)
        view_menu.addAction(reset_layout_action)
    
    def _create_tools_menu(self, menubar):
        """도구 메뉴 생성"""
        tools_menu = menubar.addMenu('🛠️ 도구')
        
        # 대화 기록 초기화
        clear_history_action = QAction('대화 기록 초기화', self.main_window)
        clear_history_action.triggered.connect(self._clear_conversation_history)
        tools_menu.addAction(clear_history_action)
        
        tools_menu.addSeparator()
        
        # RAG 테스트
        test_rag_action = QAction('RAG 테스트', self.main_window)
        test_rag_action.triggered.connect(self._test_rag_system)
        tools_menu.addAction(test_rag_action)
    
    def _create_help_menu(self, menubar):
        """도움말 메뉴 생성"""
        help_menu = menubar.addMenu('❓ 도움말')
        
        # 버전 정보
        about_action = QAction('버전 정보', self.main_window)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _open_document_manager(self):
        """문서 관리 대화상자 열기"""
        try:
            from ui.rag.rag_management_window import RAGManagementWindow
            from core.rag.storage.rag_storage_manager import RAGStorageManager
            from core.rag.embeddings.embedding_factory import EmbeddingFactory
            from core.rag.config.rag_config_manager import RAGConfigManager
            
            # RAG 윈도우가 없으면 생성 (지연 초기화)
            if not hasattr(self.main_window, 'rag_window'):
                self.main_window.rag_window = RAGManagementWindow(self.main_window)
            
            self.main_window.rag_window.show()
            self.main_window.rag_window.raise_()
            self.main_window.rag_window.activateWindow()
            
        except Exception as e:
            logger.error(f"Failed to open document manager: {e}", exc_info=True)
            self._show_error("문서 관리", f"오류: {str(e)}")
    
    def _open_rag_settings(self):
        """랜 설정 대화상자 열기"""
        try:
            from ui.dialogs import RAGSettingsDialog
            from PyQt6.QtWidgets import QDialog
            
            dialog = RAGSettingsDialog(self.main_window)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                settings = dialog.get_settings()
                logger.info(f"RAG settings updated: {settings}")
                
        except Exception as e:
            logger.error(f"Failed to open RAG settings: {e}")
            self._show_error("RAG 설정", f"오류: {str(e)}")
    
    def _test_rag_system(self):
        """랜 시스템 테스트"""
        from PyQt6.QtWidgets import QMessageBox
        
        try:
            from core.rag.rag_manager import RAGManager
            
            # RAG Manager 초기화
            if not hasattr(self.main_window, 'rag_manager'):
                self.main_window.rag_manager = RAGManager()
            
            manager = self.main_window.rag_manager
            
            if manager.is_available():
                msg = "✅ RAG 시스템이 정상적으로 동작합니다!\n\n"
                msg += f"💾 Vector Store: {manager.vectorstore.__class__.__name__}\n"
                msg += f"🧠 Embeddings: {manager.embeddings.__class__.__name__}"
            else:
                msg = "⚠️ RAG 시스템을 사용할 수 없습니다.\n\n"
                msg += "lancedb 또는 필요한 라이브러리를 설치해주세요."
            
            msg_box = QMessageBox(self.main_window)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("RAG 테스트")
            msg_box.setText(msg)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            self.main_window.theme_controller.apply_dialog_theme(msg_box)
            msg_box.exec()
            
        except Exception as e:
            logger.error(f"RAG test failed: {e}")
            self._show_error("RAG 테스트", f"오류: {str(e)}")
    
    def _show_error(self, title: str, message: str):
        """오류 메시지 표시"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self.main_window)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.main_window.theme_controller.apply_dialog_theme(msg_box)
        msg_box.exec()
    
    def _create_security_menu(self, menubar):
        """보안 메뉴 생성"""
        security_menu = menubar.addMenu('🔒 보안')
        
        # 보안 상태
        security_status_action = QAction('보안 상태', self.main_window)
        security_status_action.triggered.connect(self.main_window.dialog_manager.show_security_status)
        security_menu.addAction(security_status_action)
        
        security_menu.addSeparator()
        
        # 로그아웃
        logout_action = QAction('로그아웃', self.main_window)
        logout_action.triggered.connect(self._logout)
        security_menu.addAction(logout_action)
    
    def _clear_conversation_history(self):
        """대화 기록 초기화"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self.main_window)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle('대화 기록 초기화')
        msg_box.setText('모든 대화 기록을 삭제하시겠습니까?')
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.main_window.theme_controller.apply_dialog_theme(msg_box)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.main_window.chat_widget.clear_conversation_history()
    
    def _toggle_glassmorphism(self):
        """글래스모피즘 효과 토글"""
        new_state = theme_manager.material_manager.toggle_glassmorphism()
        self.main_window.glassmorphism_action.setChecked(new_state)
        
        if hasattr(self.main_window, 'chat_widget'):
            self.main_window.chat_widget.update_theme()
        
        logger.debug(f"글래스모피즘 {'ON' if new_state else 'OFF'}")
    
    def _logout(self):
        """로그아웃"""
        self.main_window.auth_manager.logout()
        
        if self.main_window.session_timer is not None:
            self.main_window.session_timer.stop()
        
        from PyQt6.QtWidgets import QMessageBox
        msg_box = QMessageBox(self.main_window)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("로그아웃")
        msg_box.setText("로그아웃되었습니다.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.main_window.theme_controller.apply_dialog_theme(msg_box)
        msg_box.exec()
        
        self.main_window._check_authentication()
    
    def _new_session(self):
        """새 세션 생성"""
        if hasattr(self.main_window, 'chat_widget'):
            self.main_window.chat_widget.create_new_session()
    
    def _show_about(self):
        """버전 정보 표시"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self.main_window)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("버전 정보")
        msg_box.setText(
            "<h2>Chat AI Agent</h2>"
            "<p><b>버전:</b> 1.0.0</p>"
            "<p><b>설명:</b> 다양한 MCP 서버와 연동하여 도구를 사용할 수 있는 AI 채팅 에이전트</p>"
            "<p><b>라이선스:</b> MIT License</p>"
            "<p><b>개발:</b> Chat AI Agent Development Team</p>"
        )
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.main_window.theme_controller.apply_dialog_theme(msg_box)
        msg_box.exec()
