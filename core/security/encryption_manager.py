"""
Encryption Manager for secure data handling.
Implements AES-256 encryption with PBKDF2 key derivation.
"""

import os
import gc
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import keyring
from core.logging import get_logger

logger = get_logger('security.encryption')


class EncryptionManager:
    """Manages encryption keys and data encryption/decryption."""
    
    APP_NAME = "chat-ai-agent"
    SALT_KEY = "encryption_salt"
    DEK_KEY = "data_encryption_key"
    
    def __init__(self):
        self.master_key: Optional[bytes] = None
        self.dek: Optional[bytes] = None
        self.salt: Optional[bytes] = None
        
    def setup_first_time(self, password: str) -> bool:
        """
        최초 설정: 비밀번호 → 마스터키 → DEK 생성 → 키체인 저장
        
        Args:
            password: 사용자 비밀번호
            
        Returns:
            bool: 설정 성공 여부
        """
        try:
            # 1. Salt 생성
            self.salt = os.urandom(32)
            
            # 2. 비밀번호로 마스터키 생성
            self.master_key = self._derive_master_key(password, self.salt)
            
            # 3. DEK 생성
            self.dek = os.urandom(32)
            
            # 4. 마스터키로 DEK 암호화하여 키체인에 저장
            encrypted_dek = self._encrypt_with_master_key(self.dek)
            keyring.set_password(self.APP_NAME, self.DEK_KEY, encrypted_dek.hex())
            keyring.set_password(self.APP_NAME, self.SALT_KEY, self.salt.hex())
            
            # 5. 비밀번호 메모리에서 제거
            password = None
            gc.collect()
            
            return True
            
        except Exception as e:
            logger.error(f"Encryption setup failed", exc_info=True)
            self._clear_memory()
            return False
            
    def login(self, password: str) -> bool:
        """
        로그인: 비밀번호 → 마스터키 생성 → DEK 복호화
        
        Args:
            password: 사용자 비밀번호
            
        Returns:
            bool: 로그인 성공 여부
        """
        # 이미 로그인된 상태라면 로그아웃 후 진행
        if self.is_logged_in():
            self.logout()
            
        try:
            # 1. 키체인에서 salt와 암호화된 DEK 가져오기
            salt_hex = keyring.get_password(self.APP_NAME, self.SALT_KEY)
            encrypted_dek_hex = keyring.get_password(self.APP_NAME, self.DEK_KEY)
            
            if not salt_hex or not encrypted_dek_hex:
                return False
                
            self.salt = bytes.fromhex(salt_hex)
            encrypted_dek = bytes.fromhex(encrypted_dek_hex)
            
            # 2. 비밀번호로 마스터키 재생성
            self.master_key = self._derive_master_key(password, self.salt)
            
            # 3. 마스터키로 DEK 복호화
            self.dek = self._decrypt_with_master_key(encrypted_dek)
            
            # 4. DEK 유효성 검증
            if not self.dek or len(self.dek) != 32:
                raise ValueError("Invalid DEK recovered")
            
            # 5. 비밀번호 즉시 제거
            password = None
            gc.collect()
            
            return True
            
        except Exception as e:
            logger.warning("Login failed - invalid credentials")
            self._clear_memory()
            return False
            
    def is_setup_required(self) -> bool:
        """최초 설정이 필요한지 확인"""
        salt_hex = keyring.get_password(self.APP_NAME, self.SALT_KEY)
        dek_hex = keyring.get_password(self.APP_NAME, self.DEK_KEY)
        return not (salt_hex and dek_hex)
        
    def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return self.master_key is not None and self.dek is not None
        
    def encrypt_data(self, data: str) -> bytes:
        """
        DEK로 실제 데이터 암호화
        
        Args:
            data: 암호화할 문자열
            
        Returns:
            bytes: 암호화된 데이터 (IV + 암호화된 데이터)
        """
        if not self.is_logged_in():
            raise RuntimeError("Not logged in")
            
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.dek), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        padded_data = self._pad(data.encode('utf-8'))
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        return iv + encrypted
        
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """
        DEK로 실제 데이터 복호화
        
        Args:
            encrypted_data: 암호화된 데이터
            
        Returns:
            str: 복호화된 문자열
        """
        if not self.is_logged_in():
            raise RuntimeError("Not logged in")
            
        iv = encrypted_data[:16]
        encrypted = encrypted_data[16:]
        
        cipher = Cipher(algorithms.AES(self.dek), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        return self._unpad(padded_data).decode('utf-8')
        
    def logout(self):
        """로그아웃: 메모리의 모든 키 제거"""
        self._clear_memory()
        
    def reset_password(self, new_password: str) -> bool:
        """
        비밀번호 재설정 (기존 데이터는 복구 불가)
        
        Args:
            new_password: 새로운 비밀번호
            
        Returns:
            bool: 재설정 성공 여부
        """
        try:
            # 기존 키 삭제
            keyring.delete_password(self.APP_NAME, self.SALT_KEY)
            keyring.delete_password(self.APP_NAME, self.DEK_KEY)
        except:
            pass  # 키가 없어도 무시
            
        # 새로운 키로 설정
        return self.setup_first_time(new_password)
        
    def _derive_master_key(self, password: str, salt: bytes) -> bytes:
        """PBKDF2로 마스터키 생성"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))
        
    def _encrypt_with_master_key(self, data: bytes) -> bytes:
        """마스터키로 데이터 암호화"""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.master_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        padded_data = self._pad(data)
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        return iv + encrypted
        
    def _decrypt_with_master_key(self, encrypted_data: bytes) -> bytes:
        """마스터키로 데이터 복호화"""
        try:
            iv = encrypted_data[:16]
            encrypted = encrypted_data[16:]
            
            cipher = Cipher(algorithms.AES(self.master_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            padded_data = decryptor.update(encrypted) + decryptor.finalize()
            return self._unpad(padded_data)
        except Exception:
            # 복호화 실패 시 잘못된 비밀번호로 간주
            raise ValueError("Invalid password or corrupted data")
        
    def _pad(self, data: bytes) -> bytes:
        """PKCS7 패딩"""
        padding_length = 16 - (len(data) % 16)
        padding = bytes([padding_length] * padding_length)
        return data + padding
        
    def _unpad(self, padded_data: bytes) -> bytes:
        """PKCS7 패딩 제거"""
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]
        
    def _clear_memory(self):
        """메모리의 모든 키 제거"""
        self.master_key = None
        self.dek = None
        self.salt = None
        gc.collect()