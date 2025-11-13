# 임베딩 모델 구현 가이드

## 구현 우선순위

### 1단계: 핵심 인프라 (완료)
- ✅ BaseEmbeddingModel 추상 클래스
- ✅ EmbeddingModelFactory 팩토리
- ✅ 기본 설정 관리 시스템
- ✅ 모델 다운로드 시스템

### 2단계: 모델 통합 (진행중)
- ✅ SentenceTransformersEmbedding 구현
- ✅ OpenAIEmbedding API 래퍼
- 🔄 한국어 모델 최적화
- ⏳ 배치 처리 시스템

### 3단계: 성능 최적화 (예정)
- ⏳ GPU 가속 지원
- ⏳ 멀티스레딩 처리
- ⏳ 캐싱 시스템 개선
- ⏳ 벤치마킹 도구

## 코드 구조

### 디렉토리 구조
```
core/rag/embeddings/
├── __init__.py
├── base_embedding.py          # 추상 기본 클래스
├── embedding_factory.py       # 팩토리 패턴
├── sentence_transformers_embedding.py  # 로컬 모델
├── openai_embedding.py        # API 기반 모델
├── embedding_cache.py         # 캐싱 시스템
├── embedding_config.py        # 설정 관리
└── model_downloader.py        # 모델 다운로드
```

### 핵심 클래스 구현

#### BaseEmbeddingModel
```python
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

class BaseEmbeddingModel(ABC):
    """임베딩 모델의 기본 인터페이스"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """텍스트를 벡터로 변환"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """임베딩 벡터 차원 반환"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """모델 사용 가능 여부 확인"""
        pass
```

#### EmbeddingModelFactory
```python
from typing import Dict, Type, List
from .base_embedding import BaseEmbeddingModel

class EmbeddingModelFactory:
    """임베딩 모델 생성 팩토리"""
    
    _models: Dict[str, Type[BaseEmbeddingModel]] = {}
    
    @classmethod
    def register_model(cls, model_type: str, model_class: Type[BaseEmbeddingModel]):
        """새로운 모델 타입 등록"""
        cls._models[model_type] = model_class
    
    @classmethod
    def create_model(cls, model_name: str, **kwargs) -> BaseEmbeddingModel:
        """모델 인스턴스 생성"""
        config = EmbeddingConfig.get_model_config(model_name)
        model_type = config.get('type', 'sentence_transformers')
        
        if model_type not in cls._models:
            raise ValueError(f"Unknown model type: {model_type}")
        
        model_class = cls._models[model_type]
        return model_class(model_name, **config, **kwargs)
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """사용 가능한 모델 목록 반환"""
        return list(EmbeddingConfig.get_all_models().keys())
```

### 구체적 구현 예시

#### SentenceTransformersEmbedding
```python
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
from .base_embedding import BaseEmbeddingModel

class SentenceTransformersEmbedding(BaseEmbeddingModel):
    """Sentence Transformers 기반 임베딩 모델"""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
        self.device = kwargs.get('device', 'auto')
        self.cache_folder = kwargs.get('cache_folder', './models/embeddings/')
        self._model = None
    
    def _load_model(self):
        """지연 로딩으로 모델 초기화"""
        if self._model is None:
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_folder
            )
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """텍스트를 벡터로 변환"""
        self._load_model()
        return self._model.encode(texts, convert_to_numpy=True)
    
    def get_dimension(self) -> int:
        """임베딩 벡터 차원 반환"""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
    
    def is_available(self) -> bool:
        """모델 사용 가능 여부 확인"""
        try:
            self._load_model()
            return True
        except Exception:
            return False
```

#### OpenAIEmbedding
```python
import openai
import numpy as np
from typing import List
from .base_embedding import BaseEmbeddingModel

class OpenAIEmbedding(BaseEmbeddingModel):
    """OpenAI API 기반 임베딩 모델"""
    
    def __init__(self, model_name: str, **kwargs):
        super().__init__(model_name, **kwargs)
        self.api_key = kwargs.get('api_key')
        self.client = openai.OpenAI(api_key=self.api_key)
        self.dimension = kwargs.get('dimension', 1536)
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """텍스트를 벡터로 변환"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        
        embeddings = []
        for data in response.data:
            embeddings.append(data.embedding)
        
        return np.array(embeddings)
    
    def get_dimension(self) -> int:
        """임베딩 벡터 차원 반환"""
        return self.dimension
    
    def is_available(self) -> bool:
        """모델 사용 가능 여부 확인"""
        return self.api_key is not None
```

## 설정 관리 시스템

### EmbeddingConfig 클래스
```python
import json
from pathlib import Path
from typing import Dict, Any

class EmbeddingConfig:
    """임베딩 모델 설정 관리"""
    
    _config_path = Path("core/rag/config/embedding_config.json")
    _config_cache = None
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """설정 파일 로드"""
        if cls._config_cache is None:
            with open(cls._config_path, 'r', encoding='utf-8') as f:
                cls._config_cache = json.load(f)
        return cls._config_cache
    
    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """특정 모델의 설정 반환"""
        config = cls.load_config()
        return config.get('models', {}).get(model_name, {})
    
    @classmethod
    def get_default_model(cls) -> str:
        """기본 모델명 반환"""
        config = cls.load_config()
        return config.get('default_model', 'dragonkue/KoEn-E5-Tiny')
    
    @classmethod
    def get_all_models(cls) -> Dict[str, Dict[str, Any]]:
        """모든 모델 설정 반환"""
        config = cls.load_config()
        return config.get('models', {})
```

## 캐싱 시스템

