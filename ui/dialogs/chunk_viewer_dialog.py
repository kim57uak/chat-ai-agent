"""
Chunk Viewer Dialog
RAG 문서의 청크를 보고 관리하는 대화상자
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QTextEdit, QLabel,
    QHeaderView, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt
from pathlib import Path
from core.logging import get_logger

logger = get_logger("chunk_viewer_dialog")


class ChunkViewerDialog(QDialog):
    """청크 뷰어 대화상자"""
    
    def __init__(self, rag_manager=None, document_name: str = None, parent=None):
        super().__init__(parent)
        self.rag_manager = rag_manager
        self.document_name = document_name
        self.current_chunks = []
        self._setup_ui()
        self._load_chunks()
    
    def _setup_ui(self):
        """UI 설정"""
        title = f"Chunk Viewer - {self.document_name}" if self.document_name else "Chunk Viewer"
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # 상단 정보
        info_label = QLabel(f"Document: {self.document_name or 'All Documents'}")
        layout.addWidget(info_label)
        
        # Splitter (테이블 + 미리보기)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 청크 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Document", "Content Preview", "Size", "Metadata"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.table)
        
        # 청크 미리보기
        preview_widget = self._create_preview_widget()
        splitter.addWidget(preview_widget)
        
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
        
        # 하단 버튼
        btn_layout = QHBoxLayout()
        
        self.delete_btn = QPushButton("🗑️ Delete Selected")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._load_chunks)
        btn_layout.addWidget(self.refresh_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # 상태 레이블
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def _create_preview_widget(self):
        """미리보기 위젯 생성"""
        from PyQt6.QtWidgets import QWidget, QVBoxLayout
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Chunk Preview:"))
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        self.metadata_text = QTextEdit()
        self.metadata_text.setReadOnly(True)
        self.metadata_text.setMaximumHeight(100)
        layout.addWidget(QLabel("Metadata:"))
        layout.addWidget(self.metadata_text)
        
        return widget
    
    def _load_chunks(self):
        """청크 목록 로드"""
        self.table.setRowCount(0)
        self.current_chunks = []
        
        # RAG Manager lazy 초기화
        if not self.rag_manager:
            try:
                from core.rag.rag_manager import RAGManager
                self.rag_manager = RAGManager()
            except Exception as e:
                logger.error(f"Failed to initialize RAG Manager: {e}")
                self.status_label.setText("RAG system initialization failed")
                return
        
        if not self.rag_manager.is_available():
            self.status_label.setText("RAG system not available")
            return
        
        try:
            vectorstore = self.rag_manager.vectorstore
            
            # 테이블 열기
            if vectorstore and not vectorstore.table:
                if vectorstore.db and vectorstore.table_name in vectorstore.db.table_names():
                    vectorstore.table = vectorstore.db.open_table(vectorstore.table_name)
            
            if not vectorstore or not vectorstore.table:
                self.status_label.setText("No chunks found")
                return
            
            # LanceDB에서 청크 가져오기
            df = vectorstore.table.to_pandas()
            
            # 문서별 필터링
            if self.document_name:
                df = df[df['metadata'].apply(
                    lambda m: Path(m.get('source', '')).name == self.document_name
                )]
            
            # 테이블에 추가
            self.table.setRowCount(len(df))
            for i, (_, row) in enumerate(df.iterrows()):
                metadata = row.get('metadata', {})
                text = row.get('text', '')
                doc_id = row.get('id', '')
                
                # 청크 저장
                self.current_chunks.append({
                    'id': doc_id,
                    'text': text,
                    'metadata': metadata
                })
                
                # 테이블 아이템
                self.table.setItem(i, 0, QTableWidgetItem(str(doc_id)[:20]))
                self.table.setItem(i, 1, QTableWidgetItem(Path(metadata.get('source', 'Unknown')).name))
                self.table.setItem(i, 2, QTableWidgetItem(text[:100] + "..."))
                self.table.setItem(i, 3, QTableWidgetItem(f"{len(text)} chars"))
                self.table.setItem(i, 4, QTableWidgetItem(str(metadata.get('upload_date', ''))))
            
            self.status_label.setText(f"{len(df)} chunks loaded")
            
        except Exception as e:
            logger.error(f"Failed to load chunks: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def _on_selection_changed(self):
        """선택 변경 시 미리보기 업데이트"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            self.preview_text.clear()
            self.metadata_text.clear()
            return
        
        row = selected_rows[0].row()
        if row < len(self.current_chunks):
            chunk = self.current_chunks[row]
            
            # 미리보기
            self.preview_text.setPlainText(chunk['text'])
            
            # 메타데이터
            metadata_str = "\n".join([f"{k}: {v}" for k, v in chunk['metadata'].items()])
            self.metadata_text.setPlainText(metadata_str)
    
    def _delete_selected(self):
        """선택된 청크 삭제"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No chunk selected")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected_rows)} chunk(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if not self.rag_manager:
                    from core.rag.rag_manager import RAGManager
                    self.rag_manager = RAGManager()
                
                vectorstore = self.rag_manager.vectorstore
                if not vectorstore or not vectorstore.table:
                    QMessageBox.warning(self, "Warning", "No chunks to delete")
                    return
                
                # 선택된 청크 ID 추출
                chunk_ids = []
                for row in selected_rows:
                    idx = row.row()
                    if idx < len(self.current_chunks):
                        chunk_ids.append(self.current_chunks[idx]['id'])
                
                if chunk_ids:
                    vectorstore.delete(chunk_ids)
                    self.status_label.setText(f"Deleted {len(chunk_ids)} chunk(s)")
                    logger.info(f"Deleted {len(chunk_ids)} chunks")
                    self._load_chunks()
                else:
                    self.status_label.setText("No chunks to delete")
                
            except Exception as e:
                logger.error(f"Delete failed: {e}")
                QMessageBox.critical(self, "Error", f"Delete failed: {str(e)}")
