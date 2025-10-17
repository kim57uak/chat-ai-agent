"""
Theme Manager
테마 관리 전담
"""

from PyQt6.QtCore import QTimer
from core.logging import get_logger

logger = get_logger("chat_display_theme_manager")


class ThemeManager:
    """테마 관리"""
    
    def __init__(self, web_view):
        self.web_view = web_view
    
    def is_dark_theme(self) -> bool:
        """현재 테마가 다크 테마인지 확인"""
        from ui.styles.theme_manager import theme_manager

        if theme_manager.use_material_theme:
            return theme_manager.material_manager.is_dark_theme()
        else:
            return True  # 기본 테마는 다크 테마로 간주

    def update_theme(self):
        """테마 업데이트 - CSS 변수만 업데이트 (단순화)"""
        try:
            from ui.styles.theme_manager import theme_manager
            from ui.components.chat_theme_vars import generate_css_variables
            
            logger.debug(f"테마 업데이트 시작: {theme_manager.material_manager.current_theme_key}")

            # 현재 테마 색상 가져오기
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
            else:
                from ui.styles.flat_theme import FlatTheme
                colors = FlatTheme.get_theme_colors()
            
            # CSS 변수 생성
            is_dark = theme_manager.material_manager.is_dark_theme() if theme_manager.use_material_theme else True
            css_variables = generate_css_variables(colors, is_dark)

            # CSS 변수만 업데이트 (단일 레이어)
            update_js = f"""
            try {{
                var styleTag = document.getElementById('theme-style');
                if (styleTag) {{
                    var currentCSS = styleTag.innerHTML;
                    var newVariables = `{css_variables}`;
                    var updatedCSS = currentCSS.replace(/:root \\{{[^}}]*\\}}/s, newVariables);
                    styleTag.innerHTML = updatedCSS;
                    console.log('CSS 변수 업데이트 완료');
                }}
            }} catch(e) {{
                console.error('CSS 변수 업데이트 오류:', e);
            }}
            """
            self.web_view.page().runJavaScript(update_js)
            
            logger.debug("채팅 디스플레이 테마 업데이트 완료")

        except Exception as e:
            logger.debug(f"채팅 디스플레이 테마 업데이트 오류: {e}")
    
    def reload_with_backup(self, html_builder):
        """백업된 메시지와 함께 HTML 재로드"""
        try:
            # HTML 템플릿 재로드
            html_builder.load_html_template()
            
            # 200ms 후 메시지 복원
            QTimer.singleShot(200, self.restore_messages)
            
        except Exception as e:
            logger.debug(f"HTML 재로드 오류: {e}")
    
    def restore_messages(self):
        """백업된 메시지 복원"""
        restore_js = """
        try {
            if (window.messageBackup && window.messageBackup.length > 0) {
                var messagesDiv = document.getElementById('messages');
                if (messagesDiv) {
                    for (var i = 0; i < window.messageBackup.length; i++) {
                        var msgData = window.messageBackup[i];
                        var messageDiv = document.createElement('div');
                        messageDiv.id = msgData.id;
                        messageDiv.className = 'message';
                        messageDiv.innerHTML = msgData.innerHTML;
                        messagesDiv.appendChild(messageDiv);
                    }
                    console.log('메시지 복원 완료:', window.messageBackup.length);
                    // 스크롤을 맨 아래로
                    setTimeout(function() {
                        window.scrollTo(0, document.body.scrollHeight);
                    }, 50);
                }
            }
        } catch(e) {
            console.error('메시지 복원 오류:', e);
        }
        """
        
        self.web_view.page().runJavaScript(restore_js)
        logger.debug("채팅 디스플레이 테마 업데이트 완료")
