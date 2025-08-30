"""Modern animated progress bar with neon effects and particles"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QPen, QBrush, QRadialGradient
from PyQt6.QtCore import Qt
import math
import random


class ModernProgressBar(QWidget):
    """현대적이고 화려한 애니메이션 progress bar"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)
        self.setMinimumWidth(200)
        
        # Progress state
        self._progress = 0.0
        self._is_indeterminate = True
        self._animation_offset = 0.0
        
        # Animation timers
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.setInterval(50)  # 20 FPS
        
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self._update_particles)
        self.particle_timer.setInterval(100)  # 10 FPS
        
        # Particles for extra effects
        self.particles = []
        self._max_particles = 8
        
        # Color animation
        self.color_phase = 0.0
        
        # Start animations
        self.start_animation()
    
    def start_animation(self):
        """애니메이션 시작"""
        if not self.animation_timer.isActive():
            self.animation_timer.start()
        if not self.particle_timer.isActive():
            self.particle_timer.start()
    
    def stop_animation(self):
        """애니메이션 중지"""
        if self.animation_timer.isActive():
            self.animation_timer.stop()
        if self.particle_timer.isActive():
            self.particle_timer.stop()
        self.particles.clear()
        # 애니메이션 상태 초기화
        self._animation_offset = 0.0
        self.color_phase = 0.0
        self.update()
    
    def set_indeterminate(self, indeterminate: bool):
        """무한 로딩 모드 설정"""
        self._is_indeterminate = indeterminate
        if not indeterminate:
            self.particles.clear()
        self.update()
    
    def set_progress(self, progress: float):
        """진행률 설정 (0.0 ~ 1.0)"""
        self._progress = max(0.0, min(1.0, progress))
        self.update()
    
    def _update_animation(self):
        """애니메이션 업데이트"""
        self._animation_offset += 0.01
        self.color_phase += 0.0075
        
        if self._animation_offset > 2.0:
            self._animation_offset = 0.0
        if self.color_phase > 2 * math.pi:
            self.color_phase = 0.0
            
        self.update()
    
    def _update_particles(self):
        """파티클 업데이트"""
        if not self._is_indeterminate:
            return
            
        # Remove old particles
        self.particles = [p for p in self.particles if p['life'] > 0]
        
        # Add new particles
        if len(self.particles) < self._max_particles and random.random() < 0.7:
            self.particles.append({
                'x': random.uniform(0, self.width()),
                'y': random.uniform(2, self.height() - 2),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-1, 1),
                'life': random.uniform(0.5, 1.0),
                'max_life': random.uniform(0.5, 1.0),
                'size': random.uniform(1, 3),
                'color_offset': random.uniform(0, 2 * math.pi)
            })
        
        # Update existing particles
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.02
            
            # Bounce off edges
            if particle['x'] <= 0 or particle['x'] >= self.width():
                particle['vx'] *= -0.8
            if particle['y'] <= 0 or particle['y'] >= self.height():
                particle['vy'] *= -0.8
                
        self.update()
    
    def _get_modern_color(self, phase: float, alpha: float = 1.0) -> QColor:
        """현대적이고 아름다운 색상 생성"""
        # 테마에 따른 색상 가져오기
        colors = self._get_theme_colors()
        if not colors:
            # 기본 색상
            colors = [
                (138, 43, 226),   # 블루바이올렛
                (75, 0, 130),     # 인디고
                (0, 191, 255),    # 딥스카이블루
                (30, 144, 255),   # 독지블루
                (0, 206, 209),    # 다크터콰이즈
                (64, 224, 208),   # 터콰이즈
            ]
        
        # 부드러운 전환을 위한 인덱스 계산
        normalized_phase = (phase % (2 * math.pi)) / (2 * math.pi)
        color_index = normalized_phase * (len(colors) - 1)
        
        # 인덱스와 보간 비율
        index1 = int(color_index) % len(colors)
        index2 = (index1 + 1) % len(colors)
        t = color_index - int(color_index)
        
        # 색상 보간
        r1, g1, b1 = colors[index1]
        r2, g2, b2 = colors[index2]
        
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        return QColor(r, g, b, int(255 * alpha))
    
    def _get_theme_colors(self):
        """테마에 따른 로딩바 색상 반환"""
        try:
            from ui.styles.theme_manager import theme_manager
            
            if theme_manager.use_material_theme:
                loading_config = theme_manager.material_manager.get_loading_bar_config()
                chunk_color = loading_config.get('chunk', '')
                
                # 그라디언트에서 색상 추출
                if 'linear-gradient' in chunk_color:
                    # 간단한 색상 추출 (예: #bb86fc, #03dac6)
                    import re
                    hex_colors = re.findall(r'#[0-9a-fA-F]{6}', chunk_color)
                    if len(hex_colors) >= 2:
                        colors = []
                        for hex_color in hex_colors:
                            r = int(hex_color[1:3], 16)
                            g = int(hex_color[3:5], 16)
                            b = int(hex_color[5:7], 16)
                            colors.append((r, g, b))
                        return colors
            
            return None
        except Exception:
            return None
    
    def update_theme(self):
        """테마 업데이트"""
        try:
            # 색상 캐시 초기화
            self.color_phase = 0.0
            self.update()
            print("로딩바 테마 업데이트 완료")
        except Exception as e:
            print(f"로딩바 테마 업데이트 오류: {e}")
    
    def paintEvent(self, event):
        """페인트 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 경계 없는 투명 배경
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if self._is_indeterminate:
            self._paint_indeterminate(painter, rect)
        else:
            self._paint_determinate(painter, rect)
        
        # Draw particles
        self._paint_particles(painter)
    
    def _paint_indeterminate(self, painter: QPainter, rect: QRect):
        """넓고 자유로운 선형 움직임의 고급스러운 애니메이션"""
        from PyQt6.QtGui import QPainterPath
        
        width = rect.width()
        height = rect.height()
        
        # 여러 개의 넓은 웨이브 레이어 생성
        for layer in range(5):
            # 각 레이어별 독립적인 움직임
            layer_phase = (self._animation_offset * (2.0 + layer * 0.3)) % 2.0
            
            # 넓은 선형 움직임 - 전체 폭을 가로지르는 움직임
            if layer_phase <= 1.0:
                wave_center = width * layer_phase
            else:
                wave_center = width * (2.0 - layer_phase)
            
            # 매우 넓은 웨이브 형태
            wave_width = width * 0.8  # 전체 폭의 80%
            wave_height = height * 0.9
            
            # 부드러운 웨이브 패스 생성
            path = QPainterPath()
            
            # 웨이브의 시작과 끝 지점
            start_x = max(0, wave_center - wave_width / 2)
            end_x = min(width, wave_center + wave_width / 2)
            
            # 상단 곡선 생성
            points_top = []
            points_bottom = []
            
            num_segments = 40  # 부드러운 곡선을 위한 많은 세그먼트
            
            for i in range(num_segments + 1):
                progress = i / num_segments
                x = start_x + (end_x - start_x) * progress
                
                # 복합적인 사인파로 자연스러운 웨이브 생성
                wave_amplitude = wave_height * 0.4
                
                # 여러 주파수 조합으로 복잡한 웨이브
                wave_y = (
                    math.sin(progress * math.pi * 4 + self._animation_offset * 6 + layer * 2) * 0.4 +
                    math.sin(progress * math.pi * 2 + self._animation_offset * 4 + layer) * 0.3 +
                    math.sin(progress * math.pi * 6 - self._animation_offset * 8 + layer * 1.5) * 0.2
                ) * wave_amplitude
                
                # 가장자리에서 부드럽게 감소하는 효과
                edge_factor = math.sin(progress * math.pi)
                wave_y *= edge_factor
                
                y_top = height / 2 - wave_y
                y_bottom = height / 2 + wave_y
                
                points_top.append((x, y_top))
                points_bottom.append((x, y_bottom))
            
            # 패스 생성
            if points_top:
                path.moveTo(points_top[0][0], points_top[0][1])
                
                # 상단 곡선
                for point in points_top[1:]:
                    path.lineTo(point[0], point[1])
                
                # 하단 곡선 (역순)
                for point in reversed(points_bottom):
                    path.lineTo(point[0], point[1])
                
                path.closeSubpath()
                
                # 고급스러운 그라디언트 색상
                alpha = 0.7 - layer * 0.1
                color_phase = self.color_phase + layer * math.pi / 4
                wave_color = self._get_modern_color(color_phase, alpha)
                
                # 넓은 선형 그라디언트
                gradient = QLinearGradient(start_x, 0, end_x, 0)
                gradient.setColorAt(0, QColor(wave_color.red(), wave_color.green(), wave_color.blue(), 0))
                gradient.setColorAt(0.1, QColor(wave_color.red(), wave_color.green(), wave_color.blue(), int(wave_color.alpha() * 0.3)))
                gradient.setColorAt(0.5, wave_color)
                gradient.setColorAt(0.9, QColor(wave_color.red(), wave_color.green(), wave_color.blue(), int(wave_color.alpha() * 0.3)))
                gradient.setColorAt(1, QColor(wave_color.red(), wave_color.green(), wave_color.blue(), 0))
                
                painter.setBrush(QBrush(gradient))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(path)
        
        # 전체적인 배경 글로우 효과
        glow_gradient = QLinearGradient(0, 0, width, 0)
        glow_color = self._get_modern_color(self.color_phase, 0.15)
        glow_gradient.setColorAt(0, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))
        glow_gradient.setColorAt(0.5, glow_color)
        glow_gradient.setColorAt(1, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 0))
        
        painter.setBrush(QBrush(glow_gradient))
        painter.drawRect(0, 0, width, height)
    
    def _paint_determinate(self, painter: QPainter, rect: QRect):
        """진행률 표시 애니메이션 그리기"""
        progress_width = int(rect.width() * self._progress)
        progress_rect = QRect(rect.x() + 2, rect.y() + 2, 
                            progress_width - 4, rect.height() - 4)
        
        if progress_width > 4:
            # Progress gradient
            gradient = QLinearGradient(0, 0, progress_width, 0)
            
            # Animated colors based on progress
            base_phase = self.color_phase + self._progress * math.pi
            color1 = self._get_modern_color(base_phase, 0.9)
            color2 = self._get_modern_color(base_phase + math.pi / 2, 0.9)
            color3 = self._get_modern_color(base_phase + math.pi, 0.9)
            
            gradient.setColorAt(0, color1)
            gradient.setColorAt(0.5, color2)
            gradient.setColorAt(1, color3)
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(progress_rect, 4, 4)
            
            # Progress glow
            glow_gradient = QRadialGradient(progress_width, rect.height() / 2, rect.height() * 1.5)
            glow_color = self._get_modern_color(base_phase, 0.4)
            glow_gradient.setColorAt(0, glow_color)
            glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
            
            painter.setBrush(QBrush(glow_gradient))
            painter.drawRoundedRect(rect, 6, 6)
    
    def _paint_particles(self, painter: QPainter):
        """파티클 그리기"""
        if not self._is_indeterminate:
            return
            
        painter.setPen(Qt.PenStyle.NoPen)
        
        for particle in self.particles:
            alpha = particle['life'] / particle['max_life']
            size = particle['size'] * alpha
            
            if size > 0.5:
                color_phase = self.color_phase + particle['color_offset']
                color = self._get_modern_color(color_phase, alpha * 0.8)
                
                # Particle glow
                glow_gradient = QRadialGradient(particle['x'], particle['y'], size * 3)
                glow_gradient.setColorAt(0, color)
                glow_gradient.setColorAt(1, QColor(0, 0, 0, 0))
                
                painter.setBrush(QBrush(glow_gradient))
                painter.drawEllipse(int(particle['x'] - size), int(particle['y'] - size),
                                  int(size * 2), int(size * 2))