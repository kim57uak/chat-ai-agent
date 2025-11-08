# RAG Document Topic Management System - 완전한 설계

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [아키텍처 구조](#아키텍처-구조)
3. [청킹 전략](#청킹-전략)
4. [배치 업로드](#배치-업로드)
5. [자동 Topic 분류](#자동-topic-분류)
6. [구현 가이드](#구현-가이드)

---

## 시스템 개요

### 핵심 기능
- **문서 관리**: 다양한 형식 지원 (PDF, Word, Excel, 코드 등)
- **청킹 전략**: Semantic, Document-Specific, Sliding Window
- **배치 업로드**: 단일/폴더 업로드, 진행 상황 추적
- **자동 Topic 분류**: LLM 기반 주제 추출 및 계층 구조
- **벡터 검색**: LanceDB + dragonkue-KoEn-E5-Tiny

### 기술 스택
- **Vector DB**: LanceDB (현재 사용 중)
- **Embedding**: dragonkue-KoEn-E5-Tiny (384차원)
- **청킹**: LangChain (이미 설치됨)
- **UI**: PyQt6 (독립 창)

---

## 아키텍처 구조

```
core/rag/
├── chunking/
│   ├── chunk_manager.py          # 현재 사용 중
│   ├── semantic_chunker.py       # LangChain SemanticChunker
│   ├── code_chunker.py           # 코드 전용
│   └── table_chunker.py          # 표 전용
│
├── batch/
│   ├── file_scanner.py           # 파일 스캔
│   ├── batch_processor.py        # 배치 처리
│   └── progress_tracker.py       # 진행 추적
│
├── topic/
│   ├── topic_classifier.py       # AI 주제 분류
│   ├── topic_manager.py          # CRUD
│   └── topic_matcher.py          # 유사도 매칭
│
├── embeddings/
│   └── korean_embeddings.py      # 현재 사용 중
│
└── vector_store/
    └── lancedb_store.py          # 현재 사용 중

ui/rag/
├── rag_management_window.py      # 메인 창 (독립, 글래스모피즘)
├── chunking_selector.py          # 청킹 전략 선택
├── batch_upload_dialog.py        # 배치 업로드
├── topic_tree_widget.py          # 주제 트리
├── document_list_widget.py       # 문서 목록
└── glass_style.py                # 글래스모피즘 스타일
```

### 데이터 저장 구조 (LanceDB + SQLite 조합)

#### 왜 두 개의 DB?

| 항목 | LanceDB | SQLite |
|------|---------|--------|
| **용도** | 벡터 검색 | 메타데이터 관리 |
| **저장** | 임베딩 벡터 + 최소 메타 | 문서/토픽 상세 정보 |
| **검색** | 유사도 검색 | 필터링, 정렬, 집계 |
| **예시** | "Python 관련 문서" | "기술 토픽의 문서 목록" |

**LanceDB 장점**: 벡터 검색 빠름, 메타데이터 필터링 가능  
**LanceDB 단점**: 집계 쿼리 약함, 통계 느림, 관리 어려움  
**SQLite 장점**: 빠른 집계, 쉬운 관리, UI 표시 용이  

#### SQLite 스키마

```sql
-- 토픽 테이블
CREATE TABLE topics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    description TEXT,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES topics(id)
);

-- 문서 테이블
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT,
    file_type TEXT,
    file_size INTEGER,
    chunk_count INTEGER DEFAULT 0,
    chunking_strategy TEXT,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- 청크 추적 테이블 (선택사항)
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER,
    lancedb_id TEXT,  -- LanceDB의 실제 ID
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

#### LanceDB 데이터

```python
# 청크 + 임베딩 + 메타데이터
{
    "id": "chunk_1",
    "text": "청크 내용...",
    "vector": [0.1, 0.2, ...],  # 384차원
    "metadata": {
        "source": "/path/to/file.pdf",  # 기존 (파일 경로)
        "document_id": "doc_456",       # 추가 (문서 추적용)
        "topic_id": "topic_123",        # 추가 (토픽 필터링용)
        "chunk_index": 0,                # 추가 (순서)
        "chunking_strategy": "semantic"  # 추가 (전략 기록)
    }
}
```

#### 데이터 흐름

```python
# 1. 문서 업로드
doc_id = sqlite.insert_document(filename, topic_id, file_path)

# 2. 청킹 & 임베딩
chunks = chunker.chunk(document)
for i, chunk in enumerate(chunks):
    chunk.metadata["document_id"] = doc_id
    chunk.metadata["topic_id"] = topic_id
    chunk.metadata["chunk_index"] = i

# 3. LanceDB 저장
lancedb_ids = lancedb.add_documents(chunks, embeddings=embeddings)

# 4. SQLite 업데이트
sqlite.update_document(doc_id, chunk_count=len(chunks))
sqlite.update_topic(topic_id, increment_count=1)

# 5. 검색 (토픽 필터)
results = lancedb.search(
    query="Python",
    filter={"topic_id": "topic_123"}  # 특정 토픽만
)

# 6. 문서 상세 정보 조회
doc_info = sqlite.get_document(results[0].metadata["document_id"])

# 7. 문서 삭제
lancedb.delete(filter={"document_id": doc_id})  # 모든 청크 삭제
sqlite.delete_document(doc_id)
sqlite.update_topic(topic_id, decrement_count=1)
```

---

## UI 설계 (글래스모피즘)

### 디자인 컨셉

**글래스모피즘 (Glassmorphism)**:
- 반투명 배경 + 블러 효과
- 부드러운 테두리 + 그림자
- theme.json 색상 자동 적용
- 현대적이고 직관적인 레이아웃

### 메인 창 레이아웃

```
┌──────────────────────────────────────────────────────────┐
│  📚 RAG Document Management                    [─][□][×] │
├──────────────┬────────────────────────┬──────────────────┤
│              │                        │                  │
│  Topic Tree  │   Document List        │  Preview         │
│  (30%)       │   (40%)                │  (30%)           │
│              │                        │                  │
│ 🔍 Search    │ 📄 Python_Guide.pdf    │ ┌──────────────┐ │
│ ─────────    │    • 15 chunks         │ │ Document     │ │
│              │    • Semantic          │ │ Preview      │ │
│ 📁 기술 (15) │    • 2024-01-15        │ │              │ │
│   └ AI (8)   │                        │ │ First 500    │ │
│   └ Web (7)  │ 📄 AI_Report.docx      │ │ characters   │ │
│              │    • 23 chunks         │ │ ...          │ │
│ 📁 비즈니스(9)│    • Sliding Window    │ │              │ │
│              │    • 2024-01-14        │ └──────────────┘ │
│ 📁 교육 (12) │                        │                  │
│              │ 📊 Data.xlsx           │  [View Chunks]   │
│              │    • 45 chunks         │  [Delete]        │
│              │    • Table             │                  │
│              │    • 2024-01-13        │                  │
│              │                        │                  │
├──────────────┴────────────────────────┴──────────────────┤
│  [📤 Upload Files] [📁 Upload Folder] [🔍 Search] [⚙️]   │
└──────────────────────────────────────────────────────────┘
```

### 글래스모피즘 스타일

```python
# ui/rag/glass_style.py

from typing import Dict

class GlassStyle:
    """글래스모피즘 스타일 생성기 (theme.json 기반)"""
    
    @staticmethod
    def get_style(theme_colors: Dict[str, str]) -> str:
        """
        Generate glassmorphism stylesheet
        
        Args:
            theme_colors: theme.json의 colors 딕셔너리
            
        Returns:
            QSS stylesheet
        """
        primary = theme_colors.get('primary', '#1976d2')
        background = theme_colors.get('background', '#ffffff')
        text = theme_colors.get('text_primary', '#212121')
        
        return f"""
        /* Main Window */
        QMainWindow {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {background},
                stop:1 {primary}
            );
        }}
        
        /* Glass Panels */
        QWidget#glassPanel {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
        }}
        
        /* Buttons */
        QPushButton {{
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 10px 20px;
            color: {text};
            font-weight: 500;
        }}
        
        QPushButton:hover {{
            background: rgba(255, 255, 255, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.4);
        }}
        
        QPushButton:pressed {{
            background: rgba(255, 255, 255, 0.35);
        }}
        
        /* Tree Widget */
        QTreeWidget {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 10px;
            color: {text};
        }}
        
        QTreeWidget::item {{
            padding: 8px;
            border-radius: 6px;
        }}
        
        QTreeWidget::item:hover {{
            background: rgba(255, 255, 255, 0.15);
        }}
        
        QTreeWidget::item:selected {{
            background: {primary};
            color: white;
        }}
        
        /* List Widget */
        QListWidget {{
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 10px;
        }}
        
        QListWidget::item {{
            padding: 12px;
            border-radius: 8px;
            margin: 4px;
        }}
        
        QListWidget::item:hover {{
            background: rgba(255, 255, 255, 0.15);
        }}
        
        QListWidget::item:selected {{
            background: {primary};
            color: white;
        }}
        
        /* Search Box */
        QLineEdit {{
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 20px;
            padding: 10px 15px;
            color: {text};
        }}
        
        QLineEdit:focus {{
            border: 2px solid {primary};
            background: rgba(255, 255, 255, 0.18);
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            text-align: center;
            color: {text};
        }}
        
        QProgressBar::chunk {{
            background: {primary};
            border-radius: 9px;
        }}
        """
```

### RAG Management Window

```python
# ui/rag/rag_management_window.py

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QPushButton, QLabel
)
from PyQt6.QtCore import Qt
from ui.rag.glass_style import GlassStyle
from ui.rag.topic_tree_widget import TopicTreeWidget
from ui.rag.document_list_widget import DocumentListWidget

class RAGManagementWindow(QMainWindow):
    """RAG 문서 관리 메인 창 (글래스모피즘)"""
    
    def __init__(self, theme_colors: dict):
        super().__init__()
        self.theme_colors = theme_colors
        self._setup_ui()
        self._apply_glass_style()
    
    def _setup_ui(self):
        """UI 초기화"""
        self.setWindowTitle("📚 RAG Document Management")
        self.setMinimumSize(1400, 800)
        
        # 중앙 위젯
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header = self._create_header()
        layout.addWidget(header)
        
        # 메인 스플리터 (3분할)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 좌측: Topic Tree (30%)
        self.topic_tree = TopicTreeWidget()
        self.topic_tree.setObjectName("glassPanel")
        splitter.addWidget(self.topic_tree)
        
        # 중앙: Document List (40%)
        self.document_list = DocumentListWidget()
        self.document_list.setObjectName("glassPanel")
        splitter.addWidget(self.document_list)
        
        # 우측: Preview (30%)
        self.preview = self._create_preview_panel()
        splitter.addWidget(self.preview)
        
        # 비율 설정
        splitter.setStretchFactor(0, 3)  # 30%
        splitter.setStretchFactor(1, 4)  # 40%
        splitter.setStretchFactor(2, 3)  # 30%
        
        layout.addWidget(splitter)
        
        # 하단 툴바
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
    
    def _create_header(self) -> QWidget:
        """헤더 생성"""
        header = QWidget()
        header.setObjectName("glassPanel")
        layout = QHBoxLayout(header)
        
        title = QLabel("📚 RAG Document Management")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding: 15px;
        """)
        layout.addWidget(title)
        layout.addStretch()
        
        return header
    
    def _create_preview_panel(self) -> QWidget:
        """미리보기 패널 생성"""
        panel = QWidget()
        panel.setObjectName("glassPanel")
        layout = QVBoxLayout(panel)
        
        label = QLabel("Document Preview")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)
        
        # 미리보기 영역
        preview_text = QLabel("Select a document to preview")
        preview_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        preview_text.setWordWrap(True)
        layout.addWidget(preview_text)
        
        # 버튼
        btn_layout = QHBoxLayout()
        view_chunks_btn = QPushButton("📄 View Chunks")
        delete_btn = QPushButton("🗑️ Delete")
        btn_layout.addWidget(view_chunks_btn)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)
        
        return panel
    
    def _create_toolbar(self) -> QWidget:
        """하단 툴바 생성"""
        toolbar = QWidget()
        toolbar.setObjectName("glassPanel")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # 버튼들
        upload_file_btn = QPushButton("📤 Upload Files")
        upload_folder_btn = QPushButton("📁 Upload Folder")
        search_btn = QPushButton("🔍 Search")
        settings_btn = QPushButton("⚙️ Settings")
        
        # 버튼 크기 설정
        for btn in [upload_file_btn, upload_folder_btn, search_btn, settings_btn]:
            btn.setMinimumHeight(45)
            btn.setMinimumWidth(150)
        
        layout.addWidget(upload_file_btn)
        layout.addWidget(upload_folder_btn)
        layout.addStretch()
        layout.addWidget(search_btn)
        layout.addWidget(settings_btn)
        
        return toolbar
    
    def _apply_glass_style(self):
        """글래스모피즘 스타일 적용"""
        style = GlassStyle.get_style(self.theme_colors)
        self.setStyleSheet(style)
```

### Topic Tree Widget

```python
# ui/rag/topic_tree_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QLineEdit
from PyQt6.QtCore import Qt

class TopicTreeWidget(QWidget):
    """토픽 트리 위젯"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 검색창
        search = QLineEdit()
        search.setPlaceholderText("🔍 Search topics...")
        layout.addWidget(search)
        
        # 트리
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Topics")
        self.tree.setIndentation(20)
        layout.addWidget(self.tree)
```

### Document List Widget

```python
# ui/rag/document_list_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, 
    QListWidgetItem, QLabel, QHBoxLayout
)

class DocumentListWidget(QWidget):
    """문서 목록 위젯"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 헤더
        header = QLabel("Documents")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # 리스트
        self.list = QListWidget()
        layout.addWidget(self.list)
    
    def add_document(self, filename: str, chunks: int, strategy: str, date: str):
        """문서 아이템 추가"""
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)
        
        # 파일명
        name_label = QLabel(f"📄 {filename}")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        item_layout.addWidget(name_label)
        
        # 정보
        info_label = QLabel(f"• {chunks} chunks  • {strategy}  • {date}")
        info_label.setStyleSheet("color: gray; font-size: 12px;")
        item_layout.addWidget(info_label)
        
        item = QListWidgetItem(self.list)
        item.setSizeHint(item_widget.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, item_widget)
```

### 사용성 개선 포인트

1. **직관적 아이콘**: 📚📄📁🔍⚙️ 등 이모지 활용
2. **3분할 레이아웃**: 토픽 → 문서 → 미리보기 (자연스러운 흐름)
3. **검색 우선**: 각 패널 상단에 검색창 배치
4. **큰 버튼**: 최소 45px 높이로 클릭 용이
5. **여백**: 15-20px 여백으로 답답하지 않게
6. **호버 효과**: 마우스 오버 시 시각적 피드백
7. **선택 강조**: 선택된 항목은 primary 색상으로 명확히 표시

---

## 청킹 전략

### ✅ 중요: 동일 컬렉션/토픽 내 다양한 전략 사용 가능!

**이유:**
- 벡터 검색은 청킹 방식과 무관 (임베딩 벡터만 비교)
- 메타데이터에 전략 기록 (`chunking_strategy` 필드)
- 임베딩 모델만 동일하면 OK (dragonkue-KoEn-E5-Tiny, 384차원)

### 1. Semantic Chunking (의미 기반)

**사용 라이브러리**: LangChain SemanticChunker (이미 설치됨!)

```python
from langchain_experimental.text_splitter import SemanticChunker
from core.rag.embeddings.korean_embeddings import KoreanEmbeddings

class SemanticChunkingStrategy:
    def __init__(self):
        self.embeddings = KoreanEmbeddings()
        self.splitter = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95
        )
    
    def chunk(self, document):
        chunks = self.splitter.split_documents([document])
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunking_strategy"] = "semantic"
            chunk.metadata["chunk_index"] = i
        return chunks
```

**최적 사용:**
- ✅ 기술 문서, 논문, 보고서
- ✅ 복잡한 주제 전환
- ❌ 짧은 문서 (< 1000자)

**풍선 도움말:**
```
의미 기반 청킹 (Semantic Chunking)

📖 추천: 기술 문서, 논문, 긴 보고서
⚡ 속도: 느림 (임베딩 계산)
🎯 품질: 최고 (의미 단위 보존)

장점:
• 문맥이 끊기지 않음
• 검색 정확도 향상

단점:
• 처리 시간 오래 걸림
```

### 2. Document-Specific Chunking (문서 타입별)

**사용 라이브러리**: LangChain Language Splitters

#### A. 코드 청킹
```python
from langchain.text_splitter import (
    PythonCodeTextSplitter,
    Language,
    RecursiveCharacterTextSplitter
)

class CodeChunkingStrategy:
    LANGUAGE_MAP = {
        ".py": Language.PYTHON,
        ".js": Language.JS,
        ".ts": Language.TS,
        ".java": Language.JAVA,
        ".cpp": Language.CPP,
        ".c": Language.CPP,
        ".cc": Language.CPP,
        ".cxx": Language.CPP,
        ".hpp": Language.CPP,
        ".h": Language.CPP,
        ".cs": Language.CSHARP,
        ".go": Language.GO,
        ".kt": Language.KOTLIN,
        ".php": Language.PHP,
        ".proto": Language.PROTO,
        ".rb": Language.RUBY,
        ".rs": Language.RUST,
        ".scala": Language.SCALA,
        ".swift": Language.SWIFT,
        ".md": Language.MARKDOWN,
        ".tex": Language.LATEX,
        ".html": Language.HTML,
        ".sol": Language.SOL,
        ".cob": Language.COBOL,
    }
    
    def chunk(self, document):
        ext = document.metadata.get("source", "").split(".")[-1]
        ext = f".{ext}"
        
        if ext == ".py":
            splitter = PythonCodeTextSplitter(chunk_size=500)
        elif ext in self.LANGUAGE_MAP:
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=self.LANGUAGE_MAP[ext],
                chunk_size=500
            )
        else:
            splitter = RecursiveCharacterTextSplitter(chunk_size=500)
        
        chunks = splitter.split_documents([document])
        for chunk in chunks:
            chunk.metadata["chunking_strategy"] = "code"
        return chunks
```

#### B. 마크다운 청킹
```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

class MarkdownChunkingStrategy:
    def __init__(self):
        self.headers = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers
        )
    
    def chunk(self, document):
        chunks = self.splitter.split_text(document.page_content)
        for chunk in chunks:
            chunk.metadata["chunking_strategy"] = "markdown"
        return chunks
```

#### C. 표 청킹 (직접 구현 - 간단)
```python
class TableChunkingStrategy:
    def __init__(self, rows_per_chunk=10):
        self.rows_per_chunk = rows_per_chunk
    
    def chunk(self, document):
        lines = document.page_content.split("\n")
        header = lines[0] if lines else ""
        
        chunks = []
        for i in range(1, len(lines), self.rows_per_chunk):
            chunk_lines = [header] + lines[i:i+self.rows_per_chunk]
            chunk_text = "\n".join(chunk_lines)
            
            chunk_doc = Document(
                page_content=chunk_text,
                metadata={
                    **document.metadata,
                    "chunking_strategy": "table",
                    "rows": f"{i}-{i+len(chunk_lines)-1}"
                }
            )
            chunks.append(chunk_doc)
        
        return chunks
```

**최적 사용:**
- ✅ Excel/CSV 표
- ✅ 소스 코드
- ✅ 마크다운
- ❌ 일반 텍스트

**풍선 도움말:**
```
문서 타입별 청킹 (Document-Specific)

📊 추천: 표 데이터, 소스 코드
⚡ 속도: 빠름
🎯 품질: 높음 (구조 보존)

타입별 전략:
• Excel/CSV: 행 단위 (10행씩)
• 소스 코드: 함수/클래스 단위
• 마크다운: 헤딩 기준

장점:
• 데이터 무결성 보장
• 구조 정보 보존
```

### 3. Sliding Window Chunking (슬라이딩 윈도우)

**사용 라이브러리**: LangChain RecursiveCharacterTextSplitter (현재 사용 중!)

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

class SlidingWindowChunkingStrategy:
    def __init__(self, window_size=500, overlap_ratio=0.2):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=window_size,
            chunk_overlap=int(window_size * overlap_ratio),
            separators=["\n\n", "\n", ". ", "。", " ", ""]
        )
    
    def chunk(self, document):
        chunks = self.splitter.split_documents([document])
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunking_strategy"] = "sliding_window"
            chunk.metadata["chunk_index"] = i
        return chunks
```

**최적 사용:**
- ✅ 일반 텍스트
- ✅ 짧은 문서
- ❌ 매우 긴 문서 (저장 공간)

**풍선 도움말:**
```
슬라이딩 윈도우 청킹 (Sliding Window)

📄 추천: 일반 텍스트, 짧은 문서
⚡ 속도: 빠름
🎯 품질: 중간

설정:
• 윈도우 크기: 500자
• 오버랩: 20% (100자)

장점:
• 경계 문제 완화
• 검색 누락 감소
```

### UI: 청킹 전략 선택기

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QRadioButton, QPushButton

class ChunkingStrategySelector(QWidget):
    TOOLTIPS = {
        "semantic": """<b>의미 기반 청킹</b><br>
📖 추천: 기술 문서, 논문<br>
⚡ 속도: 느림<br>
🎯 품질: 최고""",
        
        "document_specific": """<b>문서 타입별 청킹</b><br>
📊 추천: 표, 코드<br>
⚡ 속도: 빠름<br>
🎯 품질: 높음""",
        
        "sliding_window": """<b>슬라이딩 윈도우</b><br>
📄 추천: 일반 텍스트<br>
⚡ 속도: 빠름<br>
🎯 품질: 중간"""
    }
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.semantic_radio = QRadioButton("의미 기반 (Semantic)")
        self.document_radio = QRadioButton("문서 타입별 (Document-Specific)")
        self.sliding_radio = QRadioButton("슬라이딩 윈도우 (Sliding Window)")
        
        # 기본 선택
        self.sliding_radio.setChecked(True)
        
        # 도움말 버튼 추가
        for radio, strategy in [
            (self.semantic_radio, "semantic"),
            (self.document_radio, "document_specific"),
            (self.sliding_radio, "sliding_window")
        ]:
            help_btn = QPushButton("?")
            help_btn.setToolTip(self.TOOLTIPS[strategy])
            # 레이아웃에 추가...
```

---

## 배치 업로드

### 1. File Scanner

```python
from pathlib import Path
from typing import List

class FileScanner:
    SUPPORTED_EXTENSIONS = {
        # 텍스트
        ".txt", ".md", ".rst", ".log",
        # 문서
        ".pdf", ".docx", ".doc", ".odt",
        # 스프레드시트
        ".xlsx", ".xls", ".csv", ".ods",
        # 프레젠테이션
        ".pptx", ".ppt", ".odp",
        # 코드 (LANGUAGE_MAP 모두 포함)
        ".py", ".js", ".ts", ".java", ".cpp", ".c", ".cc", ".cxx", ".h", ".hpp",
        ".cs", ".go", ".kt", ".php", ".proto", ".rb", ".rs", ".scala", ".swift",
        ".sol", ".cob", ".tex",
        # 기타 코드
        ".r", ".m", ".lua",
        # 웹
        ".html", ".htm", ".xml", ".css", ".scss", ".sass",
        # 데이터
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        # 마크업
        ".rtf",
        # 기타
        ".sql", ".sh", ".bat", ".ps1"
    }
    
    def __init__(self, max_file_size_mb=50):
        self.max_file_size = max_file_size_mb * 1024 * 1024
    
    def scan_directory(self, directory: Path, recursive=True) -> List[Path]:
        files = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue
            
            # 확장자 체크
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            
            # 크기 체크
            if file_path.stat().st_size > self.max_file_size:
                continue
            
            # 제외 패턴 (node_modules, .git 등)
            if self._should_exclude(file_path):
                continue
            
            files.append(file_path)
        
        return files
```

### 2. Batch Processor

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

class BatchProcessor:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
    
    def process_batch(self, file_paths, on_progress=None):
        results = {"success": 0, "failed": 0, "topics": {}}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_file, path): path
                for path in file_paths
            }
            
            for i, future in enumerate(as_completed(futures), 1):
                try:
                    result = future.result()
                    results["success"] += 1
                    
                    if on_progress:
                        on_progress(i, len(file_paths), result["file"])
                except Exception as e:
                    results["failed"] += 1
        
        return results
    
    def _process_file(self, file_path):
        # 1. 로드
        # 2. 청킹
        # 3. 임베딩
        # 4. 저장
        pass
```

### 3. UI: Batch Upload Dialog (글래스모피즘)

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QProgressBar, QPushButton, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal

class BatchUploadDialog(QDialog):
    """배치 업로드 다이얼로그 (진행 상황 실시간 표시)"""
    
    upload_complete = pyqtSignal(dict)
    
    def __init__(self, theme_colors: dict):
        super().__init__()
        self.theme_colors = theme_colors
        self.setWindowTitle("📤 Batch Document Upload")
        self.setMinimumSize(900, 700)
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 헤더
        header = QLabel("📤 Batch Upload")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)
        
        # 파일 선택 버튼
        btn_layout = QHBoxLayout()
        self.add_files_btn = QPushButton("📄 Add Files")
        self.add_folder_btn = QPushButton("📁 Add Folder")
        self.clear_btn = QPushButton("🗑️ Clear All")
        
        for btn in [self.add_files_btn, self.add_folder_btn, self.clear_btn]:
            btn.setMinimumHeight(40)
        
        btn_layout.addWidget(self.add_files_btn)
        btn_layout.addWidget(self.add_folder_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        
        # 파일 목록
        list_label = QLabel("📂 Selected Files")
        list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(list_label)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(200)
        layout.addWidget(self.file_list)
        
        # 진행 상황 패널
        progress_panel = self._create_progress_panel()
        layout.addWidget(progress_panel)
        
        # 로그 영역
        log_label = QLabel("📝 Processing Log")
        log_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # 하단 버튼
        bottom_layout = QHBoxLayout()
        self.upload_btn = QPushButton("▶️ Start Upload")
        self.cancel_btn = QPushButton("❌ Cancel")
        
        self.upload_btn.setMinimumHeight(45)
        self.cancel_btn.setMinimumHeight(45)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        
        bottom_layout.addWidget(self.upload_btn)
        bottom_layout.addWidget(self.cancel_btn)
        layout.addLayout(bottom_layout)
    
    def _create_progress_panel(self) -> QWidget:
        """진행 상황 패널 생성"""
        panel = QWidget()
        panel.setObjectName("progressPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 제목
        title = QLabel("📈 Upload Progress")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 전체 진행률
        self.overall_label = QLabel("Ready to upload")
        layout.addWidget(self.overall_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimumHeight(30)
        self.overall_progress.setTextVisible(True)
        layout.addWidget(self.overall_progress)
        
        # 통계 정보
        stats_layout = QHBoxLayout()
        
        # 성공
        success_widget = self._create_stat_widget(
            "✅ Success", "0", "#4CAF50"
        )
        stats_layout.addWidget(success_widget)
        
        # 실패
        failed_widget = self._create_stat_widget(
            "❌ Failed", "0", "#f44336"
        )
        stats_layout.addWidget(failed_widget)
        
        # 남은 시간
        time_widget = self._create_stat_widget(
            "⏱️ Remaining", "--:--", "#2196F3"
        )
        stats_layout.addWidget(time_widget)
        
        layout.addLayout(stats_layout)
        
        # 현재 처리 중인 파일
        self.current_file_label = QLabel("📄 Current: None")
        self.current_file_label.setStyleSheet("""
            padding: 10px;
            background: rgba(33, 150, 243, 0.1);
            border-radius: 5px;
            margin-top: 10px;
        """)
        layout.addWidget(self.current_file_label)
        
        return panel
    
    def _create_stat_widget(self, label: str, value: str, color: str) -> QWidget:
        """통계 위젯 생성"""
        widget = QWidget()
        widget.setStyleSheet(f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-size: 12px; color: gray;")
        label_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label_widget)
        
        value_widget = QLabel(value)
        value_widget.setObjectName("statValue")
        value_widget.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {color};
        """)
        value_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_widget)
        
        return widget
    
    def update_progress(self, current: int, total: int, file_name: str):
        """진행 상황 업데이트"""
        # 전체 진행률
        self.overall_progress.setMaximum(total)
        self.overall_progress.setValue(current)
        
        percent = (current / total * 100) if total > 0 else 0
        self.overall_label.setText(
            f"Processing: {current}/{total} files ({percent:.1f}%)"
        )
        
        # 현재 파일
        self.current_file_label.setText(f"📄 Current: {file_name}")
        
        # 로그 추가
        self.log_text.append(f"[{current}/{total}] Processing: {file_name}")
    
    def update_stats(self, success: int, failed: int, remaining_time: str):
        """통계 업데이트"""
        # 통계 위젯 찾기
        stats_widgets = self.findChildren(QLabel, "statValue")
        if len(stats_widgets) >= 3:
            stats_widgets[0].setText(str(success))
            stats_widgets[1].setText(str(failed))
            stats_widgets[2].setText(remaining_time)
    
    def _apply_style(self):
        """글래스모피즘 스타일 적용"""
        from ui.rag.glass_style import GlassStyle
        style = GlassStyle.get_style(self.theme_colors)
        self.setStyleSheet(style)
```

**주요 기능**:
1. **실시간 진행률**: 프로그레스 바 + 퍼센트 표시
2. **통계 카드**: 성공/실패/남은시간 한눈에
3. **현재 파일**: 지금 처리 중인 파일 표시
4. **로그**: 전체 처리 내역 기록
5. **색상 코드**: 성공(초록), 실패(빨강), 정보(파랑)

---

## Topic 관리 (수동 생성)

### Topic Manager (SQLite)

```python
class TopicManager:
    def __init__(self, database):
        self.db = database
        self._init_db()
    
    def _init_db(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                parent_id TEXT,
                document_count INTEGER DEFAULT 0
            )
        """)
    
    def create_topic(self, name, parent_id=None):
        topic_id = hashlib.md5(name.encode()).hexdigest()[:16]
        self.db.execute("""
            INSERT INTO topics (id, name, parent_id)
            VALUES (?, ?, ?)
        """, (topic_id, name, parent_id))
        return topic_id
    
    def get_all_topics(self):
        rows = self.db.execute("SELECT name FROM topics").fetchall()
        return [row[0] for row in rows]
```

---

## 임베딩 모델 관리

### 지원 모델

```python
class EmbeddingType:
    LOCAL = "local"          # 내장형 (dragonkue-KoEn-E5-Tiny)
    OPENAI = "openai"        # OpenAI (text-embedding-3-small/large)
    GOOGLE = "google"        # Google (embedding-001)
    COHERE = "cohere"        # Cohere (embed-multilingual-v3.0)
```

### 임베딩 전략 (Strategy 패턴)

```python
# core/rag/embeddings/embedding_factory.py

from abc import ABC, abstractmethod
from typing import List
from core.logging import get_logger

logger = get_logger("embedding_factory")

class BaseEmbeddingStrategy(ABC):
    """임베딩 전략 인터페이스"""
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        pass

class LocalEmbeddingStrategy(BaseEmbeddingStrategy):
    """내장형 임베딩 (dragonkue-KoEn-E5-Tiny)"""
    
    def __init__(self):
        from core.rag.embeddings.korean_embeddings import KoreanEmbeddings
        self.embeddings = KoreanEmbeddings()
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)
    
    def get_dimension(self) -> int:
        return 384

class OpenAIEmbeddingStrategy(BaseEmbeddingStrategy):
    """OpenAI 임베딩 (외장형)"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        from langchain_openai import OpenAIEmbeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=api_key,
            model=model
        )
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)
    
    def get_dimension(self) -> int:
        return 1536 if "small" in self.model else 3072

