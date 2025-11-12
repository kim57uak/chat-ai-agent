"""
RAG Management Window Styles
"""

from ui.styles.material_theme_manager import material_theme_manager


class RAGManagementStyles:
    """RAG 관리 창 스타일 관리"""
    
    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
        """Convert hex to RGBA"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}, {alpha}"
        return f"30, 30, 30, {alpha}"
    
    @staticmethod
    def _adjust_color(hex_color: str, factor: float) -> str:
        """Adjust color brightness"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = min(255, int(int(hex_color[0:2], 16) * factor))
            g = min(255, int(int(hex_color[2:4], 16) * factor))
            b = min(255, int(int(hex_color[4:6], 16) * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        return hex_color
    
    @classmethod
    def get_stylesheet(cls) -> str:
        """Get complete stylesheet for RAG management window"""
        colors = material_theme_manager.get_theme_colors()
        glass_config = material_theme_manager.get_glassmorphism_config()
        
        bg = colors.get('background', '#121212')
        surface = colors.get('surface', '#1e1e1e')
        primary = colors.get('primary', '#bb86fc')
        text = colors.get('text_primary', '#ffffff')
        text_sec = colors.get('text_secondary', '#b3b3b3')
        
        border_op = glass_config.get('border_opacity', 0.2)
        
        return f"""
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {bg}, stop:0.3 {surface}, stop:0.7 {surface}, stop:1 {bg});
        }}
        
        QFrame#glassToolbar {{
            background: rgba({cls._hex_to_rgba(surface, 0.7)});
            border: none;
        }}
        
        QFrame#glassPanel {{
            background: rgba({cls._hex_to_rgba(surface, 0.5)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
            margin: 0px 4px 4px 4px;
        }}
        
        QLabel#panelHeader {{
            color: {text};
            padding: 2px 0;
            background: transparent;
            margin-bottom: 2px;
        }}
        
        QPushButton#primaryBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {cls._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 7px;
            padding: 7px 15px;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 0.3px;
        }}
        
        QPushButton#primaryBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {cls._adjust_color(primary, 1.2)}, stop:1 {primary});
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        
        QPushButton#successBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #4CAF50, stop:1 #388E3C);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 7px;
            padding: 7px 15px;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 0.3px;
        }}
        
        QPushButton#successBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #66BB6A, stop:1 #4CAF50);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        
        QPushButton#warningBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FF9800, stop:1 #F57C00);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 7px;
            padding: 7px 15px;
            font-size: 14px;
            font-weight: bold;
            letter-spacing: 0.3px;
        }}
        
        QPushButton#warningBtn:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFB74D, stop:1 #FF9800);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        
        QTreeWidget, QListWidget#glassList {{
            background: {surface};
            border: 1px solid rgba(255, 255, 255, {border_op * 0.5});
            border-radius: 10px;
            color: {text};
            padding: 6px;
            font-size: 13px;
        }}
        
        QTreeWidget::item, QListWidget::item {{
            padding: 6px 8px;
            border-radius: 6px;
            margin: 1px 0;
            color: {text};
        }}
        
        QTreeWidget::item:hover, QListWidget::item:hover {{
            background: rgba({cls._hex_to_rgba(primary, 0.2)});
            color: {text};
        }}
        
        QTreeWidget::item:selected, QListWidget::item:selected {{
            background: rgba({cls._hex_to_rgba(primary, 0.6)});
            color: white;
        }}
        
        QTextEdit#glassPreview {{
            background: {surface};
            border: 1px solid rgba(255, 255, 255, {border_op * 0.5});
            border-radius: 10px;
            color: {text};
            padding: 10px;
            font-size: 13px;
            line-height: 1.5;
        }}
        
        QSplitter::handle {{
            background: transparent;
            border: none;
        }}
        
        QSplitter::handle:horizontal {{
            width: 1px;
            background: transparent;
        }}
        
        QSplitter::handle:vertical {{
            height: 1px;
            background: transparent;
        }}
        
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: rgba({cls._hex_to_rgba(primary, 0.5)});
            border-radius: 5px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: rgba({cls._hex_to_rgba(primary, 0.7)});
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        
        QComboBox#chunkingCombo {{
            background: rgba({cls._hex_to_rgba(surface, 0.7)});
            color: {text};
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 7px;
            padding: 6px 12px;
            font-size: 14px;
            min-width: 120px;
        }}
        
        QComboBox#chunkingCombo:hover {{
            border: 1px solid rgba(255, 255, 255, {border_op * 1.5});
        }}
        
        QComboBox#chunkingCombo::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox#chunkingCombo QAbstractItemView {{
            background: {surface};
            color: {text};
            border: 1px solid rgba(255, 255, 255, {border_op});
            selection-background-color: rgba({cls._hex_to_rgba(primary, 0.4)});
        }}
        
        QProgressDialog {{
            background: rgba({cls._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
        }}
        
        QProgressDialog QLabel {{
            color: {text};
            font-size: 13px;
            padding: 10px;
        }}
        
        QProgressDialog QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {cls._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 11px;
            min-width: 80px;
        }}
        
        QProgressDialog QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {cls._adjust_color(primary, 1.2)}, stop:1 {primary});
        }}
        
        QProgressBar {{
            background: rgba({cls._hex_to_rgba(bg, 0.5)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 8px;
            text-align: center;
            color: {text};
            font-size: 12px;
            font-weight: bold;
            min-height: 25px;
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {cls._adjust_color(primary, 1.2)});
            border-radius: 7px;
        }}
        
        QMessageBox {{
            background: rgba({cls._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
        }}
        
        QMessageBox QLabel {{
            color: {text};
            font-size: 13px;
            padding: 10px;
        }}
        
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {cls._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 11px;
            min-width: 80px;
        }}
        
        QMessageBox QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {cls._adjust_color(primary, 1.2)}, stop:1 {primary});
        }}
        
        QDialog {{
            background: rgba({cls._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 12px;
        }}
        
        QDialog QLabel {{
            color: {text};
        }}
        
        QDialog QLineEdit, QDialog QTextEdit {{
            background: rgba({cls._hex_to_rgba(bg, 0.5)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 6px;
            color: {text};
            padding: 6px;
            font-size: 12px;
        }}
        
        QDialog QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {primary}, stop:1 {cls._adjust_color(primary, 0.8)});
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 11px;
            min-width: 80px;
        }}
        
        QDialog QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {cls._adjust_color(primary, 1.2)}, stop:1 {primary});
        }}
        
        QMenu {{
            background: rgba({cls._hex_to_rgba(surface, 0.95)});
            border: 1px solid rgba(255, 255, 255, {border_op});
            border-radius: 8px;
            padding: 4px;
        }}
        
        QMenu::item {{
            color: {text};
            padding: 6px 20px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background: rgba({cls._hex_to_rgba(primary, 0.4)});
        }}
        """
