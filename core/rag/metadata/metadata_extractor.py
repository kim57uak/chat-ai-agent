"""
Metadata Extractor
파일에서 메타데이터 자동 추출
"""

from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from core.logging import get_logger
from .metadata_schema import MetadataSchema

logger = get_logger("metadata_extractor")


class MetadataExtractor:
    """메타데이터 추출기"""
    
    @staticmethod
    def extract_from_file(file_path: str) -> MetadataSchema:
        """
        Extract metadata from file
        
        Args:
            file_path: File path
            
        Returns:
            MetadataSchema object
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 기본 파일 정보 추출
        stat = path.stat()
        
        metadata = MetadataSchema(
            filename=path.name,
            file_type=path.suffix.lower(),
            file_size=stat.st_size,
            upload_date=datetime.now(),
            last_modified=datetime.fromtimestamp(stat.st_mtime)
        )
        
        logger.info(f"Extracted metadata from: {path.name}")
        return metadata
    
    @staticmethod
    def extract_from_content(
        content: str, 
        filename: str,
        llm = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from content using LLM
        
        Args:
            content: Document content
            filename: File name
            llm: LLM instance for AI analysis
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "filename": filename,
            "doc_type": MetadataExtractor._infer_doc_type(filename),
            "language": MetadataExtractor._detect_language(content),
        }
        
        # LLM을 사용한 AI 분석 (선택적)
        if llm:
            try:
                ai_metadata = MetadataExtractor._analyze_with_llm(content, llm)
                metadata.update(ai_metadata)
            except Exception as e:
                logger.warning(f"LLM analysis failed: {e}")
        
        return metadata
    
    @staticmethod
    def _infer_doc_type(filename: str) -> str:
        """
        Infer document type from filename
        
        Args:
            filename: File name
            
        Returns:
            Document type
        """
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ["report", "보고서"]):
            return "report"
        elif any(word in filename_lower for word in ["contract", "계약"]):
            return "contract"
        elif any(word in filename_lower for word in ["memo", "메모"]):
            return "memo"
        elif any(word in filename_lower for word in ["data", "데이터", ".csv", ".xlsx"]):
            return "data"
        else:
            return "document"
    
    @staticmethod
    def _detect_language(content: str) -> str:
        """
        Detect language from content
        
        Args:
            content: Document content
            
        Returns:
            Language code (ko, en, mixed)
        """
        if not content:
            return "unknown"
        
        # 한글 문자 비율 계산
        korean_chars = sum(1 for c in content if '\uac00' <= c <= '\ud7a3')
        total_chars = len(content.replace(" ", "").replace("\n", ""))
        
        if total_chars == 0:
            return "unknown"
        
        korean_ratio = korean_chars / total_chars
        
        if korean_ratio > 0.5:
            return "ko"
        elif korean_ratio > 0.1:
            return "mixed"
        else:
            return "en"
    
    @staticmethod
    def _analyze_with_llm(content: str, llm) -> Dict[str, Any]:
        """
        Analyze content with LLM
        
        Args:
            content: Document content
            llm: LLM instance
            
        Returns:
            AI-generated metadata
        """
        # 내용이 너무 길면 앞부분만 사용
        sample = content[:1000] if len(content) > 1000 else content
        
        prompt = f"""Analyze this document and extract metadata in JSON format:

Document:
{sample}

Extract:
- summary: Brief summary (max 100 chars)
- topics: List of 3-5 main topics
- sentiment: positive/neutral/negative
- entities: List of key entities (people, places, organizations)

Return only valid JSON."""
        
        try:
            from langchain.schema import HumanMessage
            response = llm.invoke([HumanMessage(content=prompt)])
            
            # JSON 파싱 시도
            import json
            result = json.loads(response.content)
            
            logger.info("LLM metadata analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            return {}
