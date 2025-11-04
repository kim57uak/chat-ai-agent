"""
Document Encryptor
문서 암호화/복호화 처리
"""

from typing import List
from langchain.schema import Document
from core.logging import get_logger

logger = get_logger("document_encryptor")


class DocumentEncryptor:
    """문서 암호화기"""
    
    def __init__(self, auth_manager=None):
        """
        Initialize document encryptor
        
        Args:
            auth_manager: AuthManager instance for encryption
        """
        self.auth_manager = auth_manager
        
        if not auth_manager:
            logger.warning("No auth_manager provided, encryption disabled")
    
    def encrypt_documents(self, documents: List[Document]) -> List[Document]:
        """
        Encrypt document contents
        
        Args:
            documents: List of documents
            
        Returns:
            List of documents with encrypted content
        """
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            logger.warning("Encryption not available, returning original documents")
            return documents
        
        encrypted_docs = []
        
        for doc in documents:
            try:
                # 원본 텍스트 암호화
                encrypted_content = self.auth_manager.encrypt_data(doc.page_content)
                
                # 암호화된 문서 생성
                encrypted_doc = Document(
                    page_content="[ENCRYPTED]",  # 검색용 플레이스홀더
                    metadata={
                        **doc.metadata,
                        "encrypted_content": encrypted_content,
                        "is_encrypted": True
                    }
                )
                
                encrypted_docs.append(encrypted_doc)
                
            except Exception as e:
                logger.error(f"Failed to encrypt document: {e}")
                encrypted_docs.append(doc)
        
        logger.info(f"Encrypted {len(encrypted_docs)} documents")
        return encrypted_docs
    
    def decrypt_documents(self, documents: List[Document]) -> List[Document]:
        """
        Decrypt document contents
        
        Args:
            documents: List of encrypted documents
            
        Returns:
            List of documents with decrypted content
        """
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            logger.warning("Decryption not available, returning original documents")
            return documents
        
        decrypted_docs = []
        
        for doc in documents:
            try:
                # 암호화된 문서인지 확인
                if doc.metadata.get("is_encrypted") and "encrypted_content" in doc.metadata:
                    # 복호화
                    decrypted_content = self.auth_manager.decrypt_data(
                        doc.metadata["encrypted_content"]
                    )
                    
                    # 복호화된 문서 생성
                    decrypted_doc = Document(
                        page_content=decrypted_content,
                        metadata={
                            k: v for k, v in doc.metadata.items() 
                            if k not in ["encrypted_content", "is_encrypted"]
                        }
                    )
                    
                    decrypted_docs.append(decrypted_doc)
                else:
                    # 암호화되지 않은 문서
                    decrypted_docs.append(doc)
                    
            except Exception as e:
                logger.error(f"Failed to decrypt document: {e}")
                decrypted_docs.append(doc)
        
        logger.info(f"Decrypted {len(decrypted_docs)} documents")
        return decrypted_docs
    
    def encrypt_text(self, text: str) -> bytes:
        """
        Encrypt text
        
        Args:
            text: Plain text
            
        Returns:
            Encrypted bytes
        """
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            raise RuntimeError("Authentication required for encryption")
        
        return self.auth_manager.encrypt_data(text)
    
    def decrypt_text(self, encrypted_data: bytes) -> str:
        """
        Decrypt text
        
        Args:
            encrypted_data: Encrypted bytes
            
        Returns:
            Plain text
        """
        if not self.auth_manager or not self.auth_manager.is_logged_in():
            raise RuntimeError("Authentication required for decryption")
        
        return self.auth_manager.decrypt_data(encrypted_data)
