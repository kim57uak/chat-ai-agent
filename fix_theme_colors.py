#!/usr/bin/env python3
"""
테마 파일의 텍스트 색상을 WCAG 대비 기준으로 자동 수정
"""
import json
import re

def calculate_luminance(hex_color):
    """색상의 밝기 계산"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    except:
        return 0.5

def calculate_contrast(color1, color2):
    """두 색상 간 대비 계산 (WCAG)"""
    l1 = calculate_luminance(color1)
    l2 = calculate_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def extract_hex_color(color_str):
    """복잡한 색상 문자열에서 hex 추출"""
    if color_str.startswith('#'):
        return color_str
    match = re.search(r'#[0-9A-Fa-f]{6}', color_str)
    return match.group(0) if match else '#ffffff'

def is_dark_background(bg_color):
    """배경색이 어두운지 판단"""
    hex_color = extract_hex_color(bg_color)
    return calculate_luminance(hex_color) < 0.5

def fix_theme_colors(theme_path='theme.json'):
    """테마 파일의 텍스트 색상 수정"""
    with open(theme_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_count = 0
    
    for theme_key, theme_data in data['themes'].items():
        colors = theme_data.get('colors', {})
        surface = colors.get('surface', colors.get('background', '#ffffff'))
        surface_hex = extract_hex_color(surface)
        
        is_dark = is_dark_background(surface)
        
        if is_dark:
            target_primary = '#ffffff'
            target_secondary = '#a0a0a0'
        else:
            target_primary = '#1a1a1a'
            target_secondary = '#4a4a4a'
        
        # text_primary 검증
        if 'text_primary' in colors:
            old = colors['text_primary']
            contrast = calculate_contrast(old, surface_hex)
            if contrast < 4.5:
                colors['text_primary'] = target_primary
                print(f"{theme_key}: text_primary {old} → {target_primary} (대비 {contrast:.2f})")
                fixed_count += 1
        
        # text_secondary 검증
        if 'text_secondary' in colors:
            old = colors['text_secondary']
            contrast = calculate_contrast(old, surface_hex)
            if contrast < 3.0:
                colors['text_secondary'] = target_secondary
                print(f"{theme_key}: text_secondary {old} → {target_secondary} (대비 {contrast:.2f})")
                fixed_count += 1
    
    with open(theme_path + '.backup', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    with open(theme_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 총 {fixed_count}개 색상 수정 완료")
    print(f"📦 백업 파일: {theme_path}.backup")

if __name__ == '__main__':
    fix_theme_colors()
