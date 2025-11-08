"""
RAG Storage Manager Demo
실제 사용 예시
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.rag.storage.rag_storage_manager import RAGStorageManager
from langchain.schema import Document
from core.logging import get_logger

logger = get_logger("rag_demo")


def demo_basic_usage():
    """기본 사용법 데모"""
    
    print("\n" + "="*60)
    print("RAG Storage Manager - Basic Usage Demo")
    print("="*60 + "\n")
    
    # 1. 초기화
    print("1️⃣  Initializing RAG Storage Manager...")
    manager = RAGStorageManager()
    print("   ✅ Manager initialized\n")
    
    # 2. 토픽 생성
    print("2️⃣  Creating topics...")
    
    python_topic = manager.create_topic(
        name="Python Programming",
        description="Python 프로그래밍 관련 문서"
    )
    print(f"   ✅ Created topic: Python Programming ({python_topic})")
    
    django_topic = manager.create_topic(
        name="Django Framework",
        parent_id=python_topic,
        description="Django 웹 프레임워크"
    )
    print(f"   ✅ Created sub-topic: Django Framework ({django_topic})\n")
    
    # 3. 문서 추가
    print("3️⃣  Adding documents...")
    
    doc1_id = manager.create_document(
        topic_id=python_topic,
        filename="python_basics.txt",
        file_path="/docs/python_basics.txt",
        file_type="text",
        file_size=2048,
        chunking_strategy="sliding_window"
    )
    print(f"   ✅ Added document: python_basics.txt ({doc1_id})")
    
    doc2_id = manager.create_document(
        topic_id=django_topic,
        filename="django_tutorial.md",
        file_path="/docs/django_tutorial.md",
        file_type="markdown",
        file_size=4096,
        chunking_strategy="semantic"
    )
    print(f"   ✅ Added document: django_tutorial.md ({doc2_id})\n")
    
    # 4. 청크 추가
    print("4️⃣  Adding chunks...")
    
    python_chunks = [
        Document(
            page_content="Python is a high-level, interpreted programming language.",
            metadata={"source": "python_basics.txt", "page": 1}
        ),
        Document(
            page_content="Python supports multiple programming paradigms.",
            metadata={"source": "python_basics.txt", "page": 1}
        ),
        Document(
            page_content="Python has a comprehensive standard library.",
            metadata={"source": "python_basics.txt", "page": 2}
        )
    ]
    
    python_embeddings = [[0.1] * 384 for _ in python_chunks]
    
    chunk_ids = manager.add_chunks(
        doc_id=doc1_id,
        chunks=python_chunks,
        embeddings=python_embeddings,
        chunking_strategy="sliding_window"
    )
    print(f"   ✅ Added {len(chunk_ids)} chunks for python_basics.txt")
    
    django_chunks = [
        Document(
            page_content="Django is a high-level Python web framework.",
            metadata={"source": "django_tutorial.md", "section": "intro"}
        ),
        Document(
            page_content="Django follows the MTV architectural pattern.",
            metadata={"source": "django_tutorial.md", "section": "architecture"}
        )
    ]
    
    django_embeddings = [[0.2] * 384 for _ in django_chunks]
    
    chunk_ids = manager.add_chunks(
        doc_id=doc2_id,
        chunks=django_chunks,
        embeddings=django_embeddings,
        chunking_strategy="semantic"
    )
    print(f"   ✅ Added {len(chunk_ids)} chunks for django_tutorial.md\n")
    
    # 5. 통계 조회
    print("5️⃣  Getting statistics...")
    stats = manager.get_statistics()
    print(f"   📊 Total topics: {stats['total_topics']}")
    print(f"   📊 Total documents: {stats['total_documents']}")
    
    for topic in stats['topics']:
        print(f"      - {topic['name']}: {topic['document_count']} documents")
    print()
    
    # 6. 검색
    print("6️⃣  Searching chunks...")
    query_vector = [0.15] * 384
    
    results = manager.search_chunks(
        query="Python programming",
        k=3,
        query_vector=query_vector
    )
    print(f"   🔍 Found {len(results)} chunks (all topics)")
    
    results = manager.search_chunks(
        query="Django framework",
        k=2,
        topic_id=django_topic,
        query_vector=query_vector
    )
    print(f"   🔍 Found {len(results)} chunks (Django topic only)\n")
    
    # 7. 정리
    print("7️⃣  Cleanup...")
    
    success = manager.delete_document(doc2_id)
    print(f"   🗑️  Deleted document: django_tutorial.md ({success})")
    
    success = manager.delete_topic(python_topic)
    print(f"   🗑️  Deleted topic: Python Programming ({success})\n")
    
    stats = manager.get_statistics()
    print(f"   📊 Final: {stats['total_topics']} topics, {stats['total_documents']} documents\n")
    
    manager.close()
    print("   ✅ Manager closed\n")
    
    print("="*60)
    print("✅ Demo completed successfully!")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        demo_basic_usage()
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")
