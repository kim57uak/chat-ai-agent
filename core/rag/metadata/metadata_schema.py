"""
Metadata Schema Definition
"""

from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class MetadataSchema:
    """문서 메타데이터 스키마"""
    
    # 자동 추출 (파일 정보)
    filename: str
    file_type: str
    file_size: int = 0
    upload_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    
    # AI 자동 분석
    doc_type: str = ""  # report, contract, memo, data
    summary: str = ""
    topics: List[str] = field(default_factory=list)
    language: str = "ko"
    sentiment: str = "neutral"
    entities: List[str] = field(default_factory=list)
    
    # 사용자 입력
    category: str = ""
    tags: List[str] = field(default_factory=list)
    access_level: str = "internal"
    department: str = ""
    importance: str = "medium"
    
    # 데이터 특화 (Excel/CSV)
    data_type: str = ""
    date_range: Dict[str, Any] = field(default_factory=dict)
    row_count: int = 0
    columns: List[str] = field(default_factory=list)
    
    # 검색 최적화
    keywords: List[str] = field(default_factory=list)
    related_docs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "upload_date": self.upload_date.isoformat() if isinstance(self.upload_date, datetime) else self.upload_date,
            "last_modified": self.last_modified.isoformat() if isinstance(self.last_modified, datetime) else self.last_modified,
            "doc_type": self.doc_type,
            "summary": self.summary,
            "topics": self.topics,
            "language": self.language,
            "sentiment": self.sentiment,
            "entities": self.entities,
            "category": self.category,
            "tags": self.tags,
            "access_level": self.access_level,
            "department": self.department,
            "importance": self.importance,
            "data_type": self.data_type,
            "date_range": self.date_range,
            "row_count": self.row_count,
            "columns": self.columns,
            "keywords": self.keywords,
            "related_docs": self.related_docs,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetadataSchema":
        """Create from dictionary"""
        # datetime 변환
        if "upload_date" in data and isinstance(data["upload_date"], str):
            data["upload_date"] = datetime.fromisoformat(data["upload_date"])
        if "last_modified" in data and isinstance(data["last_modified"], str):
            data["last_modified"] = datetime.fromisoformat(data["last_modified"])
        
        return cls(**data)
