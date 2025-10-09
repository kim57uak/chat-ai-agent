"""
Encrypted Configuration Manager
설정 데이터 암호화 관리 클래스
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from core.logging import get_logger

from ..auth.auth_manager import AuthManager

logger = get_logger("encrypted_config")


class EncryptedConfig:
    """암호화된 설정 관리자"""
    
    def __init__(self, config_path: Optional[str] = None, auth_manager: Optional[AuthManager] = None):
        if config_path is None:
            config_path = self._get_default_config_path()
        
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.auth_manager = auth_manager
        self._config_cache = {}
        
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 반환"""
        from .secure_path_manager import secure_path_manager
        
        # 보안 경로 관리자를 사용하여 안전한 경로 반환
        config_path = secure_path_manager.get_secure_config_path()
        return str(config_path)
    
    def _encrypt_data(self, data: str) -> str:
        """데이터 암호화 후 hex 문자열로 반환"""
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            raise RuntimeError("Authentication required for encryption")
        
        encrypted_bytes = self.auth_manager.encrypt_data(data)
        return encrypted_bytes.hex()
    
    def _decrypt_data(self, hex_data: str) -> str:
        """hex 문자열을 복호화"""
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            raise RuntimeError("Authentication required for decryption")
        
        encrypted_bytes = bytes.fromhex(hex_data)
        return self.auth_manager.decrypt_data(encrypted_bytes)
    
    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any]):
        """설정 파일 저장"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def set_encrypted_value(self, key: str, value: str, category: str = "general"):
        """암호화된 값 설정"""
        config = self._load_config()
        
        if "encrypted" not in config:
            config["encrypted"] = {}
        
        if category not in config["encrypted"]:
            config["encrypted"][category] = {}
        
        # 값 암호화
        encrypted_value = self._encrypt_data(value)
        config["encrypted"][category][key] = encrypted_value
        
        # 설정 저장
        self._save_config(config)
        
        # 캐시 업데이트
        cache_key = f"{category}.{key}"
        self._config_cache[cache_key] = value
        
        logger.info(f"Encrypted value set for {category}.{key}")
    
    def get_encrypted_value(self, key: str, category: str = "general", default: str = None) -> Optional[str]:
        """암호화된 값 조회"""
        cache_key = f"{category}.{key}"
        
        # 캐시에서 먼저 확인
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        config = self._load_config()
        
        try:
            encrypted_value = config["encrypted"][category][key]
            decrypted_value = self._decrypt_data(encrypted_value)
            
            # 캐시에 저장
            self._config_cache[cache_key] = decrypted_value
            
            return decrypted_value
        except KeyError:
            return default
        except Exception as e:
            logger.warning(f"Failed to decrypt {category}.{key}: {e}")
            return default
    
    def set_plain_value(self, key: str, value: Any, category: str = "general"):
        """평문 값 설정 (민감하지 않은 데이터용)"""
        config = self._load_config()
        
        if "plain" not in config:
            config["plain"] = {}
        
        if category not in config["plain"]:
            config["plain"][category] = {}
        
        config["plain"][category][key] = value
        self._save_config(config)
        
        logger.info(f"Plain value set for {category}.{key}")
    
    def get_plain_value(self, key: str, category: str = "general", default: Any = None) -> Any:
        """평문 값 조회"""
        config = self._load_config()
        
        try:
            return config["plain"][category][key]
        except KeyError:
            return default
    
    def delete_value(self, key: str, category: str = "general", encrypted: bool = True):
        """값 삭제"""
        config = self._load_config()
        
        section = "encrypted" if encrypted else "plain"
        cache_key = f"{category}.{key}"
        
        try:
            del config[section][category][key]
            self._save_config(config)
            
            # 캐시에서도 제거
            if cache_key in self._config_cache:
                del self._config_cache[cache_key]
            
            logger.info(f"Deleted {section} value for {category}.{key}")
        except KeyError:
            pass
    
    def get_all_keys(self, category: str = "general", encrypted: bool = True) -> list:
        """카테고리의 모든 키 목록 반환"""
        config = self._load_config()
        section = "encrypted" if encrypted else "plain"
        
        try:
            return list(config[section][category].keys())
        except KeyError:
            return []
    
    def clear_cache(self):
        """캐시 클리어"""
        self._config_cache.clear()
        logger.info("Config cache cleared")
    
    def migrate_from_plain_config(self, plain_config_path: str, sensitive_keys: Dict[str, list]):
        """기존 평문 설정에서 민감한 데이터를 암호화하여 마이그레이션"""
        if not Path(plain_config_path).exists():
            logger.info("No plain config file to migrate")
            return
        
        try:
            with open(plain_config_path, 'r', encoding='utf-8') as f:
                plain_config = json.load(f)
            
            migrated_count = 0
            
            for category, keys in sensitive_keys.items():
                if category not in plain_config:
                    continue
                
                for key in keys:
                    if key in plain_config[category]:
                        value = plain_config[category][key]
                        if isinstance(value, str) and value:
                            self.set_encrypted_value(key, value, category)
                            migrated_count += 1
                            logger.info(f"Migrated {category}.{key} to encrypted storage")
            
            logger.info(f"Migration completed: {migrated_count} values encrypted")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    def export_config_template(self) -> Dict[str, Any]:
        """설정 템플릿 내보내기 (민감한 데이터 제외)"""
        config = self._load_config()
        
        template = {
            "plain": config.get("plain", {}),
            "encrypted_keys": {}
        }
        
        # 암호화된 키 목록만 포함 (값은 제외)
        encrypted_section = config.get("encrypted", {})
        for category, keys in encrypted_section.items():
            template["encrypted_keys"][category] = list(keys.keys())
        
        return template