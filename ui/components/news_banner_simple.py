"""
간단한 뉴스 롤링 배너 위젯 - QLabel 기반 (메모리 안정성)
"""

import json
import webbrowser
from core.logging import get_logger
import threading
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QCursor
from core.news.rss_parser import RSSParser

logger = get_logger("news_banner_simple")


class NewsLoader(QObject):
    """백그라운드 뉴스 로더"""

    news_ready = pyqtSignal(list)
    translation_updated = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.parser = RSSParser()
        self.running = False
        self.ai_client = None

    def load_news_async(self):
        """비동기 뉴스 로딩"""
        if self.running:
            return

        def load_in_thread():
            try:
                self.running = True
                from utils.config_path import config_path_manager
                config_path = config_path_manager.get_config_path('news_config.json')
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                all_news = []
                news_config = config.get("news_settings", {})

                # 국내 뉴스
                if news_config.get("show_domestic", True):
                    domestic_sources = config.get("news_sources", {}).get("domestic", [])
                    domestic_count = news_config.get("domestic_count", 3)
                    for source in domestic_sources:
                        if not source.get("enabled", True):
                            continue
                        try:
                            date_filter = config.get("date_filter", {})
                            news_days = date_filter.get("news_days", 0)
                            items = self.parser.parse_news_rss(source["url"], news_days)
                            for item in items[:domestic_count]:
                                item["category"] = "국내"
                                item["source_name"] = source["name"]
                                all_news.append(item)
                        except Exception as e:
                            logger.error(f"국내 뉴스 로딩 실패: {e}")

                # 해외 뉴스
                if news_config.get("show_international", True):
                    intl_sources = config.get("news_sources", {}).get("international", [])
                    international_count = news_config.get("international_count", 3)
                    intl_news_collected = []
                    for source in intl_sources:
                        if not source.get("enabled", True):
                            continue
                        try:
                            date_filter = config.get("date_filter", {})
                            news_days = date_filter.get("news_days", 0)
                            items = self.parser.parse_news_rss(source["url"], news_days)
                            for item in items:
                                item["category"] = "해외"
                                item["source_name"] = source["name"]
                                intl_news_collected.append(item)
                        except Exception as e:
                            logger.error(f"해외 뉴스 로딩 실패: {e}")

                    intl_news_collected.sort(key=lambda x: x.get("pubDate") or datetime.min, reverse=True)
                    for item in intl_news_collected[:international_count]:
                        item["translated_title"] = item["title"]
                        all_news.append(item)

                # 지진 정보
                if news_config.get("show_earthquake", True):
                    eq_sources = config.get("news_sources", {}).get("earthquake", [])
                    earthquake_count = news_config.get("earthquake_count", 2)
                    for source in eq_sources:
                        if not source.get("enabled", True):
                            continue
                        try:
                            date_filter = config.get("date_filter", {})
                            earthquake_days = date_filter.get("earthquake_days", 3)
                            items = self.parser.parse_earthquake_rss(source["url"], earthquake_days)
                            for item in items[:earthquake_count]:
                                item["category"] = "지진"
                                item["source_name"] = source["name"]
                                all_news.append(item)
                        except Exception as e:
                            logger.error(f"지진 정보 로딩 실패: {e}")

                logger.info(f"총 {len(all_news)}개 뉴스 로딩 완료")
                self.news_ready.emit(all_news)
                
                # 해외 뉴스 번역 시작 (메인 스레드에서)
                self._translate_news(all_news)

            except Exception as e:
                logger.error(f"뉴스 로딩 오류: {e}")
                self.news_ready.emit([])
            finally:
                self.running = False

        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()
    
    def _translate_news(self, news_items):
        """해외 뉴스 번역"""
        def translate_in_thread():
            try:
                intl_news = [(i, item) for i, item in enumerate(news_items) if item.get("category") == "해외"]
                if not intl_news:
                    return
                
                titles = [item["title"] for _, item in intl_news]
                translations = self._translate_batch(titles)
                
                if translations:
                    for (idx, _), translated in zip(intl_news, translations):
                        if translated:
                            self.translation_updated.emit(idx, translated)
                            logger.info(f"번역 완료 [{idx}]: {translated[:30]}...")
            except Exception as e:
                logger.error(f"번역 오류: {e}")
        
        thread = threading.Thread(target=translate_in_thread, daemon=True)
        thread.start()
    
    def _translate_batch(self, titles):
        """일괄 번역"""
        if not titles:
            return []
        
        try:
            from core.file_utils import load_config, load_last_model
            from core.ai_client import AIClient
            
            logger.info(f"번역 시작: {len(titles)}개 제목")
            
            current_model = load_last_model()
            config = load_config()
            models = config.get("models", {})
            
            if current_model and current_model in models:
                api_key = models[current_model].get("api_key")
                if api_key and api_key.strip():
                    self.ai_client = AIClient(api_key, current_model)
                    logger.info(f"번역 모델: {current_model}")
            
            if not self.ai_client:
                for model_name, model_config in models.items():
                    api_key = model_config.get("api_key")
                    if api_key and api_key.strip():
                        self.ai_client = AIClient(api_key, model_name)
                        logger.info(f"기본 모델: {model_name}")
                        break
            
            if not self.ai_client:
                logger.warning("AI 클라이언트 없음")
                return []
            
            numbered = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
            prompt = f"""Translate these news titles to Korean. Return ONLY the Korean translations in numbered format:\n\n{numbered}\n\nKorean translations:"""
            
            logger.info("번역 요청 전송")
            response = self.ai_client.simple_chat(prompt)
            logger.info(f"번역 응답 수신: {len(response)}자")
            
            import re
            # HTML 태그 제거
            response = re.sub(r"<[^>]+>", "", response).strip()
            
            translations = []
            lines = response.split("\n")
            
            for i in range(len(titles)):
                translated = None
                # 번호 패턴 찾기
                pattern = rf"^{i+1}\s*[.:]\s*(.+)$"
                for line in lines:
                    match = re.match(pattern, line)
                    if match:
                        translated = match.group(1).strip().strip('"').strip("'").strip("`")
                        break
                
                # 번호 패턴이 없으면 순서대로 처리
                if not translated and i < len(lines):
                    line = lines[i].strip()
                    # 번호 제거
                    translated = re.sub(r"^\d+\s*[.:]\s*", "", line).strip().strip('"').strip("'").strip("`")
                
                # 번역 검증
                if translated and translated != titles[i] and len(translated) >= 3 and any("가" <= c <= "힣" for c in translated):
                    translations.append(translated)
                    logger.info(f"번역 성공 [{i+1}]: {translated[:30]}...")
                else:
                    translations.append(None)
                    logger.warning(f"번역 실패 [{i+1}]: {titles[i][:30]}...")
            
            return translations
        except Exception as e:
            logger.error(f"번역 오류: {e}", exc_info=True)
            return []


