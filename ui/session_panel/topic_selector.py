"""
Topic Selector
RAG Topic 선택 팝업 메뉴
"""

from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import QPoint
from core.logging import get_logger

logger = get_logger("topic_selector")


class TopicSelector:
    """Topic 선택 팝업 메뉴"""
    
    _storage_cache = None
    
    def __init__(self, parent):
        self.parent = parent
    
    @classmethod
    def _get_storage(cls):
        """Storage 싱글톤 반환"""
        if cls._storage_cache is None:
            from core.rag.storage.rag_storage_manager import RAGStorageManager
            cls._storage_cache = RAGStorageManager(lazy_load_vector=True)
        return cls._storage_cache
    
    def show(self, button):
        """Topic 선택 메뉴 표시"""
        try:
            storage = self._get_storage()
            topics = storage.get_all_topics()
            selected_topic = storage.get_selected_topic()
            
            menu = QMenu(self.parent)
            
            if not topics:
                action = menu.addAction("📚 등록된 Topic 없음")
                action.setEnabled(False)
            else:
                # 선택 해제 옵션
                clear_action = menu.addAction("❌ 선택 해제")
                clear_action.triggered.connect(self._clear_selection)
                menu.addSeparator()
                
                # Topic 목록
                for topic in topics:
                    topic_name = topic['name']
                    doc_count = topic['document_count']
                    action = menu.addAction(f"📚 {topic_name} ({doc_count}개)")
                    action.setCheckable(True)
                    
                    if selected_topic and topic['id'] == selected_topic['id']:
                        action.setChecked(True)
                    
                    action.triggered.connect(
                        lambda checked, tid=topic['id'], tname=topic_name: self._select_topic(tid, tname)
                    )
            
            button_pos = button.mapToGlobal(QPoint(0, 0))
            menu.exec(QPoint(button_pos.x(), button_pos.y() + button.height()))
            
        except Exception as e:
            logger.error(f"Topic 메뉴 표시 실패: {e}")
    
    def _select_topic(self, topic_id, topic_name):
        """Topic 선택"""
        try:
            storage = self._get_storage()
            if storage.set_selected_topic(topic_id):
                # 버튼 텍스트 업데이트 및 스타일 재적용
                if hasattr(self.parent, 'topic_button'):
                    btn = self.parent.topic_button
                    display_name = topic_name if len(topic_name) <= 12 else topic_name[:9] + "..."
                    btn.setText(f"📚 {display_name}")
                    btn.setToolTip(f"현재 Topic: {topic_name}")
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
                logger.info(f"Topic 선택됨: {topic_name}")
        except Exception as e:
            logger.error(f"Topic 선택 실패: {e}")
    
    def _clear_selection(self):
        """선택 해제"""
        try:
            storage = self._get_storage()
            if storage.clear_selected_topic():
                # 버튼 텍스트 업데이트 및 스타일 재적용
                if hasattr(self.parent, 'topic_button'):
                    btn = self.parent.topic_button
                    btn.setText("📚 RAG TOPICS")
                    btn.setToolTip("RAG Topic을 선택하세요")
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
                logger.info("Topic 선택 해제됨")
        except Exception as e:
            logger.error(f"선택 해제 실패: {e}")
