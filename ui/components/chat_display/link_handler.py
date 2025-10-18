"""
Link Handler
링크 클릭 및 클립보드 처리
"""

from PyQt6.QtCore import QObject, pyqtSlot, QUrl
from PyQt6.QtGui import QDesktopServices
from core.logging import get_logger

logger = get_logger("link_handler")


class LinkHandler(QObject):
    """링크 클릭 및 이미지 저장 처리를 위한 핸들러"""

    def __init__(self, chat_widget=None):
        super().__init__()
        self.chat_widget = chat_widget

    @pyqtSlot(str)
    def openUrl(self, url):
        """URL을 기본 브라우저에서 열기"""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            logger.debug(f"URL 열기 오류: {e}")

    @pyqtSlot(str)
    def copyToClipboard(self, text):
        """텍스트를 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication
            
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.clear()
                clipboard.setText(text)
                
                # 즉시 토스트 메시지 표시
                logger.debug(f"[COPY] chat_widget 존재: {hasattr(self, 'chat_widget')}")
                logger.debug(f"[COPY] chat_widget 값: {self.chat_widget}")
                if hasattr(self, 'chat_widget') and self.chat_widget:
                    logger.debug(f"[COPY] chat_display 존재: {hasattr(self.chat_widget, 'chat_display')}")
                    if hasattr(self.chat_widget, 'chat_display'):
                        logger.debug(f"[COPY] JavaScript 실행 시도")
                        toast_js = "showToast('텍스트가 복사되었습니다!', 'success');"
                        self.chat_widget.chat_display.web_view.page().runJavaScript(toast_js)
                    else:
                        logger.debug(f"[COPY] chat_display 없음")
                else:
                    logger.debug(f"[COPY] chat_widget 없음 또는 None")
                logger.debug(f"[COPY] 클립보드 복사 시도: {len(text)}자")
            else:
                logger.debug(f"[COPY] QApplication 인스턴스 없음")
                if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                    self.chat_widget.chat_display.web_view.page().runJavaScript(
                        "showToast('복사에 실패했습니다.');"
                    )
        except Exception as e:
            logger.debug(f"[COPY] 클립보드 복사 오류: {e}")
            if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                self.chat_widget.chat_display.web_view.page().runJavaScript(
                    "showToast('복사에 실패했습니다.');"
                )
            import traceback
            traceback.print_exc()
    
    @pyqtSlot(str)
    def copyHtmlToClipboard(self, html):
        """HTML을 클립보드에 복사"""
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QMimeData
            
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                clipboard.clear()
                
                mime_data = QMimeData()
                mime_data.setHtml(html)
                mime_data.setText(html)
                clipboard.setMimeData(mime_data)
                
                logger.debug(f"[COPY_HTML] chat_widget 존재: {hasattr(self, 'chat_widget')}")
                if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                    logger.debug(f"[COPY_HTML] JavaScript 실행 시도")
                    toast_js = "showToast('HTML이 복사되었습니다!', 'success');"
                    self.chat_widget.chat_display.web_view.page().runJavaScript(toast_js)
                else:
                    logger.debug(f"[COPY_HTML] chat_widget 또는 chat_display 없음")
                logger.debug(f"[COPY_HTML] HTML 클립보드 복사 시도: {len(html)}자")
            else:
                logger.debug(f"[COPY_HTML] QApplication 인스턴스 없음")
                if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                    self.chat_widget.chat_display.web_view.page().runJavaScript(
                        "showToast('HTML 복사에 실패했습니다.');"
                    )
        except Exception as e:
            logger.debug(f"[COPY_HTML] HTML 클립보드 복사 오류: {e}")
            if hasattr(self, 'chat_widget') and self.chat_widget and hasattr(self.chat_widget, 'chat_display'):
                self.chat_widget.chat_display.web_view.page().runJavaScript(
                    "showToast('HTML 복사에 실패했습니다.');"
                )
            import traceback
            traceback.print_exc()

    @pyqtSlot(str)
    def searchDictionary(self, word):
        """구글에서 단어 검색"""
        try:
            import urllib.parse
            
            encoded_word = urllib.parse.quote(word)
            url = f"https://www.google.com/search?q={encoded_word}+meaning"
            
            logger.debug(f"[사전검색] 단어: {word}, URL: {url}")
            QDesktopServices.openUrl(QUrl(url))
            
        except Exception as e:
            logger.debug(f"[사전검색] 오류: {e}")
    
    @pyqtSlot(str)
    def deleteMessage(self, message_id):
        """메시지 삭제"""
        try:
            logger.debug(f"[DELETE] 삭제 요청: {message_id}")

            # 먼저 DOM에서 제거 (즉시 시각적 피드백)
            if (
                hasattr(self, "chat_widget")
                and self.chat_widget
                and hasattr(self.chat_widget, "chat_display")
            ):
                self.chat_widget.chat_display.web_view.page().runJavaScript(
                    f"removeMessageFromDOM('{message_id}')"
                )
                logger.debug(f"[DELETE] DOM에서 제거 완료: {message_id}")

            # 데이터에서 삭제
            if self.chat_widget and hasattr(self.chat_widget, "delete_message"):
                success = self.chat_widget.delete_message(message_id)
                logger.debug(f"[DELETE] 데이터 삭제 결과: {success}")
            else:
                logger.debug(f"[DELETE] delete_message 메소드 없음")

        except Exception as e:
            logger.debug(f"[DELETE] 오류: {e}")
            import traceback
            traceback.print_exc()
    
    @pyqtSlot(str, str)
    def executeCode(self, code, language):
        """코드 실행"""
        try:
            logger.debug(f"[EXECUTE] 코드 실행 시작: {language}, {len(code)}문자")
            
            from ui.components.code_executor import CodeExecutor
            
            # 인스턴스 저장 (가비지 커렉션 방지)
            if not hasattr(self, '_executor'):
                self._executor = CodeExecutor()
                self._executor.execution_finished.connect(self._on_execution_finished)
            
            self._executor.executeCode(code, language)
            logger.debug(f"[EXECUTE] 코드 실행 요청 완료")
            
        except Exception as e:
            logger.error(f"[EXECUTE] 코드 실행 오류: {e}", exc_info=True)
            self._show_execution_result("", f"실행 오류: {str(e)}")
    
    def _on_execution_finished(self, output, error):
        """코드 실행 완료 처리"""
        logger.debug(f"[EXECUTE] 실행 완료 - 출력: {len(output)}문자, 오류: {len(error)}문자")
        self._show_execution_result(output, error)
    
    def _show_execution_result(self, output, error):
        """실행 결과 표시"""
        try:
            logger.debug(f"[EXECUTE] 결과 표시 시작")
            
            if hasattr(self, 'chat_widget') and self.chat_widget:
                result_text = ""
                if output:
                    result_text += f"**출력:**\n```\n{output}\n```\n"
                if error:
                    result_text += f"**오류:**\n```\n{error}\n```"
                
                if not result_text:
                    result_text = "실행 완료 (출력 없음)"
                
                logger.debug(f"[EXECUTE] 결과 텍스트: {result_text[:100]}...")
                
                # 채팅 위젪f에 결과 메시지 추가
                if hasattr(self.chat_widget, 'chat_display'):
                    from ui.components.chat_display.message_renderer import MessageRenderer
                    
                    # message_renderer 사용
                    if hasattr(self.chat_widget.chat_display, 'message_renderer'):
                        self.chat_widget.chat_display.message_renderer.append_message(
                            "시스템",
                            result_text,
                            progressive=False
                        )
                        logger.debug(f"[EXECUTE] 결과 메시지 추가 완료")
                    else:
                        logger.error(f"[EXECUTE] message_renderer 없음")
                else:
                    logger.error(f"[EXECUTE] chat_display 없음")
            else:
                logger.error(f"[EXECUTE] chat_widget 없음")
                
        except Exception as e:
            logger.error(f"[EXECUTE] 결과 표시 오류: {e}", exc_info=True)
