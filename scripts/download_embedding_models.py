"""
Embedding Models Downloader
Downloads top 5 code RAG embedding models to local directory
"""
from sentence_transformers import SentenceTransformer
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Top 5 models for code RAG with multilingual support
MODELS = {
    "intfloat/multilingual-e5-large": {
        "size": "2.24GB",
        "dims": 1024,
        "reason": "MTEB #1 multilingual, 94+ languages including Korean"
    },
    "BAAI/bge-m3": {
        "size": "2.27GB", 
        "dims": 1024,
        "reason": "C-MTEB #1, hybrid retrieval, 100+ languages"
    },
    "jinaai/jina-embeddings-v2-base-code": {
        "size": "560MB",
        "dims": 768,
        "reason": "Code-specific, 8K context, multilingual"
    },
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": {
        "size": "1.11GB",
        "dims": 768,
        "reason": "50+ languages, proven multilingual performance"
    },
    "intfloat/multilingual-e5-base": {
        "size": "1.11GB",
        "dims": 768,
        "reason": "E5 family, balanced size/performance, Korean support"
    }
}

def download_models(base_path: str = "./models/embeddings"):
    """Download all embedding models to specified directory"""
    base_dir = Path(base_path)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"📁 Download directory: {base_dir.absolute()}")
    logger.info(f"📦 Total models: {len(MODELS)}\n")
    
    results = []
    
    for idx, (model_name, info) in enumerate(MODELS.items(), 1):
        logger.info(f"[{idx}/{len(MODELS)}] {model_name}")
        logger.info(f"  Size: {info['size']} | Dims: {info['dims']}")
        logger.info(f"  Reason: {info['reason']}")
        
        try:
            model_path = base_dir / model_name.replace("/", "_")
            
            # Download model (uses default cache)
            model = SentenceTransformer(model_name)
            
            # Save to specific path
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
    logger.info(f"✅ Success: {success}/{len(MODELS)}")
    logger.info(f"❌ Failed: {len(MODELS) - success}/{len(MODELS)}")
    logger.info(f"📁 Location: {base_dir.absolute()}")
    
    return results

if __name__ == "__main__":
    import sys
    
    # Custom path from command line argument
    download_path = sys.argv[1] if len(sys.argv) > 1 else "./models/embeddings"
    
    print("\n🚀 Starting embedding models download...")
    print(f"📍 Target directory: {download_path}\n")
    
    results = download_models(download_path)
    
    print("\n✨ Download complete!")
