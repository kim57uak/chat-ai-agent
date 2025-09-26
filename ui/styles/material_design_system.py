"""Google Material Design System Implementation"""

from typing import Dict, Any, Optional
from enum import Enum
import json
import os


class MaterialElevation(Enum):
    """Material Design Elevation Levels"""
    LEVEL_0 = 0   # Surface
    LEVEL_1 = 1   # Cards, Sheets
    LEVEL_2 = 2   # FAB, Snackbar
    LEVEL_3 = 3   # Navigation Drawer
    LEVEL_4 = 4   # App Bar
    LEVEL_5 = 5   # Modal


class MaterialTypography:
    """Material Design Typography Scale"""
    
    @staticmethod
    def get_typography_styles() -> Dict[str, Dict[str, str]]:
        return {
            "headline1": {
                "font-size": "96px",
                "font-weight": "300",
                "line-height": "1.167",
                "letter-spacing": "-1.5px"
            },
            "headline2": {
                "font-size": "60px", 
                "font-weight": "300",
                "line-height": "1.2",
                "letter-spacing": "-0.5px"
            },
            "headline3": {
                "font-size": "48px",
                "font-weight": "400", 
                "line-height": "1.167",
                "letter-spacing": "0px"
            },
            "headline4": {
                "font-size": "34px",
                "font-weight": "400",
                "line-height": "1.235", 
                "letter-spacing": "0.25px"
            },
            "headline5": {
                "font-size": "24px",
                "font-weight": "400",
                "line-height": "1.334",
                "letter-spacing": "0px"
            },
            "headline6": {
                "font-size": "20px",
                "font-weight": "500",
                "line-height": "1.6",
                "letter-spacing": "0.15px"
            },
            "subtitle1": {
                "font-size": "16px",
                "font-weight": "400",
                "line-height": "1.75",
                "letter-spacing": "0.15px"
            },
            "subtitle2": {
                "font-size": "14px",
                "font-weight": "500", 
                "line-height": "1.57",
                "letter-spacing": "0.1px"
            },
            "body1": {
                "font-size": "16px",
                "font-weight": "400",
                "line-height": "1.5",
                "letter-spacing": "0.15px"
            },
            "body2": {
                "font-size": "14px",
                "font-weight": "400",
                "line-height": "1.43",
                "letter-spacing": "0.25px"
            },
            "button": {
                "font-size": "14px",
                "font-weight": "500",
                "line-height": "1.75",
                "letter-spacing": "0.4px",
                "text-transform": "uppercase"
            },
            "caption": {
                "font-size": "12px",
                "font-weight": "400",
                "line-height": "1.66",
                "letter-spacing": "0.4px"
            },
            "overline": {
                "font-size": "10px",
                "font-weight": "400", 
                "line-height": "2.66",
                "letter-spacing": "1.5px",
                "text-transform": "uppercase"
            }
        }


