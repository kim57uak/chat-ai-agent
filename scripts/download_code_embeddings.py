"""
Download Code-Specific Embedding Models
"""
from sentence_transformers import SentenceTransformer
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 코드 전용 임베딩 모델
CODE_MODELS = {
    "jinaai/jina-embeddings-v2-base-code": {
        "size": "560MB",
        "dims": 768,
        "reason": "Code-specific, 8K context, multilingual"
    },
    "nomic-ai/nomic-embed-text-v1.5": {
        "size": "548MB",
        "dims": 768,
        "reason": "Fast, long context (8K), code + text"
    },
    "BAAI/bge-base-en-v1.5": {
        "size": "438MB",
        "dims": 768,
        "reason": "Fast, good for code search"
    },
    "sentence-transformers/all-mpnet-base-v2": {
        "size": "438MB",
        "dims": 768,
        "reason": "Balanced, code + text"
    }
}

def download_models(base_path: str = "/Users/dolpaks/Downloads/ai_file_folder/config/models"):
    """Download code embedding models"""
    base_dir = Path(base_path)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📁 Download directory: {base_dir.absolute()}")
    logger.info(f"📦 Total models: {len(CODE_MODELS)}\n")
    
    results = []
    
    for idx, (model_name, info) in enumerate(CODE_MODELS.items(), 1):
        logger.info(f"[{idx}/{len(CODE_MODELS)}] {model_name}")
        logger.info(f"  Size: {info['size']} | Dims: {info['dims']}")
        logger.info(f"  Reason: {info['reason']}")
        
        try:
            model_path = base_dir / model_name.replace("/", "_")
            
            # Download
            model = SentenceTransformer(model_name)
            
            # Save
            model.save(str(model_path))
            
            logger.info(f"  ✅ Downloaded to: {model_path}\n")
            results.append({"model": model_name, "status": "success", "path": str(model_path)})
            
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}\n")
            results.append({"model": model_name, "status": "failed", "error": str(e)})
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 Download Summary")
    logger.info("=" * 60)
    success = sum(1 for r in results if r["status"] == "success")
    logger.info(f"✅ Success: {success}/{len(CODE_MODELS)}")
    logger.info(f"❌ Failed: {len(CODE_MODELS) - success}/{len(CODE_MODELS)}")
    logger.info(f"📁 Location: {base_dir.absolute()}")
    
    return results

if __name__ == "__main__":
    print("\n🚀 Starting code embedding models download...\n")
    results = download_models()
    print("\n✨ Download complete!")
