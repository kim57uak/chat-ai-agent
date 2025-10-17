"""
Dialog Style Manager
다이얼로그 스타일 관리
"""

from ui.styles.theme_manager import theme_manager


class DialogStyleManager:
    """다이얼로그 스타일 관리 - Strategy 패턴"""
    
    @staticmethod
    def get_dialog_style() -> str:
        """다이얼로그 전체 스타일"""
        colors = theme_manager.material_manager.get_theme_colors()
        
        return f"""
            QDialog {{
                background-color: {colors.get('background', '#1e293b')};
                color: {colors.get('text_primary', '#f1f5f9')};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                border: none;
            }}
            QLabel {{
                color: {colors.get('text_primary', '#f1f5f9')};
                font-size: 14px;
                font-weight: 500;
                padding: 4px 0;
                background: transparent;
            }}
            QComboBox {{
                background-color: {colors.get('surface', '#334155')};
                color: {colors.get('text_primary', '#f1f5f9')};
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox:hover {{
                background-color: {colors.get('surface_variant', '#475569')};
                border-color: {colors.get('primary', '#6366f1')};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {colors.get('text_primary', '#f1f5f9')};
                width: 0;
                height: 0;
            }}
            QLineEdit {{
                background-color: {colors.get('surface', '#334155')};
                color: {colors.get('text_primary', '#f1f5f9')};
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {colors.get('primary', '#6366f1')};
                background-color: {colors.get('surface_variant', '#475569')};
            }}
            QSpinBox {{
                background-color: {colors.get('surface', '#334155')};
                color: {colors.get('text_primary', '#f1f5f9')};
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                min-height: 20px;
            }}
            QSpinBox:hover {{
                background-color: {colors.get('surface_variant', '#475569')};
                border-color: {colors.get('primary', '#6366f1')};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {colors.get('primary', '#6366f1')};
                border: none;
                width: 16px;
                border-radius: 3px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {colors.get('primary_variant', '#4f46e5')};
            }}
            QCheckBox {{
                color: {colors.get('text_primary', '#f1f5f9')};
                font-size: 14px;
                font-weight: 500;
                spacing: 8px;
                background: transparent;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 3px;
                background-color: {colors.get('surface', '#334155')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors.get('primary', '#6366f1')};
                border-color: {colors.get('primary', '#6366f1')};
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors.get('primary', '#6366f1')};
            }}
            QGroupBox {{
                color: {colors.get('text_primary', '#f1f5f9')};
                font-size: 16px;
                font-weight: 600;
                border: 1px solid {colors.get('border', '#475569')};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background-color: {colors.get('surface', 'rgba(51, 65, 85, 0.5)')};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 4px 12px;
                background-color: {colors.get('primary', '#6366f1')};
                color: {colors.get('on_primary', '#ffffff')};
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
            }}
        """
    
    @staticmethod
    def get_save_button_style() -> str:
        """저장 버튼 스타일"""
        colors = theme_manager.material_manager.get_theme_colors()
        
        return f"""
            QPushButton {{
                background-color: {colors.get('primary', '#6366f1')};
                color: {colors.get('on_primary', '#ffffff')};
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                padding: 10px 20px;
                margin: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('primary_variant', '#4f46e5')};
            }}
            QPushButton:pressed {{
                background-color: {colors.get('primary_dark', '#3730a3')};
            }}
        """
    
    @staticmethod
    def get_cancel_button_style() -> str:
        """취소 버튼 스타일"""
        colors = theme_manager.material_manager.get_theme_colors()
        
        return f"""
            QPushButton {{
                background-color: {colors.get('surface_variant', '#475569')};
                color: #ffffff;
                border: 1px solid {colors.get('border', '#64748b')};
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                padding: 10px 20px;
                margin: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors.get('error', '#ef4444')};
                color: {colors.get('on_error', '#ffffff')};
                border-color: {colors.get('error', '#ef4444')};
            }}
            QPushButton:pressed {{
                background-color: {colors.get('error_dark', '#dc2626')};
            }}
        """
