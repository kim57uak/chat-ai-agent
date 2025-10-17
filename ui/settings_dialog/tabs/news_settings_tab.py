"""
News Settings Tab
뉴스 설정 탭
"""

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QGroupBox, QVBoxLayout, QCheckBox
from utils.config_path import config_path_manager
from core.logging import get_logger
from ..base_settings_tab import BaseSettingsTab
import json

logger = get_logger("news_settings_tab")


class NewsSettingsTab(BaseSettingsTab):
    """뉴스 설정 탭"""
    
    def __init__(self, parent=None):
        self.news_source_checkboxes = {}
        super().__init__(parent)
    
    def create_ui(self):
        """UI 생성"""
        # 뉴스 소스 설정 그룹
        sources_group = QGroupBox('📰 뉴스 소스 설정')
        sources_layout = QVBoxLayout(sources_group)
        sources_layout.setSpacing(12)
        
        self._create_news_source_checkboxes(sources_layout)
        
        self.content_layout.addWidget(sources_group)
        
        # 표시 설정 그룹
        display_group = QGroupBox('📺 표시 설정')
        display_layout = QVBoxLayout(display_group)
        display_layout.setSpacing(12)
        
        domestic_layout = QHBoxLayout()
        domestic_layout.addWidget(QLabel('국내 뉴스 개수:'))
        self.domestic_count_spin = QSpinBox()
        self.domestic_count_spin.setRange(1, 20)
        self.domestic_count_spin.setValue(5)
        self.domestic_count_spin.setSuffix(' 개')
        self.domestic_count_spin.setMinimumHeight(40)
        domestic_layout.addWidget(self.domestic_count_spin)
        display_layout.addLayout(domestic_layout)
        
        international_layout = QHBoxLayout()
        international_layout.addWidget(QLabel('해외 뉴스 개수:'))
        self.international_count_spin = QSpinBox()
        self.international_count_spin.setRange(1, 100)
        self.international_count_spin.setValue(5)
        self.international_count_spin.setSuffix(' 개')
        self.international_count_spin.setMinimumHeight(40)
        international_layout.addWidget(self.international_count_spin)
        display_layout.addLayout(international_layout)
        
        earthquake_layout = QHBoxLayout()
        earthquake_layout.addWidget(QLabel('지진 정보 개수:'))
        self.earthquake_count_spin = QSpinBox()
        self.earthquake_count_spin.setRange(1, 20)
        self.earthquake_count_spin.setValue(5)
        self.earthquake_count_spin.setSuffix(' 개')
        self.earthquake_count_spin.setMinimumHeight(40)
        earthquake_layout.addWidget(self.earthquake_count_spin)
        display_layout.addLayout(earthquake_layout)
        
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel('표시 시간:'))
        self.display_duration_spin = QSpinBox()
        self.display_duration_spin.setRange(2, 30)
        self.display_duration_spin.setValue(5)
        self.display_duration_spin.setSuffix(' 초')
        self.display_duration_spin.setMinimumHeight(40)
        duration_layout.addWidget(self.display_duration_spin)
        display_layout.addLayout(duration_layout)
        
        self.content_layout.addWidget(display_group)
        
        # 날짜 필터링 설정 그룹
        filter_group = QGroupBox('📅 날짜 필터링 설정')
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(12)
        
        news_filter_layout = QHBoxLayout()
        news_filter_layout.addWidget(QLabel('뉴스 필터링 (일):'))
        self.news_days_spin = QSpinBox()
        self.news_days_spin.setRange(0, 30)
        self.news_days_spin.setValue(0)
        self.news_days_spin.setSuffix(' 일 (0=오늘만)')
        self.news_days_spin.setMinimumHeight(40)
        news_filter_layout.addWidget(self.news_days_spin)
        filter_layout.addLayout(news_filter_layout)
        
        earthquake_filter_layout = QHBoxLayout()
        earthquake_filter_layout.addWidget(QLabel('지진 필터링 (일):'))
        self.earthquake_days_spin = QSpinBox()
        self.earthquake_days_spin.setRange(1, 30)
        self.earthquake_days_spin.setValue(3)
        self.earthquake_days_spin.setSuffix(' 일')
        self.earthquake_days_spin.setMinimumHeight(40)
        earthquake_filter_layout.addWidget(self.earthquake_days_spin)
        filter_layout.addLayout(earthquake_filter_layout)
        
        self.content_layout.addWidget(filter_group)
    
    def _create_news_source_checkboxes(self, layout):
        """뉴스 소스 체크박스 동적 생성"""
        try:
            config_path = config_path_manager.get_config_path('news_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for category, sources in config['news_sources'].items():
                for source in sources:
                    checkbox_key = f"{category}_{source['name']}"
                    checkbox = QCheckBox(f"{source['name']} 사용")
                    self.news_source_checkboxes[checkbox_key] = {
                        'checkbox': checkbox,
                        'category': category,
                        'source_name': source['name']
                    }
                    layout.addWidget(checkbox)
        except Exception as e:
            logger.debug(f"뉴스 소스 체크박스 생성 오류: {e}")
    
    def load_settings(self):
        """설정 로드"""
        try:
            config_path = config_path_manager.get_config_path('news_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            for category, sources in config['news_sources'].items():
                for source in sources:
                    checkbox_key = f"{category}_{source['name']}"
                    if checkbox_key in self.news_source_checkboxes:
                        checkbox = self.news_source_checkboxes[checkbox_key]['checkbox']
                        checkbox.setChecked(source.get('enabled', False))
            
            news_settings = config.get('news_settings', {})
            self.domestic_count_spin.setValue(news_settings.get('domestic_count', 3))
            self.international_count_spin.setValue(news_settings.get('international_count', 3))
            self.earthquake_count_spin.setValue(news_settings.get('earthquake_count', 2))
            
            display_settings = config.get('display_settings', {})
            self.display_duration_spin.setValue(display_settings.get('display_duration', 8000) // 1000)
            
            date_filter = config.get('date_filter', {})
            self.news_days_spin.setValue(date_filter.get('news_days', 0))
            self.earthquake_days_spin.setValue(date_filter.get('earthquake_days', 3))
        except Exception as e:
            logger.debug(f"뉴스 설정 로드 오류: {e}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            try:
                config_path = config_path_manager.get_config_path('news_config.json')
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                config = {
                    'news_sources': {'domestic': [], 'international': [], 'earthquake': []},
                    'display_settings': {}
                }
            
            for checkbox_key, checkbox_info in self.news_source_checkboxes.items():
                category = checkbox_info['category']
                source_name = checkbox_info['source_name']
                is_checked = checkbox_info['checkbox'].isChecked()
                
                for source in config['news_sources'][category]:
                    if source['name'] == source_name:
                        source['enabled'] = is_checked
                        break
            
            if 'news_settings' not in config:
                config['news_settings'] = {}
            
            domestic_enabled = any(cb['checkbox'].isChecked() for cb in self.news_source_checkboxes.values() if cb['category'] == 'domestic')
            international_enabled = any(cb['checkbox'].isChecked() for cb in self.news_source_checkboxes.values() if cb['category'] == 'international')
            earthquake_enabled = any(cb['checkbox'].isChecked() for cb in self.news_source_checkboxes.values() if cb['category'] == 'earthquake')
            
            config['news_settings'].update({
                'show_domestic': domestic_enabled,
                'show_international': international_enabled,
                'show_earthquake': earthquake_enabled,
                'domestic_count': self.domestic_count_spin.value(),
                'international_count': self.international_count_spin.value(),
                'earthquake_count': self.earthquake_count_spin.value()
            })
            
            config['display_settings'].update({
                'domestic_news_count': self.domestic_count_spin.value(),
                'international_news_count': self.international_count_spin.value(),
                'earthquake_count': self.earthquake_count_spin.value(),
                'display_duration': self.display_duration_spin.value() * 1000,
                'auto_refresh_interval': 300000
            })
            
            config['date_filter'] = {
                'news_days': self.news_days_spin.value(),
                'earthquake_days': self.earthquake_days_spin.value()
            }
            
            config_path = config_path_manager.get_config_path('news_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"뉴스 설정 저장 오류: {e}")
    
    def get_tab_title(self) -> str:
        return '📰 뉴스'
