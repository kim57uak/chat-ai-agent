"""
RAG Document Manager Dialog
RAG 문서 관리 대화상자
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QHeaderView, QLabel
)
from PyQt6.QtCore import Qt
from pathlib import Path
from collections import defaultdict
from core.logging import get_logger

logger = get_logger("rag_document_manager")


class RAGDocumentManager(QDialog):
    """RAG 문서 관리 대화상자"""
    
    def __init__(self, rag_manager=None, parent=None):
        super().__init__(parent)
        self.rag_manager = rag_manager
        self._setup_ui()
        # 문서 목록은 대화상자가 표시된 후 로드
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._load_documents_async)
    
    def _setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("RAG Document Manager")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 상단 버튼
        btn_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton("📁 Upload Document")
        self.upload_btn.clicked.connect(self._upload_document)
        btn_layout.addWidget(self.upload_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete Selected")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._load_documents_async)
        btn_layout.addWidget(self.refresh_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 문서 테이블
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Filename", "Type", "Chunks", "Upload Date"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        # 상태 레이블
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # 닫기 버튼
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    def _load_documents_async(self):
        """비동기로 문서 목록 로드"""
        # RAG Manager lazy 초기화
        if not self.rag_manager:
            try:
                from core.rag.rag_manager import RAGManager
                self.rag_manager = RAGManager()
            except Exception as e:
                logger.error(f"Failed to initialize RAG Manager: {e}")
                self.status_label.setText("RAG system initialization failed")
                return
        
        self._load_documents()
    
    def _load_documents(self):
        """문서 목록 로드"""
        self.table.setRowCount(0)
        
        if not self.rag_manager or not self.rag_manager.is_available():
            self.status_label.setText("RAG system not available")
            return
        
        try:
            vectorstore = self.rag_manager.vectorstore
            
            # 테이블 열기 시도 (이미 존재하는 경우)
            if vectorstore and not vectorstore.table:
                if vectorstore.db and vectorstore.table_name in vectorstore.db.table_names():
                    vectorstore.table = vectorstore.db.open_table(vectorstore.table_name)
                    logger.info(f"Opened existing table: {vectorstore.table_name}")
            
            if not vectorstore or not vectorstore.table:
                self.status_label.setText("No documents")
                return
            
            # LanceDB에서 문서 목록 가져오기
            df = vectorstore.table.to_pandas()
            
            # 파일별로 그룹화
            files = defaultdict(lambda: {"chunks": 0, "type": "", "date": ""})
            
            for _, row in df.iterrows():
                metadata = row.get('metadata', {})
                source = metadata.get('source', 'Unknown')
                filename = Path(source).name if source != 'Unknown' else 'Unknown'
                
                files[filename]["chunks"] += 1
                if not files[filename]["type"]:
                    files[filename]["type"] = Path(source).suffix if source != 'Unknown' else ''
                if not files[filename]["date"]:
                    files[filename]["date"] = metadata.get('upload_date', '')
            
            # 테이블에 추가
            self.table.setRowCount(len(files))
            for i, (filename, info) in enumerate(files.items()):
                self.table.setItem(i, 0, QTableWidgetItem(filename))
                self.table.setItem(i, 1, QTableWidgetItem(info["type"]))
                self.table.setItem(i, 2, QTableWidgetItem(str(info["chunks"])))
                self.table.setItem(i, 3, QTableWidgetItem(info["date"]))
            
            self.status_label.setText(f"{len(files)} documents loaded")
            
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def _upload_document(self):
        """문서 업로드"""
        # RAG Manager lazy 초기화
        if not self.rag_manager:
            try:
                from core.rag.rag_manager import RAGManager
                self.rag_manager = RAGManager()
            except Exception as e:
                logger.error(f"Failed to initialize RAG Manager: {e}")
                QMessageBox.warning(self, "Warning", "RAG system initialization failed")
                return
        
        if not self.rag_manager.is_available():
            QMessageBox.warning(self, "Warning", "RAG system not available")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "Documents (*.pdf *.docx *.txt *.csv *.xlsx);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            self.status_label.setText(f"Uploading: {file_path}")
            logger.info(f"Starting upload: {file_path}")
            
            # RAG Manager를 통해 문서 추가
            success = self.rag_manager.add_document(file_path)
            
            if success:
                self.status_label.setText("Upload completed")
                QMessageBox.information(self, "Success", "Document uploaded successfully")
                logger.info(f"Upload completed: {file_path}")
                self._load_documents()
            else:
                self.status_label.setText("Upload failed")
                QMessageBox.warning(self, "Warning", "Failed to upload document")
                logger.warning(f"Upload failed: {file_path}")
            
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Upload failed: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def _delete_selected(self):
        """선택된 문서 삭제"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No document selected")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete {len(selected_rows)} document(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if not self.rag_manager:
                    from core.rag.rag_manager import RAGManager
                    self.rag_manager = RAGManager()
                
                vectorstore = self.rag_manager.vectorstore
                if not vectorstore or not vectorstore.table:
                    QMessageBox.warning(self, "Warning", "No documents to delete")
                    return
                
                # 선택된 파일명 추출
                filenames = []
                for row in selected_rows:
                    filename = self.table.item(row.row(), 0).text()
                    filenames.append(filename)
                
                # 파일명으로 문서 ID 찾기
                df = vectorstore.table.to_pandas()
                doc_ids = []
                for _, row in df.iterrows():
                    metadata = row.get('metadata', {})
                    source = metadata.get('source', '')
                    if Path(source).name in filenames:
                        doc_ids.append(row.get('id'))
                
                if doc_ids:
                    vectorstore.delete(doc_ids)
                    self.status_label.setText(f"Deleted {len(filenames)} document(s)")
                    logger.info(f"Deleted {len(doc_ids)} chunks from {len(filenames)} files")
                else:
                    self.status_label.setText("No matching documents found")
                
                self._load_documents()
                
            except Exception as e:
                logger.error(f"Delete failed: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Delete failed: {str(e)}")
                self.status_label.setText(f"Error: {str(e)}")
