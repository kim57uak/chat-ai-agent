#!/usr/bin/env python3
"""
RAG 설정 디버깅 스크립트
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_config():
    """현재 RAG 설정 확인"""
    try:
        from core.rag.config.rag_config_manager import RAGConfigManager
        
        print("=== RAG 설정 디버깅 ===")
        
        config_manager = RAGConfigManager()
        
        print(f"설정 파일 경로: {config_manager.config_path}")
        print(f"설정 파일 존재: {config_manager.config_path.exists()}")
        
        if config_manager.config_path.exists():
            with open(config_manager.config_path, 'r', encoding='utf-8') as f:
                raw_config = json.load(f)
            print(f"\n원본 설정 파일 내용:")
            print(json.dumps(raw_config, indent=2, ensure_ascii=False))
        
        print(f"\n현재 로드된 설정:")
        print(json.dumps(config_manager.config, indent=2, ensure_ascii=False))
        
        print(f"\n임베딩 설정:")
        embedding_config = config_manager.get_embedding_config()
        print(json.dumps(embedding_config, indent=2, ensure_ascii=False))
        
        print(f"\n등록된 모델들:")
        models = config_manager.get_embedding_models()
        for name, config in models.items():
            print(f"  {name}: {config}")
        
        print(f"\n현재 선택된 모델: {config_manager.get_current_embedding_model()}")
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()

def test_embedding_creation():
    """임베딩 생성 테스트"""
    try:
        from core.rag.embeddings.embedding_factory import EmbeddingFactory
        from core.rag.config.rag_config_manager import RAGConfigManager
        
        print("\n=== 임베딩 생성 테스트 ===")
        
        config_manager = RAGConfigManager()
        embedding_config = config_manager.get_embedding_config()
        embedding_type = embedding_config.pop('type')
        
        print(f"임베딩 타입: {embedding_type}")
        print(f"임베딩 설정: {embedding_config}")
        
        embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)
        model_name = getattr(embeddings, 'model_name', 'unknown')
        
        print(f"생성된 임베딩 모델명: {model_name}")
        print(f"임베딩 차원: {embeddings.dimension}")
        
        # 테스트 임베딩
        test_text = "안녕하세요"
        vector = embeddings.embed_query(test_text)
        print(f"테스트 임베딩 성공: {len(vector)}차원")
        
    except Exception as e:
        print(f"임베딩 생성 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config()
    test_embedding_creation()