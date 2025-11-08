"""
Custom Embedding 사용 예시
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.rag.embeddings.embedding_factory import EmbeddingFactory
from core.rag.config.rag_config_manager import RAGConfigManager


def example1_huggingface_model():
    """예시 1: 다른 HuggingFace 모델 사용"""
    print("\n" + "="*60)
    print("예시 1: HuggingFace 모델 변경")
    print("="*60)
    
    # 방법 1: 직접 생성
    embeddings = EmbeddingFactory.create(
        "local",
        model="intfloat/multilingual-e5-large",  # 다른 모델
        enable_cache=True
    )
    
    result = embeddings.embed_query("테스트 쿼리")
    print(f"✅ 모델: intfloat/multilingual-e5-large")
    print(f"   차원: {len(result)}")
    
    # 방법 2: 설정 파일로 관리
    config_manager = RAGConfigManager()
    config_manager.update_embedding_config(
        type="local",
        model="intfloat/multilingual-e5-large",
        dimension=1024,
        enable_cache=True
    )
    print(f"✅ 설정 파일에 저장됨")


def example2_custom_strategy():
    """예시 2: 커스텀 전략 사용"""
    print("\n" + "="*60)
    print("예시 2: 커스텀 임베딩 전략")
    print("="*60)
    
    # Cohere 예시
    embeddings = EmbeddingFactory.create(
        "custom",
        model="embed-multilingual-v3.0",
        api_key="your-cohere-api-key",
        dimension=1024
    )
    
    print(f"✅ 커스텀 모델 생성됨")
    print(f"   타입: custom")
    print(f"   모델: embed-multilingual-v3.0")
    
    # 설정 파일로 관리
    config_manager = RAGConfigManager()
    config_manager.update_embedding_config(
        type="custom",
        model="embed-multilingual-v3.0",
        api_key="your-cohere-api-key",
        dimension=1024
    )
    print(f"✅ 설정 파일에 저장됨")


def example3_config_based():
    """예시 3: 설정 파일 기반 사용"""
    print("\n" + "="*60)
    print("예시 3: 설정 파일 기반 사용")
    print("="*60)
    
    # 1. 설정 파일 수정
    config_manager = RAGConfigManager()
    config_manager.update_embedding_config(
        type="local",
        model="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        dimension=768,
        enable_cache=True
    )
    
    # 2. 설정에서 로드
    embedding_config = config_manager.get_embedding_config()
    embedding_type = embedding_config.pop('type')
    
    embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)
    
    print(f"✅ 설정 파일에서 로드됨")
    print(f"   타입: {embedding_type}")
    print(f"   모델: {embedding_config['model']}")
    print(f"   차원: {embeddings.dimension}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Custom Embedding 사용 가이드")
    print("="*60)
    
    print("\n📝 사용 방법:")
    print("1. HuggingFace 모델 변경: model 파라미터만 변경")
    print("2. 커스텀 전략: custom_embeddings.py 수정 후 사용")
    print("3. 설정 파일: rag_config.json 직접 편집")
    
    try:
        example1_huggingface_model()
        example2_custom_strategy()
        example3_config_based()
        
        print("\n" + "="*60)
        print("✅ 모든 예시 완료!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 오류: {e}")
