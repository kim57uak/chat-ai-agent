"""
RAG Config Manager
"""

import json
from pathlib import Path
from typing import Dict, Optional
from core.logging import get_logger

logger = get_logger("rag_config_manager")


class RAGConfigManager:
    """RAG 설정 관리자"""
    
    DEFAULT_CONFIG = {
        "embedding": {
            "type": "local",
            "model": "exp-models/dragonkue-KoEn-E5-Tiny",
            "dimension": 384,
            "enable_cache": True,
            "use_custom_model": False,
            "custom_model_path": ""
        },
        "chunking": {
            "default_strategy": "sliding_window",
            "strategies": {
                "semantic": {
                    "threshold_type": "percentile",
                    "threshold_amount": 95
                },
                "sliding_window": {
                    "window_size": 500,
                    "overlap_ratio": 0.2
                }
            }
        },
        "batch_upload": {
            "max_workers": 4,
            "max_file_size_mb": 50,
            "exclude_patterns": ["node_modules", ".git", "venv", "__pycache__"]
        },
        "retrieval": {
            "top_k": 10,
            "description": "Number of documents to retrieve from vector database"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager
        
        Args:
            config_path: Config file path (None for auto-detection)
        """
        if config_path is None:
            config_path = self._get_default_config_path()
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        logger.info(f"RAG config loaded: {self.config_path}")
    
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로"""
        try:
            from utils.config_path import config_path_manager
            config_dir = config_path_manager.get_user_config_path()
            if config_dir and config_dir.exists():
                return str(config_dir / "rag_config.json")
        except Exception as e:
            logger.warning(f"Failed to get user config path: {e}")
        
        import os
        if os.name == "nt":
            data_dir = Path.home() / "AppData" / "Local" / "ChatAIAgent"
        else:
            data_dir = Path.home() / ".chat-ai-agent"
        
        data_dir.mkdir(parents=True, exist_ok=True)
        return str(data_dir / "rag_config.json")
    
    def _load_config(self) -> Dict:
        """설정 로드"""
        if not self.config_path.exists():
            logger.info("Config not found, creating default")
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("Config loaded successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict):
        """설정 저장"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("Config saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get_embedding_config(self) -> Dict:
        """임베딩 설정 조회"""
        return self.config.get("embedding", self.DEFAULT_CONFIG["embedding"])
    
    def update_embedding_config(self, **kwargs):
        """임베딩 설정 업데이트"""
        if "embedding" not in self.config:
            self.config["embedding"] = {}
        
        self.config["embedding"].update(kwargs)
        self._save_config(self.config)
        logger.info(f"Embedding config updated: {kwargs}")
    
    def set_custom_model(self, model_path: str, dimension: int = None):
        """사용자 커스텀 모델 설정"""
        self.config["embedding"]["use_custom_model"] = True
        self.config["embedding"]["custom_model_path"] = model_path
        if dimension:
            self.config["embedding"]["dimension"] = dimension
        self._save_config(self.config)
        logger.info(f"Custom model set: {model_path}")
    
    def use_default_model(self):
        """디폴트 모델로 복귀"""
        self.config["embedding"]["use_custom_model"] = False
        self._save_config(self.config)
        logger.info("Switched to default model")
    
    def get_chunking_config(self) -> Dict:
        """청킹 설정 조회"""
        return self.config.get("chunking", self.DEFAULT_CONFIG["chunking"])
    
    def get_batch_config(self) -> Dict:
        """배치 업로드 설정 조회"""
        return self.config.get("batch_upload", self.DEFAULT_CONFIG["batch_upload"])
    
    def get_retrieval_config(self) -> Dict:
        """검색 설정 조회"""
        return self.config.get("retrieval", self.DEFAULT_CONFIG["retrieval"])
    
    def get_top_k(self) -> int:
        """Top-K 값 조회 (기본값: 10)"""
        retrieval_config = self.get_retrieval_config()
        return retrieval_config.get("top_k", 10)
