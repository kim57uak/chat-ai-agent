"""
간단한 뉴스 롤링 배너 위젯 - UI 락 방지
"""

import json
import logging
import threading
from datetime import datetime
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QUrl
from PyQt6.QtGui import QDesktopServices
from core.news.rss_parser import RSSParser

logger = logging.getLogger(__name__)


class NewsLoader(QObject):
    """백그라운드 뉴스 로더 - 비동기 번역"""

    news_ready = pyqtSignal(list)
    translation_updated = pyqtSignal(int, str)  # 인덱스, 번역된 제목

    def __init__(self):
        super().__init__()
        self.parser = RSSParser()
        self.running = False
        self.cached_news = []  # 캐시된 뉴스
        self.ai_client = None

    def load_news_async(self, force_translate=False):
        """비동기 뉴스 로딩"""
        if self.running:
            return

        # 캐시된 뉴스가 있고 번역 강제가 아니면 캐시 사용
        if self.cached_news and not force_translate:
            logger.info(f"캐시된 뉴스 사용: {len(self.cached_news)}개")

            # 캐시 내용 상세 로그
            intl_cached = [n for n in self.cached_news if n.get("category") == "해외"]
            logger.info(f"캐시된 해외 뉴스: {len(intl_cached)}개")
            for i, item in enumerate(intl_cached):
                original = item.get("title", "")[:20]
                translated = item.get("translated_title", "")[:20]
                logger.info(f"캐시 [{i}]: 원본='{original}...', 번역='{translated}...'")

            self.news_ready.emit(self.cached_news)
            # 백그라운드에서 번역 업데이트 시도
            self._translate_cached_news_async()
            return

        def load_in_thread():
            try:
                self.running = True
                with open("news_config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)

                all_news = []
                news_config = config.get("news_settings", {})

                # 국내 뉴스 (설정에 따라)
                if news_config.get("show_domestic", True):
                    domestic_sources = config.get("news_sources", {}).get(
                        "domestic", []
                    )
                    domestic_count = news_config.get("domestic_count", 3)
                    logger.info(
                        f"국내 뉴스 로딩: {len(domestic_sources)}개 소스, {domestic_count}개 수집"
                    )

                    for source in domestic_sources:
                        if not source.get("enabled", True):
                            continue
                        try:
                            # 날짜 필터링 설정 가져오기
                            date_filter = config.get("date_filter", {})
                            news_days = date_filter.get("news_days", 0)

                            items = self.parser.parse_news_rss(source["url"], news_days)
                            for item in items[:domestic_count]:
                                item["category"] = "국내"
                                item["source_name"] = source["name"]
                                all_news.append(item)
                        except Exception as e:
                            logger.error(f"국내 뉴스 로딩 실패 ({source['name']}): {e}")

                # 해외 뉴스 (설정에 따라) - AI 번역 포함
                if news_config.get("show_international", True):
                    intl_sources = config.get("news_sources", {}).get(
                        "international", []
                    )
                    international_count = news_config.get("international_count", 3)
                    logger.info(
                        f"해외 뉴스 로딩: {len(intl_sources)}개 소스, {international_count}개 수집"
                    )

                    intl_news_collected = []
                    for source in intl_sources:
                        if not source.get("enabled", True):
                            continue
                        try:
                            # 날짜 필터링 설정 가져오기
                            date_filter = config.get("date_filter", {})
                            news_days = date_filter.get("news_days", 0)

                            items = self.parser.parse_news_rss(source["url"], news_days)
                            for item in items:
                                item["category"] = "해외"
                                item["translated_title"] = item["title"]
                                item["source_name"] = source["name"]
                                logger.debug(
                                    f"해외 뉴스 원본 제목 설정: {item['title'][:30]}..."
                                )
                                intl_news_collected.append(item)
                        except Exception as e:
                            logger.error(f"해외 뉴스 처리 오류 ({source['name']}): {e}")

                    # 전체 해외 뉴스에서 최신 순으로 정렬 후 지정된 개수만 선택
                    intl_news_collected.sort(
                        key=lambda x: x.get("pubDate") or datetime.min, reverse=True
                    )
                    for item in intl_news_collected[:international_count]:
                        all_news.append(item)

                # 지진 정보 (설정에 따라)
                if news_config.get("show_earthquake", True):
                    eq_sources = config.get("news_sources", {}).get("earthquake", [])
                    earthquake_count = news_config.get("earthquake_count", 2)
                    logger.info(
                        f"지진 정보 로딩: {len(eq_sources)}개 소스, {earthquake_count}개 수집"
                    )

                    for source in eq_sources:
                        if not source.get("enabled", True):
                            continue
                        try:
                            # 날짜 필터링 설정 가져오기
                            date_filter = config.get("date_filter", {})
                            earthquake_days = date_filter.get("earthquake_days", 3)

                            items = self.parser.parse_earthquake_rss(
                                source["url"], earthquake_days
                            )
                            for item in items[:earthquake_count]:
                                item["category"] = "지진"
                                item["translated_title"] = item["title"]
                                item["source_name"] = source["name"]
                                all_news.append(item)
                        except Exception as e:
                            logger.error(f"지진 정보 처리 오류 ({source['name']}): {e}")

                # 캐시 업데이트 및 결과 전송
                logger.info(
                    f"총 {len(all_news)}개 뉴스 로딩 완료 (국내: {len([n for n in all_news if n.get('category') == '국내'])}, 해외: {len([n for n in all_news if n.get('category') == '해외'])}, 지진: {len([n for n in all_news if n.get('category') == '지진'])})"
                )

                # 캐시 업데이트 로그
                old_cache_size = len(self.cached_news)
                self.cached_news = all_news
                logger.info(
                    f"뉴스 캐시 업데이트: {old_cache_size}개 -> {len(self.cached_news)}개"
                )

                # 해외 뉴스 번역 상태 로그
                intl_news = [n for n in all_news if n.get("category") == "해외"]
                for i, item in enumerate(intl_news):
                    original = item.get("title", "")[:30]
                    translated = item.get("translated_title", "")[:30]
                    logger.info(
                        f"해외뉴스 {i+1}: 원본='{original}...', 번역='{translated}...'"
                    )

                self.news_ready.emit(all_news)

                # 번역 강제 모드일 때 로딩 완료 후 번역 시작
                if force_translate and all_news:
                    logger.info("로딩 완료 - 0.5초 후 번역 시작")
                    QTimer.singleShot(500, self._translate_cached_news_async)

            except Exception as e:
                logger.error(f"뉴스 로딩 오류: {e}")
                self.news_ready.emit([])
            finally:
                self.running = False

        # 데몬 스레드로 실행
        thread = threading.Thread(target=load_in_thread, daemon=True)
        thread.start()

        # 번역 강제 시 백그라운드 번역 시작 (로딩 완료 후)
        if force_translate:
            logger.info("번역 강제 모드 - 로딩 완료 후 번역 시작")

            # 로딩 완료 후 번역 시작되도록 수정
            def delayed_translate():
                if self.cached_news:  # 캐시가 있을 때만 번역
                    self._translate_cached_news_async()
                else:
                    logger.warning("캐시가 비어있어 번역 스킵")

            QTimer.singleShot(2000, delayed_translate)  # 2초로 연장

    def _translate_cached_news_async(self):
        """캐시된 뉴스의 백그라운드 번역 - 일괄 처리"""
        logger.info("백그라운드 번역 시작")

        def translate_in_background():
            try:
                # 번역 대상 수집
                intl_news = []
                for i, item in enumerate(self.cached_news):
                    if item.get("category") == "해외":
                        original_title = item.get("title", "")
                        translated_title = item.get("translated_title", "")
                        if (
                            translated_title == original_title
                            and original_title.strip()
                        ):
                            intl_news.append({"index": i, "title": original_title})

                if not intl_news:
                    logger.info("번역할 해외 뉴스가 없습니다.")
                    return

                logger.info(f"일괄 번역 대상: {len(intl_news)}개")

                # 일괄 번역 요청
                translations = self.translate_titles_batch(
                    [item["title"] for item in intl_news]
                )

                if translations and len(translations) == len(intl_news):
                    # 번역 결과 적용
                    for i, (news_item, translated) in enumerate(
                        zip(intl_news, translations)
                    ):
                        if translated and translated.strip():
                            cache_index = news_item["index"]
                            original = news_item["title"]

                            # 캐시 업데이트
                            self.cached_news[cache_index][
                                "translated_title"
                            ] = translated
                            logger.info(
                                f"캐시 업데이트 [{cache_index}]: '{original[:15]}...' -> '{translated[:15]}...'"
                            )

                            # UI 업데이트
                            self.translation_updated.emit(cache_index, translated)

                    logger.info(f"일괄 번역 완료: {len(translations)}개")
                else:
                    logger.error(
                        f"번역 결과 불일치: 요청={len(intl_news)}개, 응답={len(translations) if translations else 0}개"
                    )

            except Exception as e:
                logger.error(f"백그라운드 번역 오류: {e}")

        # 데몬 스레드로 백그라운드 번역 실행
        logger.info("번역 스레드 시작")
        thread = threading.Thread(target=translate_in_background, daemon=True)
        thread.start()

    def _get_ai_client(self):
        """사용자가 선택한 모델로 AI 클라이언트 생성"""
        try:
            from PyQt6.QtWidgets import QApplication
            from core.file_utils import load_config, load_last_model
            from core.ai_client import AIClient

            # 채팅창에서 선택된 모델 가져오기
            current_model = load_last_model()
            logger.info(f"채팅창 선택 모델: {current_model}")

            # 설정 로드
            config = load_config()
            models = config.get("models", {})

            # 선택된 모델이 있으면 해당 모델 사용
            if current_model and current_model in models:
                model_config = models[current_model]
                api_key = model_config.get("api_key")
                if api_key and api_key.strip():
                    logger.info(f"채팅창 선택 모델로 번역: {current_model}")
                    return AIClient(api_key, current_model)

            # 선택된 모델이 없으면 첫 번째 사용 가능한 모델 사용
            for model_name, model_config in models.items():
                api_key = model_config.get("api_key")
                if api_key and api_key.strip():
                    logger.info(f"기본 모델로 번역: {model_name}")
                    return AIClient(api_key, model_name)

            logger.warning("사용 가능한 AI 모델이 없습니다.")
            return None

        except Exception as e:
            logger.error(f"AI 클라이언트 생성 오류: {e}")
            return None

    def translate_titles_batch(self, titles):
        """제목 일괄 번역 - 사용자 선택 모델 사용"""
        if not titles:
            return []

        # AI 클라이언트 가져오기
        self.ai_client = self._get_ai_client()
        if not self.ai_client:
            logger.warning("AI 클라이언트를 찾을 수 없습니다.")
            return []

        try:
            # 일괄 번역 프롬프트 생성
            numbered_titles = []
            for i, title in enumerate(titles, 1):
                numbered_titles.append(f"{i}. {title}")

            titles_text = "\n".join(numbered_titles)

            prompt = f"""Translate these news titles to Korean. Return ONLY the Korean translations in the same numbered format, no explanations:

{titles_text}

Korean translations:"""

            response = self.ai_client.simple_chat(prompt)
            logger.info(f"일괄 번역 응답 수신: {len(response)}자")

            # 응답 파싱
            import re

            response = re.sub(r"<[^>]+>", "", response).strip()

            translations = []
            lines = response.split("\n")

            for i in range(len(titles)):
                translated = None
                # 번호로 시작하는 라인 찾기
                pattern = rf"^{i+1}\s*[.:]\s*(.+)$"
                for line in lines:
                    line = line.strip()
                    match = re.match(pattern, line)
                    if match:
                        translated = (
                            match.group(1).strip().strip('"').strip("'").strip("`")
                        )
                        break

                # 번호 패턴이 없으면 순서대로 처리
                if not translated and i < len(lines):
                    line = lines[i].strip()
                    # 번호 제거
                    translated = (
                        re.sub(r"^\d+\s*[.:]\s*", "", line)
                        .strip()
                        .strip('"')
                        .strip("'")
                        .strip("`")
                    )

                # 번역 검증
                if (
                    translated
                    and translated != titles[i]
                    and len(translated) >= 3
                    and any("가" <= c <= "힣" for c in translated)
                ):
                    translations.append(translated)
                    logger.debug(
                        f"번역 [{i+1}]: '{titles[i][:20]}...' -> '{translated[:20]}...'"
                    )
                else:
                    translations.append(None)
                    logger.warning(f"번역 실패 [{i+1}]: '{titles[i][:30]}...'")

            success_count = len([t for t in translations if t])
            logger.info(f"일괄 번역 결과: {success_count}/{len(titles)}개 성공")
            return translations

        except Exception as e:
            logger.error(f"일괄 번역 오류: {e}")
            return []


class NewsBanner(QWidget):
    """뉴스 배너 - UI 락 방지"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.news_items = []
        self.current_index = 0
        self.news_loader = NewsLoader()
        self.news_loader.news_ready.connect(self.on_news_loaded)
        self.news_loader.translation_updated.connect(self.on_translation_updated)
        self.setup_ui()
        self.setup_timer()
        # 3초 후 뉴스 로딩 시작 (번역 포함)
        QTimer.singleShot(3000, lambda: self.load_news_with_translation())

    def setup_ui(self):
        """UI 설정"""
        layout = QHBoxLayout()
        layout.setContentsMargins(3, 1, 3, 1)
        layout.setSpacing(3)

        # 웹뷰로 뉴스 표시 (이미지 지원)
        self.web_view = QWebEngineView()
        self.web_view.setFixedHeight(40)

        # 새로고침 버튼
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.clicked.connect(self.refresh_news)
        self.refresh_btn.setToolTip("뉴스 새로고침")

        layout.addWidget(self.web_view, 1)
        layout.addWidget(self.refresh_btn)
        self.setLayout(layout)
        self.setFixedHeight(44)

        self._init_web_view()
        self._setup_web_channel()
        self.apply_theme()

    def setup_timer(self):
        """롤링 타이머 설정"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_news)

        # 설정 파일에서 표시 시간 로드
        try:
            with open("news_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            display_duration = config.get("display_settings", {}).get(
                "display_duration", 8000
            )
        except:
            display_duration = 8000  # 기본값

        self.timer.start(display_duration)

    def load_news(self):
        """뉴스 로딩 - 비동기 (번역 없이)"""
        self._update_web_content("[뉴스] 로딩 중...", "", "")
        self.news_loader.load_news_async()

    def load_news_with_translation(self):
        """뉴스 로딩 - 번역 포함"""
        self._update_web_content("[뉴스] 로딩 및 번역 중...", "", "")
        self.news_loader.load_news_async(force_translate=True)

    def on_news_loaded(self, news_items):
        """뉴스 로딩 완료"""
        logger.info(f"뉴스 로딩 완룼: {len(news_items)}개")
        self.news_items = news_items
        self.current_index = 0
        if self.news_items:
            QTimer.singleShot(200, self.update_display)
        else:
            QTimer.singleShot(
                200,
                lambda: self._update_web_content(
                    "[뉴스] 뉴스를 가져올 수 없습니다", "", ""
                ),
            )

    def _init_web_view(self):
        """웹뷰 초기화"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <style>
                body {
                    margin: 0;
                    padding: 4px;
                    font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
                    font-size: 13px;
                    background: transparent;
                    overflow: hidden;
                }
                .news-container {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    height: 36px;
                    cursor: pointer;
                }
                .news-image {
                    width: 50px;
                    height: 34px;
                    object-fit: cover;
                    border-radius: 4px;
                    flex-shrink: 0;
                }
                .news-content {
                    flex: 1;
                    overflow: hidden;
                }
                .news-text {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    line-height: 1.4;
                }
            </style>
        </head>
        <body>
            <div id="news-display" class="news-container">
                <div class="news-content">
                    <div class="news-text">[뉴스] 뉴스 서비스 준비 중...</div>
                </div>
            </div>
            <script>
                var newsHandler = null;
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    newsHandler = channel.objects.newsHandler;
                });
                
                function openNewsLink(url) {
                    if (newsHandler && url) {
                        newsHandler.openUrl(url);
                    } else {
                        console.error('News handler not available or URL empty:', url);
                    }
                }
            </script>
        </body>
        </html>
        """
        self.web_view.setHtml(html_template)
        # 초기 테마 적용
        QTimer.singleShot(100, self.apply_theme)
    
    def _setup_web_channel(self):
        """웹채널 설정 - 링크 클릭 처리"""
        from PyQt6.QtWebChannel import QWebChannel
        from PyQt6.QtCore import QObject, pyqtSlot
        
        class NewsLinkHandler(QObject):
            @pyqtSlot(str)
            def openUrl(self, url):
                """URL을 기본 브라우저에서 열기"""
                try:
                    QDesktopServices.openUrl(QUrl(url))
                    logger.info(f"뉴스 링크 열기: {url}")
                except Exception as e:
                    logger.error(f"뉴스 링크 열기 오류: {e}")
        
        self.channel = QWebChannel()
        self.link_handler = NewsLinkHandler()
        self.channel.registerObject("newsHandler", self.link_handler)
        self.web_view.page().setWebChannel(self.channel)

    def update_display(self):
        """화면 업데이트"""
        if not self.news_items:
            return

        item = self.news_items[self.current_index]
        category = item.get("category", "")

        # 해외 뉴스 제목 처리
        if category == "해외":
            translated_title = item.get("translated_title", "")
            original_title = item.get("title", "")

            import re

            if translated_title:
                translated_title = re.sub(r"<[^>]+>", "", translated_title).strip()

            if (
                translated_title
                and translated_title != original_title
                and len(translated_title.strip()) > 0
            ):
                title = translated_title[:80]
            else:
                title = original_title[:80]
                logger.debug(f"해외뉴스 원본 표시: {title[:30]}...")
        else:
            title = item.get("title", "")[:80]

        # 빈 제목 방지
        if not title.strip():
            title = "제목 없음"

        # 발행일 포맷
        pub_date = item.get("pubDate")
        date_str = pub_date.strftime("%m/%d %H:%M") if pub_date else ""

        # 언론사명 가져오기
        source_name = item.get("source_name", item.get("source", ""))
        if not source_name:
            import re
            from urllib.parse import urlparse

            try:
                domain = urlparse(item.get("link", "")).netloc
                source_name = domain.replace("www.", "") if domain else ""
            except:
                source_name = ""

        # 이미지 URL 가져오기
        image_url = item.get("image_url", "")

        # 표시 텍스트 생성
        if source_name:
            if image_url:
                display_text = f"[{category}][{source_name}] {title}"
            else:
                display_text = f"[{category}][{source_name}] {title}"
        else:
            if image_url:
                display_text = f"[{category}] {title}"
            else:
                display_text = f"[{category}] {title}"

        if date_str:
            display_text += f" ({date_str})"

        # HTML 업데이트
        try:
            self._update_web_content(display_text, image_url, item.get("link", ""))
            logger.debug(f"뉴스 표시 업데이트: {display_text[:50]}...")
        except Exception as e:
            logger.error(f"뉴스 표시 업데이트 오류: {e}")

    def _update_web_content(self, text, image_url="", link=""):
        """웹 콘텐츠 업데이트"""
        try:
            # 이미지 HTML 생성
            image_html = ""
            if image_url and image_url.strip():
                image_html = f'<img src="{image_url}" class="news-image" alt="뉴스 이미지" onerror="this.style.display=\'none\'">'

            # 텍스트 이스케이프 처리
            safe_text = text.replace('"', "&quot;").replace("'", "&#39;")
            safe_link = (
                link.replace('"', "&quot;").replace("'", "&#39;") if link else ""
            )

            # JavaScript로 콘텐츠 업데이트
            js_code = f"""
            try {{
                const container = document.getElementById('news-display');
                if (container) {{
                    container.innerHTML = `
                        {image_html}
                        <div class="news-content">
                            <div class="news-text">{safe_text}</div>
                        </div>
                    `;
                    
                    if ('{safe_link}') {{
                        container.onclick = function() {{
                            openNewsLink('{safe_link}');
                        }};
                        container.style.cursor = 'pointer';
                    }} else {{
                        container.onclick = null;
                        container.style.cursor = 'default';
                    }}
                }}
            }} catch(e) {{
                console.error('뉴스 콘텐츠 업데이트 오류:', e);
            }}
            """

            self.web_view.page().runJavaScript(js_code)
            logger.debug(f"뉴스 콘텐츠 업데이트: {text[:30]}...")

        except Exception as e:
            logger.error(f"뉴스 콘텐츠 업데이트 오류: {e}")

    def next_news(self):
        """다음 뉴스로 이동"""
        if self.news_items and len(self.news_items) > 1:
            self.current_index = (self.current_index + 1) % len(self.news_items)
            self.update_display()

    def open_link(self, item):
        """링크 열기"""
        url = item.get("link", "")
        if url:
            QDesktopServices.openUrl(QUrl(url))

    def on_translation_updated(self, index, translated_title):
        """번역 업데이트 수신"""
        import re

        clean_title = re.sub(r"<[^>]+>", "", translated_title).strip()
        logger.info(f"번역 업데이트 수신: index={index}, title={clean_title[:30]}...")

        if 0 <= index < len(self.news_items):
            # 업데이트 전후 비교
            old_title = self.news_items[index].get("translated_title", "")
            self.news_items[index]["translated_title"] = clean_title
            logger.info(
                f"뉴스 아이템 [{index}] 업데이트: '{old_title[:20]}...' -> '{clean_title[:20]}...'"
            )

            # 업데이트 확인
            updated_title = self.news_items[index].get("translated_title", "")
            if updated_title == clean_title:
                logger.info(f"뉴스 아이템 [{index}] 업데이트 성공")
            else:
                logger.error(f"뉴스 아이템 [{index}] 업데이트 실패")

            if self.current_index == index:
                logger.info(f"현재 표시 중인 뉴스 업데이트, 화면 새로고침")
                self.update_display()
        else:
            logger.warning(
                f"잘못된 인덱스: {index}, 뉴스 아이템 개수: {len(self.news_items)}"
            )

    def refresh_news(self):
        """새로고침 - AI 번역 포함"""
        if not self.news_loader.running:
            self.load_news_with_translation()

    def apply_theme(self):
        """테마 적용"""
        try:
            from ui.styles.theme_manager import theme_manager

            if theme_manager.use_material_theme:
                colors = theme_manager.material_manager.get_theme_colors()

                bg_color = colors.get("surface", "#1e1e1e")
                text_color = colors.get("text_primary", "#ffffff")
                primary_color = colors.get("primary", "#bb86fc")
                secondary_color = colors.get("secondary", "#03dac6")

                # 웹뷰 테마 업데이트
                theme_js = f"""
                try {{
                    // 기존 스타일 제거
                    const existingStyle = document.getElementById('news-theme-style');
                    if (existingStyle) existingStyle.remove();
                    
                    const style = document.createElement('style');
                    style.id = 'news-theme-style';
                    style.textContent = `
                        body {{
                            background-color: {bg_color} !important;
                            color: {text_color} !important;
                        }}
                        .news-container {{
                            background-color: {bg_color} !important;
                            color: {text_color} !important;
                            border: 1px solid {colors.get('divider', '#333333')} !important;
                            border-radius: 6px !important;
                            padding: 4px 6px !important;
                        }}
                        .news-text {{
                            color: {text_color} !important;
                            font-size: 12px !important;
                        }}
                        .news-content {{
                            background-color: transparent !important;
                        }}
                    `;
                    document.head.appendChild(style);
                    
                    // 배경색 직접 적용
                    document.body.style.backgroundColor = '{bg_color}';
                    const container = document.getElementById('news-display');
                    if (container) {{
                        container.style.backgroundColor = '{bg_color}';
                        container.style.color = '{text_color}';
                    }}
                }} catch(e) {{
                    console.error('뉴스 배너 테마 업데이트 오류:', e);
                }}
                """
                self.web_view.page().runJavaScript(theme_js)

                self.refresh_btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        border: none;
                        background-color: {primary_color};
                        border-radius: 18px;
                        font-size: 14px;
                        color: {colors.get('on_primary', '#000000')};
                    }}
                    QPushButton:hover {{
                        background-color: {secondary_color};
                    }}
                    QPushButton:pressed {{
                        background-color: {colors.get('primary_variant', primary_color)};
                    }}
                """
                )

                self.setStyleSheet(
                    f"""
                    NewsBanner {{
                        background-color: {colors.get('background', '#121212')};
                        border-radius: 8px;
                    }}
                """
                )
        except Exception as e:
            logger.error(f"뉴스 배너 테마 적용 오류: {e}")
            self.refresh_btn.setStyleSheet(
                """
                QPushButton {
                    border: none;
                    background-color: #007bff;
                    border-radius: 18px;
                    font-size: 14px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """
            )

    def update_theme(self):
        """테마 업데이트"""
        self.apply_theme()