class NewsBanner(QWidget):
    """단순 뉴스 배너 - QLabel 기반"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.news_items = []
        self.current_index = 0
        self.display_duration = 5000
        self.news_loader = NewsLoader()
        self.news_loader.news_ready.connect(self.on_news_loaded)
        self.news_loader.translation_updated.connect(self.on_translation_updated)
        self.setup_ui()
        QTimer.singleShot(1000, self.load_news)

    def setup_ui(self):
        """UI 설정"""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 뉴스 라벨
        self.news_label = QLabel("[뉴스] 로딩 중...")
        self.news_label.setWordWrap(False)
        self.news_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.news_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.news_label.mousePressEvent = self.on_label_clicked

        # 새로고침 버튼
        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setFixedSize(44, 44)
        self.refresh_btn.clicked.connect(self.load_news)
        self.refresh_btn.setToolTip("뉴스 새로고침")
        self.refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout.addWidget(self.news_label, 1)
        layout.addWidget(self.refresh_btn, 0)
        self.setLayout(layout)
        self.setMaximumHeight(60)
        self.setMinimumHeight(60)
        self.apply_theme()

    def load_news(self):
        """뉴스 로딩"""
        self.news_label.setText("[뉴스] 로딩 중...")
        self.news_loader.load_news_async()

    def on_news_loaded(self, news_items):
        """뉴스 로딩 완료"""
        self.news_items = news_items
        self.current_index = 0
        if self.news_items:
            self.update_display()
            self.start_rotation()
        else:
            self.news_label.setText("[뉴스] 뉴스를 가져올 수 없습니다")

    def update_display(self):
        """화면 업데이트"""
        if not self.news_items:
            return

        item = self.news_items[self.current_index]
        category = item.get("category", "")
        
        # 해외 뉴스는 번역된 제목 사용
        if category == "해외":
            translated = item.get("translated_title", "")
            original = item.get("title", "")
            title = translated if translated and translated != original else original
        else:
            title = item.get("title", "")
        
        title = title[:100]
        source_name = item.get("source_name", "")
        pub_date = item.get("pubDate")
        date_str = pub_date.strftime("%m/%d %H:%M") if pub_date else ""

        display_text = f"[{category}]"
        if source_name:
            display_text += f"[{source_name}]"
        display_text += f" {title}"
        if date_str:
            display_text += f" ({date_str})"

        self.news_label.setText(display_text)

    def start_rotation(self):
        """뉴스 순환 시작"""
        QTimer.singleShot(self.display_duration, self.next_news)

    def next_news(self):
        """다음 뉴스"""
        if self.news_items and len(self.news_items) > 1:
            self.current_index = (self.current_index + 1) % len(self.news_items)
            self.update_display()
            self.start_rotation()

    def on_label_clicked(self, event):
        """라벨 클릭 시 링크 열기"""
        if self.news_items and 0 <= self.current_index < len(self.news_items):
            url = self.news_items[self.current_index].get("link", "")
            if url:
                webbrowser.open(url)
                logger.info(f"뉴스 링크 열기: {url}")
    
    def on_translation_updated(self, index, translated_title):
        """번역 업데이트 수신"""
        if 0 <= index < len(self.news_items):
            self.news_items[index]["translated_title"] = translated_title
            if self.current_index == index:
                self.update_display()

    def apply_theme(self):
        """테마 적용"""
        try:
            from ui.styles.theme_manager import theme_manager
            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()
                bg_color = colors.get("surface", "#1e1e1e")
                text_color = colors.get("text_primary", "#ffffff")
                primary_color = colors.get("primary", "#bb86fc")

                self.news_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: 1px solid {primary_color};
                        border-radius: 8px;
                        padding: 8px 12px;
                        font-size: 14px;
                        font-weight: 500;
                        line-height: 1.5;
                    }}
                """)

                self.refresh_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {bg_color};
                        border: 1px solid {primary_color};
                        border-radius: 8px;
                        font-size: 20px;
                        font-weight: bold;
                        color: {primary_color};
                        padding: 0px;
                        min-width: 44px;
                        max-width: 44px;
                        min-height: 44px;
                        max-height: 44px;
                    }}
                    QPushButton:hover {{
                        background-color: {primary_color};
                        color: {bg_color};
                        border-color: {primary_color};
                    }}
                    QPushButton:pressed {{
                        background-color: {colors.get('primary_variant', primary_color)};
                        transform: scale(0.95);
                    }}
                """)
        except Exception as e:
            logger.error(f"테마 적용 오류: {e}")

    def update_theme(self):
        """테마 업데이트"""
        self.apply_theme()
    
    def cleanup(self):
        """리소스 정리"""
        try:
            if hasattr(self, 'news_loader'):
                self.news_loader.running = False
        except:
            pass