### EmbeddingCache 클래스
```python
import hashlib
import pickle
import sqlite3
from pathlib import Path
from typing import List, Optional
import numpy as np

class EmbeddingCache:
    """임베딩 결과 캐싱 시스템"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "embedding_cache.db"
        self._init_db()
    
    def _init_db(self):
        """캐시 데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    text_hash TEXT PRIMARY KEY,
                    model_name TEXT,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def _get_text_hash(self, text: str, model_name: str) -> str:
        """텍스트와 모델명으로 해시 생성"""
        content = f"{model_name}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        """캐시에서 임베딩 조회"""
        text_hash = self._get_text_hash(text, model_name)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT embedding FROM embedding_cache WHERE text_hash = ?",
                (text_hash,)
            )
            row = cursor.fetchone()
            
            if row:
                return pickle.loads(row[0])
        
        return None
    
    def set(self, text: str, model_name: str, embedding: np.ndarray):
        """캐시에 임베딩 저장"""
        text_hash = self._get_text_hash(text, model_name)
        embedding_blob = pickle.dumps(embedding)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO embedding_cache 
                   (text_hash, model_name, embedding) VALUES (?, ?, ?)""",
                (text_hash, model_name, embedding_blob)
            )
```

## 모델 다운로드 시스템

### ModelDownloader 클래스
```python
from pathlib import Path
from typing import Optional
import requests
from tqdm import tqdm

class ModelDownloader:
    """임베딩 모델 다운로드 관리"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download_model(self, model_name: str, progress_callback: Optional[callable] = None) -> bool:
        """모델 다운로드"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # 진행률 콜백 설정
            if progress_callback:
                progress_callback(0, f"Downloading {model_name}...")
            
            # 모델 다운로드 (sentence-transformers가 자동 처리)
            model = SentenceTransformer(model_name, cache_folder=str(self.cache_dir))
            
            if progress_callback:
                progress_callback(100, f"Downloaded {model_name}")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(-1, f"Error downloading {model_name}: {str(e)}")
            return False
    
    def is_model_cached(self, model_name: str) -> bool:
        """모델이 로컬에 캐시되어 있는지 확인"""
        model_path = self.cache_dir / model_name.replace('/', '_')
        return model_path.exists()
    
    def get_model_size(self, model_name: str) -> Optional[int]:
        """모델 크기 반환 (바이트)"""
        if self.is_model_cached(model_name):
            model_path = self.cache_dir / model_name.replace('/', '_')
            return sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
        return None
```

## 통합 사용 예시

### RAG 시스템과의 통합
```python
from core.rag.embeddings import EmbeddingModelFactory

class RAGEmbeddingManager:
    """RAG 시스템의 임베딩 관리자"""
    
    def __init__(self):
        self.current_model = None
        self.model_name = EmbeddingConfig.get_default_model()
        self._load_model()
    
    def _load_model(self):
        """현재 설정된 모델 로드"""
        try:
            self.current_model = EmbeddingModelFactory.create_model(self.model_name)
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            # 폴백 모델 시도
            self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.current_model = EmbeddingModelFactory.create_model(self.model_name)
    
    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """문서들을 임베딩으로 변환"""
        if not self.current_model:
            raise RuntimeError("No embedding model available")
        
        return self.current_model.encode(documents)
    
    def embed_query(self, query: str) -> np.ndarray:
        """쿼리를 임베딩으로 변환"""
        return self.embed_documents([query])[0]
    
    def switch_model(self, model_name: str):
        """임베딩 모델 변경"""
        self.model_name = model_name
        self._load_model()
```

## 팩토리 등록

### 모델 타입 등록
```python
# core/rag/embeddings/__init__.py
from .embedding_factory import EmbeddingModelFactory
from .sentence_transformers_embedding import SentenceTransformersEmbedding
from .openai_embedding import OpenAIEmbedding

# 모델 타입 등록
EmbeddingModelFactory.register_model('sentence_transformers', SentenceTransformersEmbedding)
EmbeddingModelFactory.register_model('openai_api', OpenAIEmbedding)

__all__ = [
    'EmbeddingModelFactory',
    'BaseEmbeddingModel',
    'SentenceTransformersEmbedding',
    'OpenAIEmbedding'
]
```

## 테스트 코드

### 단위 테스트 예시
```python
import unittest
from core.rag.embeddings import EmbeddingModelFactory

class TestEmbeddingModels(unittest.TestCase):
    
    def test_sentence_transformers_model(self):
        """Sentence Transformers 모델 테스트"""
        model = EmbeddingModelFactory.create_model('dragonkue/KoEn-E5-Tiny')
        
        texts = ["안녕하세요", "Hello world"]
        embeddings = model.encode(texts)
        
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(embeddings.shape[1], model.get_dimension())
    
    def test_model_caching(self):
        """모델 캐싱 테스트"""
        cache = EmbeddingCache(Path("./test_cache"))
        
        # 캐시 저장
        embedding = np.array([1.0, 2.0, 3.0])
        cache.set("test text", "test_model", embedding)
        
        # 캐시 조회
        cached_embedding = cache.get("test text", "test_model")
        np.testing.assert_array_equal(embedding, cached_embedding)
```

## 성능 최적화 팁

### 1. 배치 처리
- 여러 텍스트를 한 번에 처리하여 GPU 활용도 향상
- 메모리 사용량을 고려한 동적 배치 크기 조정

### 2. 지연 로딩
- 모델을 실제 사용 시점에 로드하여 초기화 시간 단축
- 메모리 사용량 최적화

### 3. 캐싱 전략
- 자주 사용되는 임베딩 결과를 메모리에 캐시
- 디스크 캐시로 재시작 후에도 성능 유지

이 구현 가이드를 따라 단계적으로 임베딩 시스템을 구축하면 확장 가능하고 성능이 우수한 RAG 시스템을 만들 수 있습니다.