"""
Download reranker model
"""

from sentence_transformers import CrossEncoder
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.rag.reranker_constants import RerankerConstants

def download_model(model_id: str, local_name: str):
    """모델 다운로드"""
    save_path = RerankerConstants.get_models_base_path() / local_name
    save_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nDownloading {model_id}...")
    model = CrossEncoder(model_id)
    model.save(str(save_path))
    
    size_mb = sum(f.stat().st_size for f in save_path.rglob('*') if f.is_file()) / 1024 / 1024
    print(f"✓ Saved to {save_path}")
    print(f"✓ Model size: {size_mb:.1f} MB")
    return size_mb

def download_all_models():
    """기본 모델 다운로드"""
    models = [
        (RerankerConstants.DEFAULT_MODEL_HF_ID, RerankerConstants.DEFAULT_MODEL_NAME),
    ]
    
    total_size = 0
    for model_id, local_name in models:
        try:
            size = download_model(model_id, local_name)
            total_size += size
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    print(f"\n{'='*60}")
    print(f"Total: {total_size:.1f} MB")
    print(f"{'='*60}")

if __name__ == "__main__":
    print(f"=" * 60)
    print(f"Reranker Models Download")
    print(f"=" * 60)
    print(f"1. {RerankerConstants.DEFAULT_MODEL_NAME}")
    print(f"2. ms-marco-MiniLM-L-6-v2")
    print(f"=" * 60)
    download_all_models()