class MaterialDesignSystem:
    """Complete Material Design System Implementation"""
    
    def __init__(self):
        self.typography = MaterialTypography()
        self.elevation_shadows = self._create_elevation_shadows()
        
    def _create_elevation_shadows(self) -> Dict[int, str]:
        """Create Material Design elevation shadows"""
        return {
            0: "none",
            1: "0px 2px 1px -1px rgba(0,0,0,0.2), 0px 1px 1px 0px rgba(0,0,0,0.14), 0px 1px 3px 0px rgba(0,0,0,0.12)",
            2: "0px 3px 1px -2px rgba(0,0,0,0.2), 0px 2px 2px 0px rgba(0,0,0,0.14), 0px 1px 5px 0px rgba(0,0,0,0.12)",
            3: "0px 3px 3px -2px rgba(0,0,0,0.2), 0px 3px 4px 0px rgba(0,0,0,0.14), 0px 1px 8px 0px rgba(0,0,0,0.12)",
            4: "0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12)",
            5: "0px 3px 5px -1px rgba(0,0,0,0.2), 0px 5px 8px 0px rgba(0,0,0,0.14), 0px 1px 14px 0px rgba(0,0,0,0.12)",
            6: "0px 3px 5px -1px rgba(0,0,0,0.2), 0px 6px 10px 0px rgba(0,0,0,0.14), 0px 1px 18px 0px rgba(0,0,0,0.12)",
            8: "0px 5px 5px -3px rgba(0,0,0,0.2), 0px 8px 10px 1px rgba(0,0,0,0.14), 0px 3px 14px 2px rgba(0,0,0,0.12)",
            12: "0px 7px 8px -4px rgba(0,0,0,0.2), 0px 12px 17px 2px rgba(0,0,0,0.14), 0px 5px 22px 4px rgba(0,0,0,0.12)",
            16: "0px 8px 10px -5px rgba(0,0,0,0.2), 0px 16px 24px 2px rgba(0,0,0,0.14), 0px 6px 30px 5px rgba(0,0,0,0.12)",
            24: "0px 11px 15px -7px rgba(0,0,0,0.2), 0px 24px 38px 3px rgba(0,0,0,0.14), 0px 9px 46px 8px rgba(0,0,0,0.12)"
        }
    
    def get_elevation_shadow(self, level: int) -> str:
        """Get shadow for elevation level"""
        return self.elevation_shadows.get(level, self.elevation_shadows[0])
    
    def get_border_radius(self, size: str = "medium") -> str:
        """Get Material Design border radius"""
        radius_map = {
            "none": "0px",
            "small": "4px", 
            "medium": "8px",
            "large": "12px",
            "extra_large": "16px",
            "full": "50%"
        }
        return radius_map.get(size, "8px")
    
    def get_spacing(self, multiplier: int = 1) -> str:
        """Get Material Design spacing (8px base unit)"""
        return f"{8 * multiplier}px"
    
    def create_material_button_style(self, colors: Dict[str, str], variant: str = "contained") -> str:
        """Create Material Design button styles"""
        typography = self.typography.get_typography_styles()["button"]
        
        if variant == "contained":
            return f"""
                QPushButton {{
                    background-color: {colors.get('primary', '#1976d2')};
                    color: {colors.get('on_primary', '#ffffff')};
                    border: none;
                    border-radius: {self.get_border_radius('small')};
                    padding: {self.get_spacing(1)} {self.get_spacing(2)};
                    font-size: {typography['font-size']};
                    font-weight: {typography['font-weight']};
                    letter-spacing: {typography['letter-spacing']};
                    text-transform: {typography.get('text-transform', 'none')};
                    box-shadow: {self.get_elevation_shadow(2)};
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {colors.get('primary_variant', '#1565c0')};
                    box-shadow: {self.get_elevation_shadow(4)};
                }}
                QPushButton:pressed {{
                    box-shadow: {self.get_elevation_shadow(8)};
                }}
                QPushButton:disabled {{
                    background-color: rgba(0, 0, 0, 0.12);
                    color: rgba(0, 0, 0, 0.26);
                    box-shadow: none;
                }}
            """
        elif variant == "outlined":
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {colors.get('primary', '#1976d2')};
                    border: 1px solid {colors.get('primary', '#1976d2')};
                    border-radius: {self.get_border_radius('small')};
                    padding: {self.get_spacing(1)} {self.get_spacing(2)};
                    font-size: {typography['font-size']};
                    font-weight: {typography['font-weight']};
                    letter-spacing: {typography['letter-spacing']};
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: rgba({self._hex_to_rgb(colors.get('primary', '#1976d2'))}, 0.04);
                }}
                QPushButton:pressed {{
                    background-color: rgba({self._hex_to_rgb(colors.get('primary', '#1976d2'))}, 0.12);
                }}
            """
        else:  # text variant
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {colors.get('primary', '#1976d2')};
                    border: none;
                    border-radius: {self.get_border_radius('small')};
                    padding: {self.get_spacing(1)} {self.get_spacing(2)};
                    font-size: {typography['font-size']};
                    font-weight: {typography['font-weight']};
                    letter-spacing: {typography['letter-spacing']};
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: rgba({self._hex_to_rgb(colors.get('primary', '#1976d2'))}, 0.04);
                }}
                QPushButton:pressed {{
                    background-color: rgba({self._hex_to_rgb(colors.get('primary', '#1976d2'))}, 0.12);
                }}
            """
    
    def create_material_card_style(self, colors: Dict[str, str], elevation: int = 1) -> str:
        """Create Material Design card styles"""
        return f"""
            QWidget {{
                background-color: {colors.get('surface', '#ffffff')};
                color: {colors.get('on_surface', '#000000')};
                border-radius: {self.get_border_radius('medium')};
                box-shadow: {self.get_elevation_shadow(elevation)};
                padding: {self.get_spacing(2)};
            }}
        """
    
    def create_material_input_style(self, colors: Dict[str, str]) -> str:
        """Create Material Design input field styles"""
        return f"""
            QTextEdit, QLineEdit {{
                background-color: {colors.get('surface', '#ffffff')};
                color: {colors.get('on_surface', '#000000')};
                border: 1px solid {colors.get('divider', '#e0e0e0')};
                border-radius: {self.get_border_radius('small')};
                padding: {self.get_spacing(2)};
                font-size: 16px;
                line-height: 1.5;
                selection-background-color: {colors.get('primary', '#1976d2')};
                selection-color: {colors.get('on_primary', '#ffffff')};
            }}
            QTextEdit:focus, QLineEdit:focus {{
                border-color: {colors.get('primary', '#1976d2')};
                border-width: 2px;
            }}
            QTextEdit:disabled, QLineEdit:disabled {{
                background-color: rgba(0, 0, 0, 0.06);
                color: rgba(0, 0, 0, 0.38);
            }}
        """
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB string"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        return "0, 0, 0"


# Global Material Design System instance
material_design_system = MaterialDesignSystem()