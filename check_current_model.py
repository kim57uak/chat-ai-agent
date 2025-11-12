#!/usr/bin/env python3
"""
현재 사용 중인 임베딩 모델 정확히 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_current_model():
    """현재 모델 상태 정확히 확인"""
    print("🔍 현재 임베딩 모델 상태 확인...")
    print("=" * 60)
    
    # 1. EmbeddingModelManager 확인
    print("📋 1. EmbeddingModelManager 상태")
    try:
        from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
        manager = EmbeddingModelManager()
        
        current_model = manager.get_current_model()
        available_models = manager.get_available_models()
        
        print(f"   현재 모델: {current_model}")
        print(f"   사용 가능한 모델:")
        for model_id, info in available_models.items():
            is_current = "✅ (현재)" if model_id == current_model else "   "
            print(f"   {is_current} {model_id}: {info.get('name', 'Unknown')}")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    print()
    
    # 2. 실제 테이블명 확인
    print("🗄️ 2. LanceDB 테이블 상태")
    try:
        from core.rag.vector_store.lancedb_store import LanceDBStore
        
        store = LanceDBStore()
        print(f"   현재 사용 중인 테이블: {store.table_name}")
        
        if store.db:
            all_tables = store.db.table_names()
            print(f"   존재하는 모든 테이블:")
            for table in all_tables:
                if table == store.table_name:
                    print(f"   ✅ {table} (현재 활성)")
                else:
                    print(f"      {table}")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    print()
    
    # 3. 실제 임베딩 생성 테스트
    print("🧪 3. 실제 임베딩 생성 테스트")
    try:
        from core.rag.embeddings.embedding_factory import EmbeddingFactory
        
        # 현재 설정된 모델로 임베딩 생성
        embeddings = EmbeddingFactory.create_embeddings()
        test_vector = embeddings.embed_query("테스트")
        
        print(f"   실제 사용된 임베딩 클래스: {type(embeddings).__name__}")
        print(f"   생성된 벡터 차원: {len(test_vector)}")
        
        # 차원으로 모델 추정
        if len(test_vector) == 384:
            print(f"   → 한국어 E5-Tiny 모델 사용 중 (384차원)")
        elif len(test_vector) == 768:
            print(f"   → Jina AI 모델 사용 중 (768차원)")
        elif len(test_vector) == 1536:
            print(f"   → OpenAI Small 모델 사용 중 (1536차원)")
        else:
            print(f"   → 알 수 없는 모델 (차원: {len(test_vector)})")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 4. 설정 파일들 확인
    print("📄 4. 설정 파일 확인")
    
    # embedding_config.json
    embedding_config_path = Path("embedding_config.json")
    if embedding_config_path.exists():
        try:
            import json
            with open(embedding_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"   embedding_config.json 현재 모델: {config.get('current_model', 'None')}")
            print(f"   커스텀 모델 수: {len(config.get('custom_models', {}))}")
        except Exception as e:
            print(f"   ❌ embedding_config.json 읽기 실패: {e}")
    else:
        print("   ❌ embedding_config.json 파일 없음!")
    
    print()
    
    # 5. RAG 관리 메뉴에서 사용하는 모델 확인
    print("🎛️ 5. RAG 관리 시스템에서 사용하는 모델")
    try:
        # RAG 매니저가 사용하는 모델 확인
        from core.rag.rag_manager import RAGManager
        
        rag_manager = RAGManager()
        # RAG 매니저의 임베딩 모델 확인
        if hasattr(rag_manager, 'embeddings') and rag_manager.embeddings:
            print(f"   RAG 매니저 임베딩 클래스: {type(rag_manager.embeddings).__name__}")
            test_vector = rag_manager.embeddings.embed_query("테스트")
            print(f"   RAG 매니저 벡터 차원: {len(test_vector)}")
        else:
            print("   RAG 매니저에 임베딩이 설정되지 않음")
            
    except Exception as e:
        print(f"   ❌ RAG 매니저 확인 실패: {e}")
    
    print()
    print("🔍 확인 완료!")

if __name__ == "__main__":
    check_current_model()