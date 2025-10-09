"""상태 표시 컴포넌트 - 실시간 AI 처리 상태 모니터링"""
from core.logging import get_logger

logger = get_logger("status_display")

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Optional
import time
import json


class StatusDisplay(QObject):
    """AI 처리 상태를 실시간으로 표시하는 컴포넌트"""
    
    status_updated = pyqtSignal(dict)  # 상태 업데이트 시그널
    
    def __init__(self):
        super().__init__()
        self.current_status = {
            'state': 'idle',  # idle, processing, streaming, completed, error
            'model': '',
            'mode': 'ask',  # ask, agent
            'start_time': None,
            'elapsed_time': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'tools_used': [],
            'progress': 0,
            'response_time': 0
        }
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_elapsed_time)
        self.session_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_time': 0,
            'tools_count': 0
        }
    
    def start_processing(self, model: str, mode: str = 'ask'):
        """AI 처리 시작"""
        self.current_status.update({
            'state': 'processing',
            'model': model,
            'mode': mode,
            'start_time': time.time(),
            'elapsed_time': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'tools_used': [],
            'progress': 0,
            'response_time': 0
        })
        self.timer.start(100)  # 100ms마다 업데이트
        self.status_updated.emit(self.current_status.copy())
    
    def update_tokens(self, input_tokens: int = 0, output_tokens: int = 0):
        """토큰 사용량 업데이트 (현재 단계만)"""
        self.current_status['input_tokens'] = input_tokens
        self.current_status['output_tokens'] = output_tokens
        self.current_status['total_tokens'] = input_tokens + output_tokens
        
        # 전역 토큰 카운터에 토큰 추가
        from core.global_token_counter import global_token_counter
        logger.debug(f"StatusDisplay] update_tokens() 호출: {input_tokens}/{output_tokens}")
        global_token_counter.add_tokens(input_tokens, output_tokens)
        
        self.status_updated.emit(self.current_status.copy())
    
    def add_tool_used(self, tool_name: str):
        """사용된 도구 추가"""
        if tool_name not in self.current_status['tools_used']:
            self.current_status['tools_used'].append(tool_name)
            self.status_updated.emit(self.current_status.copy())
    
    def set_streaming(self, progress: int = 0):
        """스트리밍 상태 설정"""
        self.current_status['state'] = 'streaming'
        self.current_status['progress'] = progress
        self.status_updated.emit(self.current_status.copy())
    
    def finish_processing(self, success: bool = True):
        """처리 완료"""
        self.timer.stop()
        
        # 응답 시간 계산
        if self.current_status['start_time']:
            self.current_status['response_time'] = time.time() - self.current_status['start_time']
        
        self.current_status['state'] = 'completed' if success else 'error'
        
        # 세션 통계 업데이트
        if success:
            self.session_stats['total_requests'] += 1
            self.session_stats['total_tokens'] += self.current_status['total_tokens']
            self.session_stats['total_time'] += self.current_status['response_time']
            self.session_stats['tools_count'] += len(self.current_status['tools_used'])
        
        self.status_updated.emit(self.current_status.copy())
        
        # 3초 후 idle 상태로 복귀
        QTimer.singleShot(3000, self._reset_to_idle)
    
    def _update_elapsed_time(self):
        """경과 시간 업데이트"""
        if self.current_status['start_time']:
            self.current_status['elapsed_time'] = time.time() - self.current_status['start_time']
            self.status_updated.emit(self.current_status.copy())
    
    def _reset_to_idle(self):
        """idle 상태로 복귀"""
        self.current_status['state'] = 'idle'
        self.status_updated.emit(self.current_status.copy())
    
    def get_status_html(self) -> str:
        """상태를 HTML로 변환"""
        status = self.current_status
        state = status['state']
        
        if state == 'idle':
            # 세션 통계 표시
            if self.session_stats['total_requests'] > 0:
                avg_time = self.session_stats['total_time'] / self.session_stats['total_requests']
                return f'''
                <div class="status-idle" style="color: #888; font-size: 10px;">
                    💤 대기 중 | 📊 세션: {self.session_stats['total_requests']}회 
                    {self.session_stats['total_tokens']:,}토큰 평균{avg_time:.1f}초
                </div>
                '''
            return '<div class="status-idle" style="color: #888;">💤 대기 중</div>'
        
        # 상태별 아이콘과 색상
        state_config = {
            'processing': {'icon': '🤔', 'color': '#87CEEB', 'text': '처리 중'},
            'streaming': {'icon': '✨', 'color': '#98FB98', 'text': '응답 생성 중'},
            'completed': {'icon': '✅', 'color': '#90EE90', 'text': '완료'},
            'error': {'icon': '❌', 'color': '#FFB6C1', 'text': '오류'}
        }
        
        config = state_config.get(state, state_config['processing'])
        
        # 시간 정보
        if state == 'completed':
            time_str = f"{status['response_time']:.1f}초"
        else:
            elapsed = status['elapsed_time']
            time_str = f"{elapsed:.1f}초" if elapsed < 60 else f"{elapsed//60:.0f}분 {elapsed%60:.1f}초"
        
        # 토큰 정보 - 기존 형태 유지
        total_tokens = status.get('total_tokens', 0)
        input_tokens = status.get('input_tokens', 0)
        output_tokens = status.get('output_tokens', 0)
        
        if total_tokens > 0:
            if input_tokens > 0 and output_tokens > 0:
                token_str = f"📊 {total_tokens:,}토큰 (IN:{input_tokens:,} OUT:{output_tokens:,})"
            else:
                token_str = f"📊 {total_tokens:,}토큰"
        else:
            token_str = ""
        
        # 도구 정보 (시각적 강조)
        tools = status.get('tools_used', [])
        if tools:
            tool_icons = self._get_tool_icons(tools)
            tools_str = f"🔧 {' '.join(tool_icons)}"
        else:
            tools_str = ""
        
        # 모델 정보
        model = status.get('model', '')
        mode = status.get('mode', 'ask')
        mode_icon = '🔧' if mode == 'agent' else '💬'
        
        # 응답 시간과 토큰 사용량을 한 줄로 표시
        status_parts = [f"{config['icon']} {config['text']}", f"{mode_icon} {model}", f"⏱️ {time_str}"]
        
        if token_str:
            status_parts.append(token_str)
        
        if tools_str:
            status_parts.append(tools_str)
        
        return f'''
        <div class="status-active" style="color: {config['color']}; font-size: 11px;">
            {" | ".join(status_parts)}
        </div>
        '''


    def _get_tool_icons(self, tools: List[str]) -> List[str]:
        """도구별 아이콘 반환"""
        icon_map = {
            'search': '🔍', 'web': '🌐', 'url': '📄', 'fetch': '📄',
            'database': '🗄️', 'mysql': '🗄️', 'sql': '🗄️',
            'travel': '✈️', 'tour': '✈️', 'hotel': '🏨',
            'map': '🗺️', 'location': '📍', 'geocode': '📍',
            'email': '📧', 'file': '📁', 'excel': '📊',
            'image': '🖼️', 'translate': '🌐'
        }
        
        icons = []
        for tool in tools[:3]:  # 최대 3개만 표시
            tool_name = str(tool).lower()
            icon = "⚡"
            for keyword, emoji in icon_map.items():
                if keyword in tool_name:
                    icon = emoji
                    break
            icons.append(icon)
        
        if len(tools) > 3:
            icons.append(f"+{len(tools)-3}")
        
        return icons
    
    def get_session_stats(self) -> Dict:
        """세션 통계 반환"""
        return self.session_stats.copy()
    
    def reset_session_stats(self):
        """세션 통계 초기화"""
        self.session_stats = {
            'total_requests': 0,
            'total_tokens': 0,
            'total_time': 0,
            'tools_count': 0
        }


# 전역 상태 표시 인스턴스
status_display = StatusDisplay()