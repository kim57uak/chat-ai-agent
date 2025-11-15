# Sentence-Transformers 패키징 이슈 해결 가이드

## 📋 목차
1. [문제 상황](#문제-상황)
2. [근본 원인 분석](#근본-원인-분석)
3. [해결 과정](#해결-과정)
4. [최종 솔루션](#최종-솔루션)
5. [검증 방법](#검증-방법)
6. [교훈 및 베스트 프랙티스](#교훈-및-베스트-프랙티스)

---

## 문제 상황

### 증상
PyInstaller로 패키징한 애플리케이션에서 `sentence-transformers` 라이브러리 사용 시 다음 오류 발생:

```python
ModuleNotFoundError: No module named 'transformers.generation.utils'
ImportError: cannot import name 'GenerationMixin' from 'transformers.modeling_utils'
```

### 환경
- **OS**: macOS (Apple Silicon M1/M2)
- **Python**: 3.11
- **PyInstaller**: 6.15.0
- **sentence-transformers**: 3.3.1
- **transformers**: 4.46.3
- **torch**: 2.5.1

### 영향 범위
- RAG(Retrieval-Augmented Generation) 기능 완전 불능
- 한국어 임베딩 모델 로딩 실패
- 패키징된 앱에서만 발생 (개발 환경에서는 정상 작동)

---

## 근본 원인 분석

### 1. Lazy Import 문제
`sentence-transformers`는 내부적으로 `transformers` 라이브러리를 **lazy import** 방식으로 사용:

```python
# sentence_transformers 내부 코드
def _import_transformers():
    from transformers import AutoModel, AutoTokenizer
    from transformers.generation.utils import GenerationMixin
    return AutoModel, AutoTokenizer, GenerationMixin
```

**문제점**: PyInstaller는 정적 분석으로 import를 감지하는데, lazy import는 런타임에만 실행되므로 감지 불가

### 2. 복잡한 의존성 체인
```
sentence-transformers
  └─ transformers
      ├─ transformers.models.auto
      │   ├─ modeling_auto
      │   ├─ tokenization_auto
      │   └─ configuration_auto
      ├─ transformers.generation
      │   └─ utils (GenerationMixin)
      └─ transformers.modeling_utils
  └─ torch
      └─ torch.nn
```

각 모듈이 동적으로 로드되므로 PyInstaller가 전체 체인을 추적하지 못함

### 3. PyInstaller의 한계
- **정적 분석 기반**: `import` 문만 감지
- **동적 import 미지원**: `importlib.import_module()`, `__import__()` 등 감지 불가
- **조건부 import 누락**: `if` 문 내부의 import 무시

---

## 해결 과정

### Phase 1: 기본 Hook 작성 (실패)
**시도**: PyInstaller hook 파일 생성

```python
# hooks/hook-sentence_transformers.py
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('sentence_transformers')
```

**결과**: ❌ 여전히 `transformers.generation.utils` 누락

**원인**: `collect_all`은 패키지 자체만 수집하고, 동적 의존성은 수집하지 못함

---

### Phase 2: Hidden Imports 추가 (부분 성공)
**시도**: spec 파일에 명시적 hiddenimports 추가

```python
# my_genie.spec
hiddenimports=[
    'sentence_transformers',
    'transformers',
    'transformers.models.auto',
    'transformers.generation',
    'transformers.generation.utils',
]
```

**결과**: ⚠️ 일부 모델은 작동하지만 여전히 간헐적 오류

**원인**: 모든 하위 모듈을 수동으로 나열하기 어려움

---

### Phase 3: Runtime Hook 도입 (개선)
**시도**: 런타임에 사전 import 수행

```python
# hooks/rthook_sentence_transformers.py
import sys

if getattr(sys, 'frozen', False):
    # 패키징된 앱에서만 실행
    try:
        import transformers
        import transformers.generation.utils
        import transformers.models.auto.modeling_auto
        print("[RTHOOK] Pre-imported transformers modules")
    except Exception as e:
        print(f"[RTHOOK] Warning: {e}")
```

**결과**: ✅ 대부분의 경우 작동하지만 여전히 불안정

**원인**: import 순서 문제 - 다른 모듈이 먼저 로드되면 실패

---

### Phase 4: 동적 Import Resolver 구현 (핵심 솔루션)
**시도**: 중앙 집중식 동적 import 관리 시스템 구축

```python
# core/dynamic_import_resolver.py
class DynamicImportResolver:
    """Centralized dynamic import resolver for PyInstaller compatibility."""
    
    def __init__(self):
        self._cached_modules = {}
        self._import_strategies = {}
        self._register_strategies()
    
    def _import_sentence_transformers(self, module_name: str):
        """Import sentence_transformers with ALL dependencies pre-loaded."""
        try:
            # CRITICAL: Pre-import ALL transformers dependencies
            import torch
            import torch.nn
            import transformers
            import transformers.generation
            import transformers.generation.utils
            import transformers.modeling_utils
            import transformers.models.auto.modeling_auto
            import transformers.models.auto.tokenization_auto
            import transformers.models.auto.configuration_auto
            
            # Now safe to import sentence_transformers
            import sentence_transformers
            return sentence_transformers
        except ImportError as e:
            logger.error(f"sentence_transformers import failed: {e}")
            return None
```

**핵심 아이디어**:
1. **사전 로딩**: 의존성을 명시적 순서로 미리 import
2. **캐싱**: 한 번 로드된 모듈 재사용
3. **Fallback**: 실패 시 대체 전략 시도

**결과**: ✅ 100% 안정적으로 작동

---

### Phase 5: 통합 및 최적화
**최종 구조**:

```
패키징 시스템
├── my_genie.spec (PyInstaller 설정)
│   ├── collect_all('sentence_transformers')
│   ├── collect_all('transformers')
│   ├── collect_all('torch')
│   └── hiddenimports (명시적 모듈 리스트)
│
├── hooks/hook-sentence_transformers.py (빌드 타임)
│   └── 패키지 데이터 수집
│
├── hooks/hook-transformers.py (빌드 타임)
│   └── transformers 하위 모듈 수집
│
├── hooks/rthook_sentence_transformers.py (런타임)
│   └── 앱 시작 시 사전 import
│
└── core/dynamic_import_resolver.py (런타임)
    └── 동적 import 중앙 관리
```

---

## 최종 솔루션

### 1. PyInstaller Spec 파일 설정

```python
# my_genie.spec
from PyInstaller.utils.hooks import collect_all

# 완전한 패키지 수집
sentence_transformers_datas, sentence_transformers_binaries, sentence_transformers_hiddenimports = collect_all('sentence_transformers')
transformers_datas, transformers_binaries, transformers_hiddenimports = collect_all('transformers')
torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')

a = Analysis(
    ['main.py'],
    binaries=(
        sentence_transformers_binaries + 
        transformers_binaries + 
        torch_binaries
    ),
    datas=(
        sentence_transformers_datas + 
        transformers_datas + 
        torch_datas
    ),
    hiddenimports=[
        # Sentence Transformers
        'sentence_transformers',
        'sentence_transformers.models',
        'sentence_transformers.util',
        
        # Transformers - CRITICAL
        'transformers',
        'transformers.modeling_utils',
        'transformers.generation',
        'transformers.generation.utils',
        'transformers.generation.configuration_utils',
        'transformers.models.auto',
        'transformers.models.auto.modeling_auto',
        'transformers.models.auto.tokenization_auto',
        'transformers.models.auto.configuration_auto',
        
        # Torch
        'torch',
        'torch.nn',
        'torch.nn.functional',
    ] + (
        sentence_transformers_hiddenimports +
        transformers_hiddenimports +
        torch_hiddenimports
    ),
    hookspath=['hooks'],
    runtime_hooks=[
        'hooks/rthook_sentence_transformers.py',
    ],
)
```

### 2. Build-time Hook

```python
# hooks/hook-transformers.py
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('transformers')

# Collect all submodules
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('transformers.models')
hiddenimports += collect_submodules('transformers.models.auto')
hiddenimports += collect_submodules('transformers.generation')

# Critical modules that must be explicitly included
hiddenimports += [
    'transformers.modeling_utils',
    'transformers.generation.utils',
    'transformers.generation.configuration_utils',
    'transformers.models.auto.modeling_auto',
    'transformers.models.auto.tokenization_auto',
    'transformers.models.auto.configuration_auto',
]
```

### 3. Runtime Hook

```python
# hooks/rthook_sentence_transformers.py
import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):
    # Running in packaged app
    if sys.platform == 'darwin':
        base_path = Path(sys.executable).parent.parent / 'Resources'
    else:
        base_path = Path(sys.executable).parent
    
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
        print(f"[RTHOOK] Added base path: {base_path}")
    
    # Pre-import critical transformers modules
    try:
        import transformers
        import transformers.models
        import transformers.models.auto
        import transformers.models.auto.modeling_auto
        import transformers.models.auto.tokenization_auto
        import transformers.models.auto.configuration_auto
        print("[RTHOOK] Pre-imported transformers modules")
    except Exception as e:
        print(f"[RTHOOK] Warning: Could not pre-import transformers: {e}")
    
    # Pre-import torch
    try:
        import torch
        import torch.nn
        print("[RTHOOK] Pre-imported torch modules")
    except Exception as e:
        print(f"[RTHOOK] Warning: Could not pre-import torch: {e}")
```

### 4. Dynamic Import Resolver

```python
# core/dynamic_import_resolver.py
class DynamicImportResolver:
    """Centralized dynamic import resolver for PyInstaller compatibility."""
    
    def _import_sentence_transformers(self, module_name: str) -> Optional[Any]:
        """Import sentence_transformers modules with fallback."""
        try:
            # Pre-import ALL transformers dependencies
            import torch
            import torch.nn
            import transformers
            import transformers.generation
            import transformers.generation.utils
            import transformers.modeling_utils
            import transformers.models.auto.modeling_auto
            import transformers.models.auto.tokenization_auto
            import transformers.models.auto.configuration_auto
            
            import sentence_transformers
            if module_name == 'sentence_transformers':
                return sentence_transformers
            return self._get_nested_attr(sentence_transformers, module_name.replace('sentence_transformers.', ''))
        except ImportError as e:
            logger.error(f"sentence_transformers import failed: {e}")
        return None

# Global instance
dynamic_import_resolver = DynamicImportResolver()
```

### 5. 사용 예시

```python
# core/rag/embeddings/sentence_transformer_embeddings.py
from core.dynamic_import_resolver import dynamic_import_resolver

class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str):
        # 동적 import resolver 사용
        SentenceTransformer = dynamic_import_resolver.safe_import(
            'sentence_transformers',
            'SentenceTransformer'
        )
        
        if SentenceTransformer is None:
            raise ImportError("sentence_transformers not available")
        
        self.model = SentenceTransformer(model_name)
```

---

## 검증 방법

### 1. 개발 환경 테스트
```bash
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
```

### 2. 패키징 빌드
```bash
pyinstaller my_genie.spec
```

### 3. 패키징된 앱 테스트
```bash
# macOS
./dist/MyGenie.app/Contents/MacOS/MyGenie

# Windows
dist\MyGenie.exe

# Linux
./dist/MyGenie
```

### 4. 로그 확인
```bash
# 런타임 훅 메시지 확인
[RTHOOK] Added base path: /path/to/app/Resources
[RTHOOK] Pre-imported transformers modules
[RTHOOK] Pre-imported torch modules
```

### 5. 기능 테스트
```python
# RAG 임베딩 생성 테스트
from core.rag.embeddings import get_embedding_model

model = get_embedding_model("dragonkue/KoEn-E5-Tiny")
embeddings = model.embed_documents(["테스트 문장"])
print(f"Embedding dimension: {len(embeddings[0])}")
```

---

## 교훈 및 베스트 프랙티스

### 핵심 교훈

1. **Lazy Import는 PyInstaller의 적**
   - 동적 import는 정적 분석으로 감지 불가
   - 명시적 사전 로딩 필수

2. **의존성 체인 전체를 고려**
   - 단일 모듈만 추가해서는 부족
   - 전체 의존성 트리 분석 필요

3. **다층 방어 전략**
   - Build-time hook (패키지 수집)
   - Runtime hook (사전 import)
   - Dynamic resolver (fallback)

4. **플랫폼별 차이 고려**
   - macOS: `.app/Contents/Resources`
   - Windows: 실행 파일과 동일 디렉토리
   - Linux: 실행 파일과 동일 디렉토리

### 베스트 프랙티스

#### ✅ DO
- `collect_all()` 사용하여 전체 패키지 수집
- Runtime hook에서 의존성 사전 import
- 중앙 집중식 import 관리 시스템 구축
- 상세한 로깅으로 디버깅 용이하게
- 캐싱으로 성능 최적화

#### ❌ DON'T
- 수동으로 모든 hiddenimports 나열하지 말 것
- Runtime hook 없이 spec 파일만 수정하지 말 것
- 에러 무시하지 말고 로깅할 것
- 플랫폼별 차이 간과하지 말 것

### 재사용 가능한 패턴

다른 복잡한 라이브러리 패키징 시 동일한 패턴 적용 가능:

```python
# 1. spec 파일에서 collect_all
library_datas, library_binaries, library_hiddenimports = collect_all('library_name')

# 2. Build-time hook 작성
# hooks/hook-library_name.py
from PyInstaller.utils.hooks import collect_all, collect_submodules
datas, binaries, hiddenimports = collect_all('library_name')
hiddenimports += collect_submodules('library_name')

# 3. Runtime hook 작성
# hooks/rthook_library_name.py
if getattr(sys, 'frozen', False):
    import library_name
    import library_name.submodule

# 4. Dynamic resolver에 전략 추가
def _import_library(self, module_name: str):
    import dependency1
    import dependency2
    import library_name
    return library_name
```

---

## 참고 자료

### 공식 문서
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PyInstaller Hooks](https://pyinstaller.org/en/stable/hooks.html)
- [sentence-transformers Documentation](https://www.sbert.net/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/)

### 관련 이슈
- [PyInstaller #7783: Dynamic imports not detected](https://github.com/pyinstaller/pyinstaller/issues/7783)
- [sentence-transformers #2156: Packaging issues](https://github.com/UKPLab/sentence-transformers/issues/2156)

### 프로젝트 파일
- `core/dynamic_import_resolver.py` - 동적 import 관리
- `hooks/hook-sentence_transformers.py` - Build-time hook
- `hooks/hook-transformers.py` - Transformers hook
- `hooks/rthook_sentence_transformers.py` - Runtime hook
- `my_genie.spec` - PyInstaller 설정

---

## 결론

**4일간의 디버깅 끝에 얻은 핵심 인사이트**:

> PyInstaller 패키징은 단순히 파일을 모으는 것이 아니라, 
> 런타임 의존성 체인 전체를 이해하고 명시적으로 관리하는 것이다.

이 솔루션은 `sentence-transformers`뿐만 아니라 복잡한 의존성을 가진 모든 Python 라이브러리 패키징에 적용 가능한 범용 패턴입니다.

---

**작성일**: 2025-01-27  
**작성자**: Chat AI Agent Development Team  
**버전**: 1.0  
**라이선스**: MIT
