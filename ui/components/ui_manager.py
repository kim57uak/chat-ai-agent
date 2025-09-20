from PyQt6.QtWidgets import QProgressBar
from PyQt6.QtCore import QTimer
from ui.components.modern_progress_bar import ModernProgressBar
import math


class UIManager:
    """UI 상태 관리를 담당하는 클래스 (SRP)"""
    
    def __init__(self, send_button, cancel_button, upload_button, template_button, loading_bar):
        self.send_button = send_button
        self.cancel_button = cancel_button
        self.upload_button = upload_button
        self.template_button = template_button
        self.loading_bar = loading_bar
        
        # 애니메이션 관련 속성
        self.loading_animation_value = 0
        self.animation_direction = 1
        self.pulse_value = 0
        self.loading_animation_timer = None
        self.fade_timer = None
        self.fade_out_timer = None
        self.fade_value = 0
        self.fade_out_value = 1.0
    
    def set_ui_enabled(self, enabled):
        """UI 활성화/비활성화"""
        self.send_button.setEnabled(enabled)
        self.cancel_button.setVisible(not enabled)
        self.upload_button.setEnabled(enabled)
        self.template_button.setEnabled(enabled)
    
    def show_loading(self, show):
        """로딩 상태 표시/숨김"""
        if isinstance(self.loading_bar, ModernProgressBar):
            if show:
                self.loading_bar.set_indeterminate(True)
                self.loading_bar.start_animation()  # 명시적으로 애니메이션 시작
                self.loading_bar.show()
            else:
                self.loading_bar.hide()
                self.loading_bar.stop_animation()
        else:
            # Fallback for standard QProgressBar
            if show:
                self._start_loading_animation()
            else:
                self._stop_loading_animation()
    
    def _start_loading_animation(self):
        """로딩 애니메이션 시작"""
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2a2a;
                border: none;
                border-radius: 2px;
                margin: 0px;
                padding: 0px;
                opacity: 0;
            }
            QProgressBar::chunk {
                background: rgba(135,163,215,180);
                border-radius: 2px;
            }
        """)
        self.loading_bar.show()
        
        self.fade_timer = QTimer()
        self.fade_value = 0
        
        def fade_in():
            self.fade_value += 0.1
            if self.fade_value >= 1.0:
                self.fade_value = 1.0
                self.fade_timer.stop()
                
                self.loading_animation_timer = QTimer()
                self.loading_animation_timer.timeout.connect(self._update_loading_animation)
                self.loading_animation_timer.start(80)
                self.loading_animation_value = 0
            else:
                style = f"""
                    QProgressBar {{
                        background-color: #2a2a2a;
                        border: none;
                        border-radius: 2px;
                        margin: 0px;
                        padding: 0px;
                    }}
                    QProgressBar::chunk {{
                        background: rgba(135,163,215,{int(180 * self.fade_value)});
                        border-radius: 2px;
                    }}
                """
                self.loading_bar.setStyleSheet(style)
        
        self.fade_timer.timeout.connect(fade_in)
        self.fade_timer.start(30)
    
    def _stop_loading_animation(self):
        """로딩 애니메이션 중지"""
        if hasattr(self, 'loading_animation_timer') and self.loading_animation_timer and self.loading_animation_timer.isActive():
            self.loading_animation_timer.stop()
            
        self.fade_out_timer = QTimer()
        self.fade_out_value = 1.0
        
        def fade_out():
            self.fade_out_value -= 0.1
            if self.fade_out_value <= 0:
                self.fade_out_value = 0
                self.fade_out_timer.stop()
                self.loading_bar.hide()
            else:
                style = f"""
                    QProgressBar {{
                        background-color: #2a2a2a;
                        border: none;
                        border-radius: 2px;
                        margin: 0px;
                        padding: 0px;
                    }}
                    QProgressBar::chunk {{
                        background: rgba(135,163,215,{int(180 * self.fade_out_value)});
                        border-radius: 2px;
                    }}
                """
                self.loading_bar.setStyleSheet(style)
        
        self.fade_out_timer.timeout.connect(fade_out)
        self.fade_out_timer.start(30)
    
    def _update_loading_animation(self):
        """로딩 애니메이션 업데이트"""
        if not hasattr(self, 'loading_animation_value'):
            self.loading_animation_value = 0
        if not hasattr(self, 'animation_direction'):
            self.animation_direction = 1
        if not hasattr(self, 'pulse_value'):
            self.pulse_value = 0
            
        self.pulse_value = (self.pulse_value + 0.1) % (2 * 3.14159)
        pulse_factor = (math.sin(self.pulse_value) + 1) / 2
        
        self.loading_animation_value += 3 * self.animation_direction
        
        if self.loading_animation_value >= 200 or self.loading_animation_value <= 0:
            self.animation_direction *= -1
        
        offset = self.loading_animation_value / 100.0
        
        color1_alpha = int(180 + 75 * pulse_factor)
        color2_alpha = int(220 + 35 * pulse_factor)
        
        gradient = f"""qlineargradient(x1:{offset}, y1:0, x2:{offset+1}, y2:0, 
                      stop:0 rgba(163,135,215,{color1_alpha}), 
                      stop:0.4 rgba(135,163,215,{color2_alpha}), 
                      stop:0.6 rgba(135,163,215,{color2_alpha}), 
                      stop:1 rgba(163,135,215,{color1_alpha}))"""
        
        style = f"""
            QProgressBar {{
                background-color: #2a2a2a;
                border: none;
                border-radius: 2px;
                margin: 0px;
                padding: 0px;
            }}
            QProgressBar::chunk {{
                background: {gradient};
                border-radius: 2px;
            }}
        """
        
        self.loading_bar.setStyleSheet(style)