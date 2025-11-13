#!/usr/bin/env python3
"""
임베딩 모델 디버깅 스크립트
현재 사용 중인 모델과 실제 임베딩 생성 모델 확인
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_embedding_model():
    """임베딩 모델 상태 디버깅"""
    print("🔍 임베딩 모델 디버깅 시작...")
    print("=" * 50)
    
    # 1. 설정 파일 확인
    print("📋 1. 설정 파일 확인")
    try:
        from core.rag.embeddings.embedding_model_manager import EmbeddingModelManager
        manager = EmbeddingModelManager()
        
        current_model = manager.get_current_model()
        available_models = manager.get_available_models()
        
        print(f"   현재 모델: {current_model}")
        print(f"   사용 가능한 모델: {list(available_models.keys())}")
        
        if current_model in available_models:
            model_info = available_models[current_model]
            print(f"   모델 정보: {model_info}")
        else:
            print(f"   ❌ 현재 모델 '{current_model}'이 사용 가능한 모델 목록에 없음!")
            
    except Exception as e:
        print(f"   ❌ 설정 파일 로드 실패: {e}")
    
    print()
    
    # 2. 임베딩 팩토리 확인
    print("🏭 2. 임베딩 팩토리 확인")
    try:
        from core.rag.embeddings.embedding_factory import EmbeddingFactory
        
        # 현재 모델로 임베딩 생성 시도
        embeddings = EmbeddingFactory.create_embeddings()
        print(f"   생성된 임베딩 클래스: {type(embeddings).__name__}")
        print(f"   임베딩 모듈: {type(embeddings).__module__}")
        
        # 테스트 임베딩 생성
        test_text = "테스트 문장입니다"
        test_vector = embeddings.embed_query(test_text)
        print(f"   테스트 벡터 차원: {len(test_vector)}")
        print(f"   벡터 샘플: {test_vector[:5]}...")
        
    except Exception as e:
        print(f"   ❌ 임베딩 생성 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 3. LanceDB 테이블 확인
    print("🗄️ 3. LanceDB 테이블 확인")
    try:
        from core.rag.vector_store.lancedb_store import LanceDBStore
        
        # 현재 모델 기반 테이블명 확인
        store = LanceDBStore()
        print(f"   현재 테이블명: {store.table_name}")
        
        if store.db:
            table_names = store.db.table_names()
            print(f"   존재하는 테이블들: {table_names}")
            
            if store.table_name in table_names:
                table = store.db.open_table(store.table_name)
                doc_count = table.count_rows()
                print(f"   현재 테이블 문서 수: {doc_count}")
            else:
                print(f"   ❌ 현재 테이블 '{store.table_name}'이 존재하지 않음!")
        else:
            print("   ❌ LanceDB 연결 실패!")
            
    except Exception as e:
        print(f"   ❌ LanceDB 확인 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # 4. 설정 파일 내용 직접 확인
    print("📄 4. 설정 파일 내용 확인")
    try:
        import json
        
        # embedding_config.json 확인
        config_path = Path("embedding_config.json")
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"   embedding_config.json: {config}")
        else:
            print("   ❌ embedding_config.json 파일이 없음!")
        
        # config.json도 확인
        main_config_path = Path("config.json")
        if main_config_path.exists():
            with open(main_config_path, 'r', encoding='utf-8') as f:
                main_config = json.load(f)
            print(f"   config.json 모델 관련: {main_config.get('models', {})}")
        
    except Exception as e:
        print(f"   ❌ 설정 파일 읽기 실패: {e}")
    
    print()
    
    # 5. 실제 임베딩 테스트
    print("🧪 5. 실제 임베딩 테스트")
    try:
        # 지정된 모델로 직접 임베딩 생성
        target_model = "jinaai_jina-embeddings-v2-base-code"
        print(f"   타겟 모델: {target_model}")
        
        embeddings = EmbeddingFactory.create_embeddings(target_model)
        print(f"   생성된 임베딩 타입: {type(embeddings).__name__}")
        
        test_vector = embeddings.embed_query("테스트")
        print(f"   벡터 차원: {len(test_vector)}")
        
        # 기본 모델과 비교
        default_embeddings = EmbeddingFactory.create_embeddings("dragonkue-KoEn-E5-Tiny")
        default_vector = default_embeddings.embed_query("테스트")
        print(f"   기본 모델 벡터 차원: {len(default_vector)}")
        
        if len(test_vector) != len(default_vector):
            print("   ✅ 모델이 다르게 동작함 (차원이 다름)")
        else:
            print("   ⚠️ 모델이 같게 동작함 (차원이 같음)")
            
    except Exception as e:
        print(f"   ❌ 임베딩 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🔍 디버깅 완료!")

if __name__ == "__main__":
    debug_embedding_model()