# 커스텀 임베딩 모델 사용 가이드

## 📋 개요

RAG 시스템에서 2가지 임베딩 모델 옵션 제공:
1. **디폴트 모델**: dragonkue-KoEn-E5-Tiny (384차원)
2. **사용자 선택 모델**: 폴더에서 직접 선택한 로컬 모델

## 🎯 사용 방법

### 1. 디폴트 모델 사용

```python
from core.rag.config.rag_config_manager import RAGConfigManager

config_manager = RAGConfigManager()
config_manager.use_default_model()
```

**설정 파일:**
```json
{
  "embedding": {
    "type": "local",
    "model": "exp-models/dragonkue-KoEn-E5-Tiny",
    "dimension": 384,
    "use_custom_model": false
  }
}
```

### 2. 사용자 커스텀 모델 사용

```python
from core.rag.config.rag_config_manager import RAGConfigManager

config_manager = RAGConfigManager()

# 사용자가 폴더에서 선택한 모델 경로
custom_path = "/Users/user/my_models/custom-embedding-model"
config_manager.set_custom_model(custom_path, dimension=768)
```

**설정 파일:**
```json
{
  "embedding": {
    "type": "local",
    "use_custom_model": true,
    "custom_model_path": "/Users/user/my_models/custom-embedding-model",
    "dimension": 768
  }
}
```

### 3. 임베딩 생성 (자동 선택)

```python
from core.rag.config.rag_config_manager import RAGConfigManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory

# 설정 로드
config_manager = RAGConfigManager()
embedding_config = config_manager.get_embedding_config()

# 팩토리가 자동으로 디폴트 or 커스텀 선택
embedding_type = embedding_config.pop('type')
embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)

# 사용
vectors = embeddings.embed_documents(["text1", "text2"])
query_vector = embeddings.embed_query("search query")
```

## 🖥️ UI 통합 (예정)

### RAG 관리 화면 구성

```
┌─────────────────────────────────────┐
│  임베딩 모델 설정                    │
├─────────────────────────────────────┤
│  ○ 디폴트 모델 사용                  │
│     dragonkue-KoEn-E5-Tiny (384차원) │
│                                      │
│  ○ 사용자 모델 선택                  │
│     [폴더 선택...] [선택됨: /path]   │
│     차원: [768]                      │
│                                      │
│  [저장]  [취소]                      │
└─────────────────────────────────────┘
```

### UI 코드 예시

```python
from PyQt6.QtWidgets import QRadioButton, QPushButton, QFileDialog

class EmbeddingSettingsDialog:
    def __init__(self):
        self.default_radio = QRadioButton("디폴트 모델 사용")
        self.custom_radio = QRadioButton("사용자 모델 선택")
        self.folder_btn = QPushButton("폴더 선택...")
        
        self.folder_btn.clicked.connect(self._select_folder)
    
    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "모델 폴더 선택")
        if folder:
            self.custom_model_path = folder
            # 차원 자동 감지 또는 사용자 입력
    
    def _on_save(self):
        config_manager = RAGConfigManager()
        
        if self.default_radio.isChecked():
            config_manager.use_default_model()
        else:
            config_manager.set_custom_model(
                self.custom_model_path,
                dimension=self.dimension_input.value()
            )
```

## 📊 동작 흐름

### 디폴트 모델
```
사용자 → [디폴트 선택] → use_default_model()
                      ↓
                  use_custom_model: false
                      ↓
              EmbeddingFactory.create()
                      ↓
          dragonkue-KoEn-E5-Tiny 로드
```

### 커스텀 모델
```
사용자 → [폴더 선택] → set_custom_model(path)
                      ↓
                  use_custom_model: true
                  custom_model_path: /path
                      ↓
              EmbeddingFactory.create()
                      ↓
          사용자 선택 모델 로드
```

## 🔧 지원 모델 형식

### HuggingFace 모델
- sentence-transformers 호환 모델
- 폴더 구조:
  ```
  custom-model/
  ├── config.json
  ├── pytorch_model.bin
  ├── tokenizer_config.json
  └── vocab.txt
  ```

### 예시 모델
- `intfloat/multilingual-e5-large` (1024차원)
- `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (768차원)
- `BAAI/bge-m3` (1024차원)

## ⚠️ 주의사항

1. **차원 일치**: 기존 벡터 DB와 차원이 다르면 새로 생성 필요
2. **모델 크기**: 큰 모델은 메모리 사용량 증가
3. **호환성**: sentence-transformers 호환 모델만 지원

## 🧪 테스트

```bash
source venv/bin/activate
python tests/test_custom_model_selection.py
```

**결과:**
```
✅ 디폴트 모델 사용
✅ 커스텀 모델 설정
✅ 모델 전환
```

## 📝 설정 파일 위치

- macOS/Linux: `~/.chat-ai-agent/rag_config.json`
- Windows: `%LOCALAPPDATA%\ChatAIAgent\rag_config.json`

## 🚫 OpenAI/Google 모델 숨김

현재 UI에서 노출하지 않음:
- `openai`: 코드에만 존재, UI 옵션 없음
- `google`: 코드에만 존재, UI 옵션 없음

필요시 나중에 활성화 가능.

---

**작성일**: 2024
**상태**: ✅ 구현 완료
**다음 단계**: UI 통합
