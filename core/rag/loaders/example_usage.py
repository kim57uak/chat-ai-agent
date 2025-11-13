"""
Document Loader with Chunking - Usage Examples
"""

from document_loader_factory import DocumentLoaderFactory
from ..chunking.chunking_factory import ChunkingFactory

# 예시 1: 자동 청킹 전략 (파일 확장자 기반)
def load_with_auto_chunking():
    """파일 확장자에 따라 자동으로 청킹 전략 선택"""
    
    # Python 파일 -> 코드 청킹
    documents = DocumentLoaderFactory.load_document("example.py")
    
    # Markdown 파일 -> 마크다운 청킹  
    documents = DocumentLoaderFactory.load_document("readme.md")
    
    # PDF 파일 -> 슬라이딩 윈도우 청킹
    documents = DocumentLoaderFactory.load_document("document.pdf")

# 예시 2: 수동 청킹 전략 지정
def load_with_custom_chunking():
    """특정 청킹 전략을 직접 지정"""
    
    # 시맨틱 청킹 사용 (임베딩 필요)
    from ..embeddings.embedding_factory import EmbeddingFactory
    embeddings = EmbeddingFactory.create("openai")
    
    semantic_chunker = ChunkingFactory.create(
        "semantic", 
        embeddings=embeddings,
        threshold_type="percentile",
        threshold=95
    )
    
    documents = DocumentLoaderFactory.load_document(
        "large_document.pdf", 
        chunker=semantic_chunker
    )

# 예시 3: 청킹 파라미터 조정
def load_with_custom_params():
    """청킹 파라미터를 조정하여 로드"""
    
    # 작은 청크 크기로 슬라이딩 윈도우
    documents = DocumentLoaderFactory.load_document(
        "document.txt",
        chunk_size=200,
        overlap=50
    )
    
    # 코드 파일의 청크 크기 조정
    documents = DocumentLoaderFactory.load_document(
        "large_script.py",
        chunk_size=1000,
        overlap=100
    )

if __name__ == "__main__":
    # 테스트 실행
    load_with_auto_chunking()
    load_with_custom_chunking() 
    load_with_custom_params()