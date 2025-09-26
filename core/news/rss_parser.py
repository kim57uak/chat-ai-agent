"""
RSS 파서 및 뉴스 분석기
"""

import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

class RSSParser:
    """RSS 피드 파서"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_news_rss(self, url: str, filter_days: int = 0) -> List[Dict]:
        """뉴스 RSS 파싱 (날짜 필터링 포함)"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            items = []
            
            # 날짜 필터링 기준 설정 (오늘 자정부터)
            if filter_days == 0:
                # 오늘 날짜만 (자정부터)
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                cutoff_date = today
                logger.info(f"뉴스 필터링: 오늘({today.strftime('%Y-%m-%d')}) 이후만 표시")
            elif filter_days > 0:
                cutoff_date = datetime.now() - timedelta(days=filter_days)
                logger.info(f"뉴스 필터링: {filter_days}일 전({cutoff_date.strftime('%Y-%m-%d %H:%M')}) 이후만 표시")
            else:
                cutoff_date = None
                logger.info("뉴스 필터링: 모든 날짜 표시")
            
            # RSS 2.0 형식
            if root.tag == 'rss':
                for item in root.findall('.//item'):
                    title = self._get_text(item, 'title')
                    link = self._get_text(item, 'link')
                    pub_date = self._get_text(item, 'pubDate')
                    parsed_date = self._parse_date(pub_date)
                    
                    # 날짜 필터링
                    if cutoff_date and parsed_date and parsed_date < cutoff_date:
                        continue
                    
                    if title and link:
                        # 이미지 URL 추출
                        image_url = self._extract_image_url(item)
                        
                        items.append({
                            'title': title.strip(),
                            'link': link.strip(),
                            'pubDate': parsed_date,
                            'source': self._extract_domain(url),
                            'image_url': image_url
                        })
            
            # RDF 형식 (아사히신문 등)
            elif 'RDF' in root.tag:
                namespaces = {
                    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    '': 'http://purl.org/rss/1.0/'
                }
                
                for item in root.findall('.//item', namespaces):
                    title = self._get_text_ns(item, 'title', namespaces)
                    link = self._get_text_ns(item, 'link', namespaces)
                    pub_date = self._get_text_ns(item, 'dc:date', namespaces)
                    parsed_date = self._parse_date(pub_date)
                    
                    # 날짜 필터링
                    if cutoff_date and parsed_date and parsed_date < cutoff_date:
                        continue
                    
                    if title and link:
                        # 이미지 URL 추출
                        image_url = self._extract_image_url(item)
                        
                        items.append({
                            'title': title.strip(),
                            'link': link.strip(),
                            'pubDate': parsed_date,
                            'source': self._extract_domain(url),
                            'image_url': image_url
                        })
            
            return sorted(items, key=lambda x: x['pubDate'] or datetime.min, reverse=True)
            
        except Exception as e:
            logger.error(f"RSS 파싱 오류 ({url}): {e}")
            return []
    
    def parse_earthquake_rss(self, url: str, filter_days: int = 3) -> List[Dict]:
        """지진 RSS 파싱 (날짜 필터링 포함)"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            items = []
            
            # 날짜 필터링 기준 설정
            if filter_days > 0:
                cutoff_date = datetime.now() - timedelta(days=filter_days)
                logger.info(f"지진 필터링: {filter_days}일 전({cutoff_date.strftime('%Y-%m-%d %H:%M')}) 이후만 표시")
            else:
                cutoff_date = None
                logger.info("지진 필터링: 모든 날짜 표시")
            
            namespaces = {
                'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            for item in root.findall('.//item'):
                title = self._get_text(item, 'title')
                link = self._get_text(item, 'link')
                pub_date = self._get_text(item, 'pubDate')
                parsed_date = self._parse_date(pub_date)
                lat = self._get_text_ns(item, 'geo:lat', namespaces)
                lon = self._get_text_ns(item, 'geo:long', namespaces)
                
                # 날짜 필터링
                if cutoff_date and parsed_date and parsed_date < cutoff_date:
                    continue
                
                if title and link and lat and lon:
                    # 진도 추출 (제목에서)
                    magnitude = self._extract_magnitude(title)
                    
                    items.append({
                        'title': title.strip(),
                        'link': link.strip(),
                        'pubDate': parsed_date,
                        'latitude': float(lat),
                        'longitude': float(lon),
                        'magnitude': magnitude,
                        'source': self._extract_domain(url)
                    })
            
            return sorted(items, key=lambda x: x['pubDate'] or datetime.min, reverse=True)
            
        except Exception as e:
            logger.error(f"지진 RSS 파싱 오류 ({url}): {e}")
            return []
    
    def _get_text(self, element, tag: str) -> Optional[str]:
        """XML 요소에서 텍스트 추출"""
        child = element.find(tag)
        return child.text if child is not None else None
    
    def _get_text_ns(self, element, tag: str, namespaces: Dict) -> Optional[str]:
        """네임스페이스를 고려한 텍스트 추출"""
        child = element.find(tag, namespaces)
        return child.text if child is not None else None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None
        
        try:
            parsed_date = date_parser.parse(date_str)
            # timezone 정보가 있으면 UTC로 변환 후 naive로 만들기
            if parsed_date.tzinfo is not None:
                parsed_date = parsed_date.utctimetuple()
                parsed_date = datetime(*parsed_date[:6])
            return parsed_date
        except:
            return None
    
    def _extract_domain(self, url: str) -> str:
        """URL에서 도메인 추출"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return url
    
    def _extract_magnitude(self, title: str) -> Optional[float]:
        """제목에서 진도 추출"""
        import re
        
        # M 5.2, Magnitude 5.2, ML 5.2 등의 패턴 찾기
        patterns = [
            r'M\s*(\d+\.?\d*)',
            r'ML\s*(\d+\.?\d*)',
            r'Magnitude\s*(\d+\.?\d*)',
            r'magnitude\s*(\d+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_image_url(self, item) -> Optional[str]:
        """뉴스 아이템에서 이미지 URL 추출"""
        try:
            # enclosure 태그에서 이미지 찾기
            enclosure = item.find('enclosure')
            if enclosure is not None:
                url = enclosure.get('url', '')
                type_attr = enclosure.get('type', '')
                if url and 'image' in type_attr.lower():
                    return url
            
            # media:content 태그에서 이미지 찾기
            media_content = item.find('.//{http://search.yahoo.com/mrss/}content')
            if media_content is not None:
                url = media_content.get('url', '')
                type_attr = media_content.get('type', '')
                if url and 'image' in type_attr.lower():
                    return url
            
            # media:thumbnail 태그에서 이미지 찾기
            media_thumbnail = item.find('.//{http://search.yahoo.com/mrss/}thumbnail')
            if media_thumbnail is not None:
                url = media_thumbnail.get('url', '')
                if url:
                    return url
            
            # description에서 img 태그 찾기
            description = self._get_text(item, 'description')
            if description:
                import re
                img_match = re.search(r'<img[^>]+src=["\']([^"\'>]+)["\']', description, re.IGNORECASE)
                if img_match:
                    return img_match.group(1)
            
            return None
            
        except Exception as e:
            logger.debug(f"이미지 URL 추출 오류: {e}")
            return None


class NewsAnalyzer:
    """뉴스 분석기"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    def analyze_and_summarize(self, news_items: List[Dict], category: str) -> List[Dict]:
        """뉴스 분석 및 요약"""
        if not self.ai_client:
            logger.error("AI 클라이언트가 설정되지 않았습니다.")
            return news_items
        
        if not news_items:
            logger.warning("분석할 뉴스 아이템이 없습니다.")
            return news_items
        
        logger.info(f"{category} 뉴스 {len(news_items)}개 분석 시작 (AI 클라이언트: {type(self.ai_client).__name__})")
        
        try:
            # 해외 뉴스인 경우만 번역 수행
            if category == '해외':
                # 간단한 번역 요청으로 변경
                titles_to_translate = [item['title'] for item in news_items[:3]]
                prompt = f"""
Please translate these news titles to Korean:

{json.dumps(titles_to_translate, ensure_ascii=False, indent=2)}

Respond in JSON format:
{{
  "translations": [
    "Korean title 1",
    "Korean title 2",
    "Korean title 3"
  ]
}}
"""
            else:
                # 국내 뉴스는 번역 없이 그대로 반환
                return news_items
            
            messages = [{
                "role": "user",
                "content": prompt
            }]
            logger.info(f"AI에게 번역 요청 전송 중... (프롬프트 길이: {len(prompt)} 문자)")
            logger.debug(f"번역 요청 내용: {titles_to_translate}")
            response, _ = self.ai_client.chat(messages)
            logger.info(f"AI 응답 수신 완료 (응답 길이: {len(response)} 문자)")
            logger.debug(f"AI 응답 내용: {response[:200]}...")
            
            try:
                translation_result = json.loads(response)
                translations = translation_result.get('translations', [])
                
                analyzed_items = []
                logger.info(f"번역 결과: {len(translations)}개 수신")
                for i, item in enumerate(news_items):
                    news_item = item.copy()
                    if category == '해외' and i < len(translations):
                        translated_title = translations[i]
                        if translated_title and translated_title.strip() and translated_title != item['title']:
                            news_item['translated_title'] = translated_title
                            logger.info(f"해외뉴스 번역 성공: {item['title'][:30]}... -> {translated_title[:30]}...")
                        else:
                            news_item['translated_title'] = item['title']
                            logger.warning(f"번역 실패 또는 동일, 원본 사용: {item['title'][:30]}...")
                    else:
                        news_item['translated_title'] = item['title']
                    news_item['importance_score'] = 5  # 기본 점수
                    analyzed_items.append(news_item)
                
                return analyzed_items
                
            except json.JSONDecodeError as e:
                logger.error(f"AI 응답 JSON 파싱 실패: {e}")
                logger.error(f"AI 응답 내용: {response[:500]}...")
                # JSON 파싱 실패 시 원본 뉴스에 빈 번역 필드 추가
                for item in news_items:
                    if category == '해외':
                        item['translated_title'] = item['title']  # 원본 제목 사용
                return news_items
                
        except Exception as e:
            logger.error(f"뉴스 분석 오류: {e}")
            return news_items
    
    def translate_earthquake_info(self, earthquake_items: List[Dict]) -> List[Dict]:
        """지진 정보 번역"""
        if not self.ai_client or not earthquake_items:
            return earthquake_items
        
        try:
            titles = [item['title'] for item in earthquake_items[:5]]  # 최대 5개만
            
            prompt = f"""
다음 지진 정보 제목들을 한글로 번역해주세요:

{json.dumps(titles, ensure_ascii=False, indent=2)}

응답 형식:
{{
  "translated_titles": [
    "번역된 제목1",
    "번역된 제목2",
    ...
  ]
}}

JSON 형식으로만 응답해주세요.
"""
            
            messages = [{
                "role": "user",
                "content": prompt
            }]
            response, _ = self.ai_client.chat(messages)
            
            try:
                translation = json.loads(response)
                translated_titles = translation.get('translated_titles', [])
                
                for i, item in enumerate(earthquake_items):
                    if i < len(translated_titles):
                        item['translated_title'] = translated_titles[i]
                    else:
                        item['translated_title'] = item['title']
                
                return earthquake_items
                
            except json.JSONDecodeError:
                logger.error("지진 정보 번역 JSON 파싱 실패")
                return earthquake_items
                
        except Exception as e:
            logger.error(f"지진 정보 번역 오류: {e}")
            return earthquake_items