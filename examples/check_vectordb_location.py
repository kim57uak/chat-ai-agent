"""
Vector DB 위치 확인
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.rag.vector_store.lancedb_store import LanceDBStore
from core.rag.storage.topic_database import TopicDatabase


def main():
    """Vector DB 및 SQLite 위치 확인"""
    print("\n" + "="*60)
    print("RAG 데이터베이스 위치 확인")
    print("="*60 + "\n")
    
    # LanceDB 위치
    print("📊 Vector DB (LanceDB):")
    vector_store = LanceDBStore()
    print(f"   경로: {vector_store.db_path}")
    print(f"   테이블: {vector_store.table_name}")
    
    if vector_store.db:
        tables = vector_store.db.table_names()
        print(f"   테이블 목록: {tables}")
    else:
        print("   ⚠️  LanceDB 연결 실패")
    
    print()
    
    # SQLite 위치
    print("📁 Metadata DB (SQLite):")
    topic_db = TopicDatabase()
    print(f"   경로: {topic_db.db_path}")
    
    # 통계
    topics = topic_db.get_all_topics()
    print(f"   토픽 수: {len(topics)}")
    
    total_docs = 0
    for topic in topics:
        docs = topic_db.get_documents_by_topic(topic['id'])
        total_docs += len(docs)
    
    print(f"   문서 수: {total_docs}")
    
    print()
    
    # 설정 파일 위치
    print("⚙️  설정 파일:")
    from core.rag.config.rag_config_manager import RAGConfigManager
    config_manager = RAGConfigManager()
    print(f"   경로: {config_manager.config_path}")
    
    print("\n" + "="*60)
    print("✅ 확인 완료")
    print("="*60 + "\n")
    
    # 파일 탐색기로 열기 (선택)
    print("💡 Tip: 위 경로를 복사하여 파일 탐색기에서 열 수 있습니다.")
    print()


if __name__ == "__main__":
    main()
