"""Material Design Stylesheet Generator"""

from typing import Dict


def create_material_stylesheet(colors: Dict[str, str], material_design) -> str:
    """Create complete Material Design stylesheet"""
    
    # Material Design 컴포넌트 스타일 생성
    button_style = material_design.create_material_button_style(colors, "contained")
    input_style = material_design.create_material_input_style(colors)
    
    # 기본 Material Design 스타일시트
    return f"""
    * {{
        font-family: 'Roboto', 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    }}
    
    QMainWindow {{
        background-color: {colors.get('background', '#ffffff')};
        color: {colors.get('text_primary', '#000000')};
    }}
    
    QWidget {{
        background-color: {colors.get('background', '#ffffff')};
        color: {colors.get('text_primary', '#000000')};
    }}
    
    QMenuBar {{
        background-color: {colors.get('surface', '#ffffff')};
        color: {colors.get('text_primary', '#000000')};
        border: none;
        border-bottom: 1px solid {colors.get('divider', '#e0e0e0')};
        padding: {material_design.get_spacing(1)} 0;
        font-weight: 500;
    }}
    
    QMenuBar::item {{
        background: transparent;
        padding: {material_design.get_spacing(1)} {material_design.get_spacing(2)};
        border-radius: {material_design.get_border_radius('small')};
        margin: 0 {material_design.get_spacing(0.5)};
    }}
    
    QMenuBar::item:selected {{
        background-color: rgba({material_design._hex_to_rgb(colors.get('primary', '#1976d2'))}, 0.08);
        color: {colors.get('primary', '#1976d2')};
    }}
    
    QMenu {{
        background-color: {colors.get('surface', '#ffffff')};
        color: {colors.get('text_primary', '#000000')};
        border: none;
        border-radius: {material_design.get_border_radius('small')};
        box-shadow: {material_design.get_elevation_shadow(8)};
        padding: {material_design.get_spacing(1)};
    }}
    
    QMenu::item {{
        padding: {material_design.get_spacing(1.5)} {material_design.get_spacing(2)};
        border-radius: {material_design.get_border_radius('small')};
        margin: {material_design.get_spacing(0.25)} 0;
    }}
    
    QMenu::item:selected {{
        background-color: rgba({material_design._hex_to_rgb(colors.get('primary', '#1976d2'))}, 0.08);
        color: {colors.get('primary', '#1976d2')};
    }}
    
    {button_style}
    {input_style}
    
    QScrollBar:vertical {{
        background-color: {colors.get('scrollbar_track', '#f5f5f5')};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors.get('scrollbar', '#bdbdbd')};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors.get('primary', '#1976d2')};
    }}
    
    QSplitter::handle {{
        background-color: {colors.get('divider', '#e0e0e0')};
        border: 1px solid {colors.get('divider', '#e0e0e0')};
        border-radius: {material_design.get_border_radius('small')};
        margin: 2px;
    }}
    
    QSplitter::handle:hover {{
        background-color: {colors.get('primary', '#1976d2')};
        border-color: {colors.get('primary', '#1976d2')};
    }}
    """