class GoogleEmbeddingStrategy(BaseEmbeddingStrategy):
    """Google 임베딩 (외장형)"""
    
    def __init__(self, api_key: str):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            google_api_key=api_key,
            model="models/embedding-001"
        )
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)
    
    def get_dimension(self) -> int:
        return 768

class EmbeddingFactory:
    """임베딩 전략 팩토리"""
    
    @staticmethod
    def create(embedding_type: str, **kwargs) -> BaseEmbeddingStrategy:
        if embedding_type == "local":
            return LocalEmbeddingStrategy()
        elif embedding_type == "openai":
            return OpenAIEmbeddingStrategy(
                api_key=kwargs.get("api_key"),
                model=kwargs.get("model", "text-embedding-3-small")
            )
        elif embedding_type == "google":
            return GoogleEmbeddingStrategy(
                api_key=kwargs.get("api_key")
            )
        else:
            logger.warning(f"Unknown embedding type: {embedding_type}, using local")
            return LocalEmbeddingStrategy()
```

### 설정 관리

```python
# core/rag/config/embedding_config.py

import json
from pathlib import Path
from typing import Dict, Optional

class EmbeddingConfigManager:
    """임베딩 설정 관리자"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        return {
            "embedding": {
                "type": "local",
                "model": "dragonkue-KoEn-E5-Tiny",
                "dimension": 384
            }
        }
    
    def get_embedding_type(self) -> str:
        return self.config["embedding"]["type"]
    
    def get_embedding_config(self) -> Dict:
        return self.config["embedding"]
    
    def update_embedding(self, embedding_type: str, **kwargs):
        """임베딩 설정 업데이트"""
        self.config["embedding"]["type"] = embedding_type
        self.config["embedding"].update(kwargs)
        self._save_config()
    
    def _save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
```

### UI: 임베딩 설정 다이얼로그

```python
# ui/rag/embedding_settings_dialog.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QGroupBox
)
from PyQt6.QtCore import pyqtSignal

class EmbeddingSettingsDialog(QDialog):
    """임베딩 모델 설정 다이얼로그"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, current_config: dict, theme_colors: dict):
        super().__init__()
        self.current_config = current_config
        self.theme_colors = theme_colors
        self.setWindowTitle("⚙️ Embedding Model Settings")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 헤더
        header = QLabel("🧠 Embedding Model Configuration")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header)
        
        # 모델 타입 선택
        type_group = QGroupBox("Model Type")
        type_layout = QVBoxLayout()
        
        type_label = QLabel("Select Embedding Model:")
        type_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "local - 내장형 (무료, 빠름)",
            "openai - OpenAI (유료, 고성능)",
            "google - Google (무료 티어, 고성능)"
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # 상세 설정
        self.details_group = QGroupBox("Model Details")
        self.details_layout = QVBoxLayout()
        self.details_group.setLayout(self.details_layout)
        layout.addWidget(self.details_group)
        
        # 정보 표시
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            padding: 15px;
            background: rgba(33, 150, 243, 0.1);
            border-radius: 8px;
            margin-top: 10px;
        """)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        # 버튼
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save")
        self.cancel_btn = QPushButton("❌ Cancel")
        
        self.save_btn.setMinimumHeight(40)
        self.cancel_btn.setMinimumHeight(40)
        
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        # 초기값 설정
        self._load_current_config()
    
    def _on_type_changed(self, index: int):
        """모델 타입 변경 시"""
        # 기존 위젯 제거
        for i in reversed(range(self.details_layout.count())):
            self.details_layout.itemAt(i).widget().setParent(None)
        
        if index == 0:  # Local
            self._show_local_settings()
        elif index == 1:  # OpenAI
            self._show_openai_settings()
        elif index == 2:  # Google
            self._show_google_settings()
    
    def _show_local_settings(self):
        """내장형 설정"""
        label = QLabel("Model: dragonkue-KoEn-E5-Tiny")
        self.details_layout.addWidget(label)
        
        dim_label = QLabel("Dimension: 384")
        self.details_layout.addWidget(dim_label)
        
        self.info_label.setText("""
        ✅ 내장형 모델 (Local)
        
        • 무료 사용
        • 빠른 처리 속도
        • 인터넷 불필요
        • 한국어 최적화
        • 차원: 384
        """)
    
    def _show_openai_settings(self):
        """OpenAI 설정"""
        # API Key
        key_label = QLabel("API Key:")
        self.details_layout.addWidget(key_label)
        
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setPlaceholderText("sk-...")
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.details_layout.addWidget(self.openai_key_input)
        
        # Model
        model_label = QLabel("Model:")
        self.details_layout.addWidget(model_label)
        
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems([
            "text-embedding-3-small (1536 dim)",
            "text-embedding-3-large (3072 dim)"
        ])
        self.details_layout.addWidget(self.openai_model_combo)
        
        self.info_label.setText("""
        🚀 OpenAI Embedding
        
        • 고성능 임베딩
        • 다국어 지원
        • API 키 필요 (유료)
        • 인터넷 연결 필요
        • 차원: 1536 or 3072
        """)
    
    def _show_google_settings(self):
        """Google 설정"""
        # API Key
        key_label = QLabel("API Key:")
        self.details_layout.addWidget(key_label)
        
        self.google_key_input = QLineEdit()
        self.google_key_input.setPlaceholderText("AIza...")
        self.google_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.details_layout.addWidget(self.google_key_input)
        
        model_label = QLabel("Model: embedding-001")
        self.details_layout.addWidget(model_label)
        
        self.info_label.setText("""
        🌐 Google Embedding
        
        • 고성능 임베딩
        • 무료 티어 제공
        • API 키 필요
        • 인터넷 연결 필요
        • 차원: 768
        """)
    
    def _load_current_config(self):
        """현재 설정 로드"""
        embedding_type = self.current_config.get("type", "local")
        
        if embedding_type == "local":
            self.type_combo.setCurrentIndex(0)
        elif embedding_type == "openai":
            self.type_combo.setCurrentIndex(1)
        elif embedding_type == "google":
            self.type_combo.setCurrentIndex(2)
    
    def _on_save(self):
        """설정 저장"""
        index = self.type_combo.currentIndex()
        
        if index == 0:  # Local
            config = {
                "type": "local",
                "model": "dragonkue-KoEn-E5-Tiny",
                "dimension": 384
            }
        elif index == 1:  # OpenAI
            api_key = self.openai_key_input.text().strip()
            if not api_key:
                self.info_label.setText("❌ API Key is required!")
                return
            
            model_text = self.openai_model_combo.currentText()
            model = "text-embedding-3-small" if "small" in model_text else "text-embedding-3-large"
            
            config = {
                "type": "openai",
                "api_key": api_key,
                "model": model,
                "dimension": 1536 if "small" in model else 3072
            }
        elif index == 2:  # Google
            api_key = self.google_key_input.text().strip()
            if not api_key:
                self.info_label.setText("❌ API Key is required!")
                return
            
            config = {
                "type": "google",
                "api_key": api_key,
                "model": "embedding-001",
                "dimension": 768
            }
        
        self.settings_changed.emit(config)
        self.accept()
    
    def _apply_style(self):
        from ui.rag.glass_style import GlassStyle
        style = GlassStyle.get_style(self.theme_colors)
        self.setStyleSheet(style)
```

### RAG Management Window에 설정 버튼 추가

```python
# _create_toolbar() 메서드에 추가

def _create_toolbar(self) -> QWidget:
    toolbar = QWidget()
    toolbar.setObjectName("glassPanel")
    layout = QHBoxLayout(toolbar)
    
    upload_file_btn = QPushButton("📤 Upload Files")
    upload_folder_btn = QPushButton("📁 Upload Folder")
    search_btn = QPushButton("🔍 Search")
    embedding_settings_btn = QPushButton("🧠 Embedding")  # 추가!
    settings_btn = QPushButton("⚙️ Settings")
    
    # 임베딩 설정 버튼 연결
    embedding_settings_btn.clicked.connect(self._open_embedding_settings)
    
    layout.addWidget(upload_file_btn)
    layout.addWidget(upload_folder_btn)
    layout.addStretch()
    layout.addWidget(search_btn)
    layout.addWidget(embedding_settings_btn)  # 추가!
    layout.addWidget(settings_btn)
    
    return toolbar

def _open_embedding_settings(self):
    """임베딩 설정 다이얼로그 열기"""
    from ui.rag.embedding_settings_dialog import EmbeddingSettingsDialog
    
    dialog = EmbeddingSettingsDialog(
        current_config=self.embedding_config,
        theme_colors=self.theme_colors
    )
    dialog.settings_changed.connect(self._on_embedding_changed)
    dialog.exec()

def _on_embedding_changed(self, new_config: dict):
    """임베딩 설정 변경 시"""
    # 설정 저장
    self.config_manager.update_embedding(**new_config)
    
    # 임베딩 모델 재생성
    from core.rag.embeddings.embedding_factory import EmbeddingFactory
    self.embeddings = EmbeddingFactory.create(
        embedding_type=new_config["type"],
        **new_config
    )
    
    # 사용자 알림
    QMessageBox.information(
        self,
        "Success",
        f"Embedding model changed to: {new_config['type']}"
    )
```

## 구현 가이드

### 필요한 패키지

```bash
# 이미 설치됨
langchain
langchain-experimental  # SemanticChunker

# 외장형 임베딩용 (선택)
pip install langchain-openai      # OpenAI
pip install langchain-google-genai  # Google

# 확인
pip list | grep langchain
```

### 설정 파일 (rag_config.json)

**위치**: 사용자 지정 외부 경로 (config_path_manager 사용)

```python
# 설정 파일 로드 (외부 경로)
from utils.config_path import config_path_manager
from pathlib import Path

# 사용자 지정 외부 경로
config_dir = config_path_manager.get_user_config_path()
if not config_dir:
    # 폴백: 홈 디렉토리
    config_dir = Path.home() / ".chat-ai-agent"
    config_dir.mkdir(parents=True, exist_ok=True)

rag_config_path = config_dir / "rag_config.json"

# 없으면 기본값 생성
if not rag_config_path.exists():
    create_default_rag_config(rag_config_path)

# 예시 경로:
# macOS/Linux: ~/.chat-ai-agent/rag_config.json
# Windows: C:\Users\<user>\AppData\Local\ChatAIAgent\rag_config.json
```

```json
{
  "vector_db": "LanceDB",
  "embedding_model": "dragonkue-KoEn-E5-Tiny",
  
  "chunking": {
    "default_strategy": "sliding_window",
    "strategies": {
      "semantic": {
        "threshold_type": "percentile",
        "threshold_amount": 95
      },
      "document_specific": {
        "code_chunk_size": 500,
        "table_rows_per_chunk": 10
      },
      "sliding_window": {
        "window_size": 500,
        "overlap_ratio": 0.2
      }
    }
  },
  
  "batch_upload": {
    "max_workers": 4,
    "max_file_size_mb": 50,
    "exclude_patterns": ["node_modules", ".git", "venv"]
  },
  
  "topic_management": {
    "enable_hierarchy": true,
    "max_depth": 3
  }
}
```

### 구현 우선순위

#### Phase 1: 데이터 계층 (1일)
- [ ] SQLite 스키마 생성 (topics, documents 테이블)
- [ ] TopicManager (SQLite CRUD - 수동 생성)
- [ ] LanceDB metadata 필드 확장 (source, document_id, topic_id, chunk_index, chunking_strategy)
- [ ] 계층적 삭제 구현 (토픽→문서→청크)

#### Phase 2: 임베딩 모델 관리 (1-2일)
- [ ] BaseEmbeddingStrategy 인터페이스
- [ ] LocalEmbeddingStrategy (현재 사용 중)
- [ ] CustomLocalEmbeddingStrategy (사용자 모델 폴더)
- [ ] OpenAIEmbeddingStrategy (선택)
- [ ] GoogleEmbeddingStrategy (선택)
- [ ] EmbeddingFactory
- [ ] EmbeddingConfigManager
- [ ] EmbeddingSettingsDialog UI

#### Phase 3: 청킹 전략 (3-4시간)
- [ ] ChunkingStrategySelector UI (풍선 도움말)
- [ ] SemanticChunkingStrategy (LangChain)
- [ ] CodeChunkingStrategy (LangChain, 20개 언어)
- [ ] MarkdownChunkingStrategy (LangChain)
- [ ] TableChunkingStrategy (직접 구현, 헤더+10행)
- [ ] SlidingWindowChunkingStrategy (현재 사용 중)

#### Phase 4: 배치 업로드 (2-3일)
- [ ] FileScanner (50개 이상 확장자)
- [ ] BatchProcessor (SQLite + LanceDB 동시 업데이트)
- [ ] ProgressTracker (실시간 통계)
- [ ] BatchUploadDialog UI (진행률, 통계 카드, 로그)
- [ ] 병렬 처리 (ThreadPoolExecutor)

#### Phase 5: Topic 관리 UI (1-2일)
- [ ] Topic 생성 다이얼로그 (이름, 설명, 부모 토픽)
- [ ] Topic 편집/삭제 기능
- [ ] Topic 계층 구조 UI (드래그 앤 드롭, 최대 3단계)
- [ ] TopicTreeWidget (검색 기능)

#### Phase 6: 메인 UI (2-3일)
- [ ] RAGManagementWindow (글래스모피즘)
- [ ] 3분할 레이아웃 (Topic Tree 30% | Document List 40% | Preview 30%)
- [ ] DocumentListWidget (파일명, 청크 수, 전략, 날짜)
- [ ] Preview 패널 (문서 미리보기, View Chunks, Delete)
- [ ] GlassStyle (theme.json 기반)

#### Phase 7: 검색 & 통합 (1-2일)
- [ ] 토픽 필터링 검색 (선택 시 해당 토픽만, 미선택 시 전체)
- [ ] 문서 삭제 기능 (청크 자동 삭제)
- [ ] 설정 파일 외부 경로 관리
- [ ] 전체 워크플로우 테스트

### 예상 총 구현 시간: 2주

---

## 핵심 포인트 요약

### ✅ 데이터 저장 구조
- **LanceDB**: 벡터 검색 + 최소 메타데이터 (document_id, topic_id)
- **SQLite**: 토픽/문서 관리 + 통계 + UI 표시
- **조합 이유**: 빠른 검색 + 쉬운 관리

### ✅ 청킹 전략
- **Semantic**: LangChain SemanticChunker (이미 있음!)
- **Document-Specific**: LangChain Language Splitters (이미 있음!)
- **Sliding Window**: RecursiveCharacterTextSplitter (현재 사용 중!)
- **구현 시간**: 3-4시간 (라이브러리 활용)

### ✅ 동일 컬렉션 내 다양한 전략 사용 가능
- 벡터 검색은 청킹 방식과 무관
- 메타데이터에 전략 기록
- 임베딩 모델만 동일하면 OK

### ✅ 토픽 필터링 검색
- 전체 검색: filter 없음
- 특정 토픽: filter={"topic_id": "topic_123"}
- 복수 토픽: filter={"topic_id": ["topic_1", "topic_2"]}

### ✅ 배치 업로드
- 병렬 처리 (ThreadPoolExecutor)
- SQLite + LanceDB 동시 업데이트
- 진행 상황 실시간 표시

### ✅ Topic 관리
- 사용자 수동 생성 (이름, 설명, 부모 토픽)
- 계층 구조 지원 (최대 3단계)
- 드래그 앤 드롭으로 이동

---

**작성일**: 2024
**버전**: 2.0 (통합 완료)
**상태**: 구현 준비 완료
**다음 단계**: Phase 1 (청킹 전략) 구현 시작
