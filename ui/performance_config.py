"""
UI Performance Configuration
성능 관련 설정을 중앙에서 관리
"""

class PerformanceConfig:
    # 렌더링 최적화
    RENDER_BATCH_SIZE = 50  # 한 번에 렌더링할 메시지 수
    RENDER_DELAY_MS = 16  # 60fps 기준 (1000/60)
    
    # 스크롤 최적화
    SCROLL_DEBOUNCE_MS = 100
    SCROLL_LOAD_THRESHOLD = 200  # 스크롤 상단에서 이 픽셀 이내면 로드
    
    # 테마 적용 최적화
    THEME_APPLY_DELAY_MS = 50
    THEME_BATCH_UPDATE = True
    
    # 메모리 관리
    MAX_CACHED_MESSAGES = 100
    CLEANUP_INTERVAL_MS = 30000  # 30초마다 메모리 정리
    
    # WebView 최적화
    WEBVIEW_CACHE_ENABLED = True
    WEBVIEW_LAZY_LOAD = True
    
    # 타이머 통합
    USE_UNIFIED_TIMER = True
    UNIFIED_TIMER_INTERVAL_MS = 100

performance_config = PerformanceConfig()
