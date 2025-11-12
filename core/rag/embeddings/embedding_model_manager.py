"""
Embedding Model Manager
임베딩 모델별 저장소 분리 관리
"""

import json
from typing import Dict, Optional
from pathlib import Path
from core.logging import get_logger
from ..constants import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION, DEFAULT_EMBEDDING_PATH

logger = get_logger("embedding_model_manager")


class EmbeddingModelManager:
    """임베딩 모델 관리 - 모델별 저장소 분리"""
    
    DEFAULT_MODEL = DEFAULT_EMBEDDING_MODEL
    
    def __init__(self):
        # RAG Config Manager 사용
        from ..config.rag_config_manager import RAGConfigManager
        self.rag_config = RAGConfigManager()
        logger.info("Using RAG config manager for embedding settings")
        

    
    def get_current_model(self) -> str:
        """현재 모델 반환"""
        return self.rag_config.get_current_embedding_model()
    
    def get_available_models(self) -> Dict[str, Dict]:
        """사용 가능한 모델 목록 (기본 + 커스텀)"""
        models = {}
        
        # 기본 모델 정보는 RAG 설정에서 가져오기
        try:
            default_config = self.rag_config.get_embedding_models().get(self.DEFAULT_MODEL, {})
            if default_config:
                models[self.DEFAULT_MODEL] = {
                    "name": default_config.get("name", "한국어 E5-Tiny"),
                    "dimension": default_config.get("dimension", DEFAULT_EMBEDDING_DIMENSION),
                    "provider": "sentence_transformers",
                    "description": default_config.get("description", "한국어 최적화 경량 모델"),
                    "model_path": default_config.get("model", DEFAULT_EMBEDDING_PATH)
                }
        except Exception as e:
            logger.warning(f"Failed to load default model config: {e}")
            # 폴백: 기본값 사용
            models[self.DEFAULT_MODEL] = {
                "name": "한국어 E5-Tiny",
                "dimension": DEFAULT_EMBEDDING_DIMENSION,
                "provider": "sentence_transformers",
                "description": "한국어 최적화 경량 모델",
                "model_path": DEFAULT_EMBEDDING_PATH
            }
        
        # RAG 설정에서 커스텀 모델 가져오기
        rag_models = self.rag_config.get_embedding_models()
        for model_id, model_config in rag_models.items():
            if model_id != self.DEFAULT_MODEL:  # 기본 모델 중복 방지
                # RAG 설정을 우리 형식으로 변환
                models[model_id] = {
                    "name": model_config.get("name", model_id),
                    "dimension": model_config.get("dimension", DEFAULT_EMBEDDING_DIMENSION),
                    "provider": "sentence_transformers",
                    "description": model_config.get("description", ""),
                    "model_path": model_config.get("model", model_id)
                }
        
        return models
    
    def change_model(self, new_model: str) -> tuple[bool, str]:
        """
        모델 변경 - 즉시 적용
        
        Args:
            new_model: 새 모델 ID
            
        Returns:
            (성공여부, 메시지)
        """
        available_models = self.get_available_models()
        if new_model not in available_models:
            return False, f"지원하지 않는 모델: {new_model}"
        
        current_model = self.get_current_model()
        if current_model == new_model:
            return True, "이미 선택된 모델입니다"
        
        # RAG 설정에 저장
        self.rag_config.set_current_embedding_model(new_model)
        
        return True, f"임베딩 모델이 {new_model}로 변경되었습니다.\n\n⚠️ 변경사항을 적용하려면 앱을 재시작해주세요.\n기존 벡터 데이터는 별도 보관되며, 재시작 후 새 문서를 업로드하세요."
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """모델 정보 반환"""
        return self.get_available_models().get(model_id)
    
    def get_table_name(self, model_id: Optional[str] = None) -> str:
        """모델별 테이블명 생성 (모델별 폴더 분리로 간단한 이름 사용)"""
        # 모델별 폴더로 분리되었으므로 간단한 테이블명 사용
        return "documents"
    
    def add_custom_model(self, model_id: str, model_info: Dict) -> tuple[bool, str]:
        """커스텀 모델 추가"""
        required_fields = ["name", "dimension"]
        for field in required_fields:
            if field not in model_info:
                return False, f"필수 필드 누락: {field}"
        
        # RAG 설정에 추가
        rag_model_config = {
            "type": "local",
            "model": model_info.get("model_path", model_id),
            "name": model_info["name"],
            "dimension": model_info["dimension"],
            "description": model_info.get("description", ""),
            "enable_cache": True
        }
        
        self.rag_config.add_embedding_model(model_id, rag_model_config)
        return True, f"커스텀 모델 '{model_id}' 추가됨"
    
    def remove_custom_model(self, model_id: str) -> tuple[bool, str]:
        """커스텀 모델 제거"""
        if model_id == self.DEFAULT_MODEL:
            return False, "기본 모델은 제거할 수 없습니다"
        
        available_models = self.get_available_models()
        if model_id not in available_models or model_id == self.DEFAULT_MODEL:
            return False, f"커스텀 모델 '{model_id}'를 찾을 수 없습니다"
        
        # 현재 모델이 제거되는 모델이면 기본모델로 변경
        if self.get_current_model() == model_id:
            self.rag_config.set_current_embedding_model(self.DEFAULT_MODEL)
        
        # RAG 설정에서 제거
        self.rag_config.delete_embedding_model(model_id)
        return True, f"커스텀 모델 '{model_id}' 제거됨"
    
    def list_model_data(self) -> Dict[str, Dict]:
        """모델별 데이터 현황"""
        result = {}
        current_model = self.get_current_model()
        available_models = self.get_available_models()
        
        for model_id in available_models:
            try:
                from ..vector_store.lancedb_store import LanceDBStore
                
                table_name = self.get_table_name(model_id)
                store = LanceDBStore(table_name=table_name)
                
                doc_count = 0
                if store.db and table_name in store.db.table_names():
                    table = store.db.open_table(table_name)
                    doc_count = table.count_rows()
                
                result[model_id] = {
                    "document_count": doc_count,
                    "is_current": model_id == current_model,
                    "model_info": available_models[model_id],
                    "table_name": table_name
                }
            except Exception as e:
                result[model_id] = {
                    "document_count": 0,
                    "error": str(e),
                    "is_current": model_id == current_model,
                    "table_name": self.get_table_name(model_id)
                }
        
        return result
    
    def requires_restart(self, new_model: str) -> bool:
        """모델 변경 시 재시작 필요 여부 - 안전성을 위해 재시작 요구"""
        current_model = self.get_current_model()
        return current_model != new_model