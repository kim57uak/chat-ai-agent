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
        self._create_settings_menu(menubar)
        self._create_rag_menu(menubar)
        self._create_security_menu(menubar)
    
    def _create_settings_menu(self, menubar):
        """설정 메뉴 생성"""
        settings_menu = menubar.addMenu('설정')
        
        # Environment settings
        settings_action = QAction('환경설정', self.main_window)
        settings_action.triggered.connect(self.main_window.dialog_manager.open_settings)
        settings_menu.addAction(settings_action)
        
        # MCP actions
        mcp_action = QAction('MCP 확장 임포트', self.main_window)
        mcp_action.triggered.connect(self.main_window.dialog_manager.open_mcp)
        settings_menu.addAction(mcp_action)
        
        mcp_manager_action = QAction('MCP 서버 관리', self.main_window)
        mcp_manager_action.triggered.connect(self.main_window.dialog_manager.open_mcp_manager)
        settings_menu.addAction(mcp_manager_action)
        
        settings_menu.addSeparator()
        
        # Config path setting
        config_path_action = QAction('설정 파일 경로 설정', self.main_window)
        config_path_action.triggered.connect(self.main_window.dialog_manager.open_config_path_dialog)
        settings_menu.addAction(config_path_action)
        
        settings_menu.addSeparator()
        
        # History and prompt actions
        clear_history_action = QAction('대화 기록 초기화', self.main_window)
        clear_history_action.triggered.connect(self._clear_conversation_history)
        settings_menu.addAction(clear_history_action)
        
        user_prompt_action = QAction('유저 프롬프트 설정', self.main_window)
        user_prompt_action.triggered.connect(self.main_window.dialog_manager.open_user_prompt)
        settings_menu.addAction(user_prompt_action)
        
        settings_menu.addSeparator()
        
        # Session panel toggle (단축키 제거 - WebEngine 충돌 방지)
        self.main_window.session_panel_action = QAction('세션 패널 표시', self.main_window)
        self.main_window.session_panel_action.setCheckable(True)
        self.main_window.session_panel_action.setChecked(True)
        self.main_window.session_panel_action.triggered.connect(
            self.main_window.layout_manager.toggle_session_panel
        )
        settings_menu.addAction(self.main_window.session_panel_action)
        
        # Token usage toggle (단축키 제거 - WebEngine 충돌 방지)
        self.main_window.token_usage_action = QAction('토큰 사용량 표시', self.main_window)
        self.main_window.token_usage_action.setCheckable(True)
        self.main_window.token_usage_action.setChecked(True)
        self.main_window.token_usage_action.triggered.connect(
            self.main_window.layout_manager.toggle_token_display
        )
        settings_menu.addAction(self.main_window.token_usage_action)
        
        # Glassmorphism toggle (단축키 제거 - WebEngine 충돌 방지)
        self.main_window.glassmorphism_action = QAction('글래스모피즘 효과', self.main_window)
        self.main_window.glassmorphism_action.setCheckable(True)
        self.main_window.glassmorphism_action.setChecked(
            theme_manager.material_manager.is_glassmorphism_enabled()
        )
        self.main_window.glassmorphism_action.triggered.connect(self._toggle_glassmorphism)
        settings_menu.addAction(self.main_window.glassmorphism_action)
        
        settings_menu.addSeparator()
        
        # Splitter reset action
        reset_layout_action = QAction('레이아웃 초기화', self.main_window)
        reset_layout_action.triggered.connect(self.main_window.layout_manager.reset_layout)
        settings_menu.addAction(reset_layout_action)
    
    def _create_rag_menu(self, menubar):
        """랜 메뉴 생성"""
        rag_menu = menubar.addMenu('RAG')
        
        # 문서 관리
        doc_manager_action = QAction('📁 문서 관리', self.main_window)
        doc_manager_action.triggered.connect(self._open_document_manager)
        rag_menu.addAction(doc_manager_action)
        
        # RAG 설정
        rag_settings_action = QAction('⚙️ RAG 설정', self.main_window)
        rag_settings_action.triggered.connect(self._open_rag_settings)
        rag_menu.addAction(rag_settings_action)
        
        rag_menu.addSeparator()
        
        # 테스트
        test_rag_action = QAction('🧪 RAG 테스트', self.main_window)
        test_rag_action.triggered.connect(self._test_rag_system)
        rag_menu.addAction(test_rag_action)
    
    def _open_document_manager(self):
        """문서 관리 대화상자 열기"""
        try:
            from ui.dialogs import RAGDocumentManager
            
            # RAG Manager는 대화상자에서 lazy 초기화
            dialog = RAGDocumentManager(
                parent=self.main_window
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Failed to open document manager: {e}")
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
        security_menu = menubar.addMenu('보안')
        
        # 로그아웃
        logout_action = QAction('로그아웃', self.main_window)
        logout_action.triggered.connect(self._logout)
        security_menu.addAction(logout_action)
        
        # 보안 상태 표시
        security_status_action = QAction('보안 상태', self.main_window)
        security_status_action.triggered.connect(self.main_window.dialog_manager.show_security_status)
        security_menu.addAction(security_status_action)
    
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
