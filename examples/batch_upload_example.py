"""
Batch Upload Example
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.rag.batch.batch_uploader import BatchUploader
from core.rag.storage.rag_storage_manager import RAGStorageManager
from core.rag.embeddings.embedding_factory import EmbeddingFactory
from core.rag.config.rag_config_manager import RAGConfigManager


def example_batch_upload():
    """배치 업로드 예시"""
    print("\n" + "="*60)
    print("Batch Upload Example")
    print("="*60 + "\n")
    
    # 1. 설정 로드
    config_manager = RAGConfigManager()
    embedding_config = config_manager.get_embedding_config()
    batch_config = config_manager.get_batch_config()
    
    print(f"📝 Batch config:")
    print(f"   Max workers: {batch_config['max_workers']}")
    print(f"   Max file size: {batch_config['max_file_size_mb']}MB")
    print(f"   Exclude: {batch_config['exclude_patterns']}\n")
    
    # 2. 임베딩 모델 생성
    embedding_type = embedding_config.pop('type')
    embeddings = EmbeddingFactory.create(embedding_type, **embedding_config)
    print(f"✅ Embedding model: {embedding_type}\n")
    
    # 3. 스토리지 초기화
    storage = RAGStorageManager()
    print(f"✅ Storage initialized\n")
    
    # 4. 토픽 생성
    topic_id = storage.create_topic(
        name="Example Project",
        description="Example batch upload"
    )
    print(f"✅ Topic created: {topic_id}\n")
    
    # 5. 배치 업로더 생성
    uploader = BatchUploader(storage, embeddings, batch_config)
    
    # 6. 진행 상황 콜백
    def on_progress(current, total, percentage, stats):
        print(f"   📊 Progress: {current}/{total} ({percentage:.1f}%)")
        print(f"      Chunks: {stats['total_chunks']}, Speed: {stats['files_per_second']:.2f} files/s")
    
    def on_complete(stats):
        print(f"\n✅ Upload completed!")
        print(f"   Processed: {stats['processed_files']}/{stats['total_files']}")
        print(f"   Failed: {stats['failed_files']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Elapsed: {stats['elapsed_seconds']:.2f}s")
        
        if stats['errors']:
            print(f"\n⚠️  Errors:")
            for error in stats['errors'][:5]:  # 최대 5개만 표시
                print(f"      - {Path(error['file']).name}: {error['error']}")
    
    # 7. 업로드 (실제 폴더 경로 지정 필요)
    folder_path = "/path/to/your/folder"
    
    print(f"📁 Folder: {folder_path}")
    print(f"🚀 Starting batch upload...\n")
    
    # stats = uploader.upload_folder(
    #     folder_path,
    #     topic_id,
    #     on_progress=on_progress,
    #     on_complete=on_complete
    # )
    
    print("\n💡 Usage:")
    print("   1. Set folder_path to your target folder")
    print("   2. Uncomment the upload_folder() call")
    print("   3. Run this script")
    print()


if __name__ == "__main__":
    example_batch_upload()
