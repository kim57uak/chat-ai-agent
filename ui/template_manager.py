"""템플릿 관리 시스템"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class Template:
    """템플릿 데이터 모델"""
    
    def __init__(self, name: str, content: str, category: str = "기타", 
                 variables: List[str] = None, favorite: bool = False):
        self.name = name
        self.content = content
        self.category = category
        self.variables = variables or []
        self.favorite = favorite
        self.created_at = datetime.now().isoformat()
        self.used_count = 0
        self.last_used = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'content': self.content,
            'category': self.category,
            'variables': self.variables,
            'favorite': self.favorite,
            'created_at': self.created_at,
            'used_count': self.used_count,
            'last_used': self.last_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        template = cls(
            name=data['name'],
            content=data['content'],
            category=data.get('category', '기타'),
            variables=data.get('variables', []),
            favorite=data.get('favorite', False)
        )
        template.created_at = data.get('created_at', datetime.now().isoformat())
        template.used_count = data.get('used_count', 0)
        template.last_used = data.get('last_used')
        return template


class TemplateManager(QObject):
    """템플릿 관리자"""
    
    templates_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.templates: List[Template] = []
        self.templates_file = 'templates.json'
        self.categories = ['💼 업무용', '🔍 분석/리서치', '📊 데이터 처리', '💻 코딩 도움', '🎯 기타']
        self.load_templates()
        self._create_default_templates()
    
    def _create_default_templates(self):
        """기본 템플릿 생성"""
        if not self.templates:
            defaults = [
                Template(
                    "데이터 분석 요청",
                    "다음 데이터를 분석해주세요:\n\n파일: {파일명}\n분석 목적: {목적}\n\n다음 항목들을 포함해서 분석해주세요:\n1. 기본 통계 정보\n2. 데이터 품질 검사\n3. 주요 인사이트\n4. 시각화 제안\n\n결과는 마크다운 형식으로 정리해주세요.",
                    "📊 데이터 처리",
                    ["파일명", "목적"],
                    True
                ),
                Template(
                    "코드 리뷰 요청",
                    "다음 코드를 리뷰해주세요:\n\n```{언어}\n{코드}\n```\n\n다음 관점에서 검토해주세요:\n1. 코드 품질 및 가독성\n2. 성능 최적화\n3. 보안 이슈\n4. 개선 제안\n\n구체적인 수정 사항과 이유를 설명해주세요.",
                    "💻 코딩 도움",
                    ["언어", "코드"],
                    True
                ),
                Template(
                    "웹 검색 및 요약",
                    "다음 주제에 대해 웹 검색을 하고 요약해주세요:\n\n주제: {주제}\n검색 범위: {범위}\n\n다음 형식으로 정리해주세요:\n1. 핵심 내용 요약\n2. 주요 출처 및 링크\n3. 최신 동향\n4. 결론 및 시사점",
                    "🔍 분석/리서치",
                    ["주제", "범위"]
                ),
                Template(
                    "비즈니스 이메일 작성",
                    "다음 내용으로 전문적인 비즈니스 이메일을 작성해주세요:\n\n수신자: {수신자}\n목적: {목적}\n주요 내용: {내용}\n\n다음 요소를 포함해주세요:\n- 적절한 인사말\n- 명확한 목적 전달\n- 구체적인 요청사항\n- 정중한 마무리",
                    "💼 업무용",
                    ["수신자", "목적", "내용"]
                )
            ]
            
            for template in defaults:
                self.add_template(template)
    
    def load_templates(self):
        """템플릿 파일에서 로드"""
        try:
            from utils.config_path import config_path_manager
            config_path = config_path_manager.get_config_path(self.templates_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.templates = [Template.from_dict(t) for t in data]
        except Exception as e:
            print(f"템플릿 로드 오류: {e}")
            self.templates = []
    
    def save_templates(self):
        """템플릿을 파일에 저장"""
        try:
            from utils.config_path import config_path_manager
            data = [t.to_dict() for t in self.templates]
            config_path = config_path_manager.get_config_path(self.templates_file)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"템플릿 저장 오류: {e}")
    
    def add_template(self, template: Template):
        """템플릿 추가"""
        self.templates.append(template)
        self.save_templates()
        self.templates_changed.emit()
    
    def remove_template(self, name: str):
        """템플릿 삭제"""
        self.templates = [t for t in self.templates if t.name != name]
        self.save_templates()
        self.templates_changed.emit()
    
    def get_template(self, name: str) -> Optional[Template]:
        """템플릿 조회"""
        for template in self.templates:
            if template.name == name:
                return template
        return None
    
    def get_templates_by_category(self, category: str) -> List[Template]:
        """카테고리별 템플릿 조회"""
        return [t for t in self.templates if t.category == category]
    
    def get_favorite_templates(self) -> List[Template]:
        """즐겨찾기 템플릿 조회"""
        return [t for t in self.templates if t.favorite]
    
    def get_recent_templates(self, limit: int = 5) -> List[Template]:
        """최근 사용 템플릿 조회"""
        recent = [t for t in self.templates if t.last_used]
        recent.sort(key=lambda x: x.last_used or '', reverse=True)
        return recent[:limit]
    
    def use_template(self, name: str) -> Optional[str]:
        """템플릿 사용 (사용 횟수 증가)"""
        template = self.get_template(name)
        if template:
            template.used_count += 1
            template.last_used = datetime.now().isoformat()
            self.save_templates()
            return template.content
        return None
    
    def search_templates(self, query: str) -> List[Template]:
        """템플릿 검색"""
        query = query.lower()
        results = []
        for template in self.templates:
            if (query in template.name.lower() or 
                query in template.content.lower() or
                query in template.category.lower()):
                results.append(template)
        return results


# 전역 템플릿 매니저 인스턴스
template_manager = TemplateManager()