"""
Theme Color Contrast Analyzer
테마별 색상 대비율 분석 및 가독성 최적화
"""

import json
from pathlib import Path


def hex_to_rgb(hex_color):
    """HEX 색상을 RGB로 변환"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (0, 0, 0)


def calculate_luminance(rgb):
    """상대 휘도 계산 (WCAG 2.0)"""
    r, g, b = [x / 255.0 for x in rgb]
    
    def adjust(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = adjust(r), adjust(g), adjust(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(color1, color2):
    """두 색상 간 대비율 계산"""
    lum1 = calculate_luminance(hex_to_rgb(color1))
    lum2 = calculate_luminance(hex_to_rgb(color2))
    
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)


def get_contrast_grade(ratio):
    """대비율에 따른 등급"""
    if ratio >= 7.0:
        return "AAA (Excellent)"
    elif ratio >= 4.5:
        return "AA (Good)"
    elif ratio >= 3.0:
        return "AA Large (Acceptable)"
    else:
        return "Fail (Poor)"


def analyze_theme(theme_name, theme_data):
    """테마 분석"""
    colors = theme_data.get('colors', {})
    
    bg = colors.get('background', '#000000')
    surface = colors.get('surface', '#000000')
    text_primary = colors.get('text_primary', '#ffffff')
    text_secondary = colors.get('text_secondary', '#cccccc')
    primary = colors.get('primary', '#6366f1')
    
    # 주요 대비율 계산
    results = {
        'theme': theme_name,
        'type': theme_data.get('type', 'unknown'),
        'contrasts': {
            'text_on_background': {
                'ratio': calculate_contrast_ratio(text_primary, bg),
                'colors': f"{text_primary} on {bg}"
            },
            'text_on_surface': {
                'ratio': calculate_contrast_ratio(text_primary, surface),
                'colors': f"{text_primary} on {surface}"
            },
            'secondary_text_on_background': {
                'ratio': calculate_contrast_ratio(text_secondary, bg),
                'colors': f"{text_secondary} on {bg}"
            },
            'white_on_primary': {
                'ratio': calculate_contrast_ratio('#ffffff', primary),
                'colors': f"#ffffff on {primary}"
            }
        }
    }
    
    # 등급 추가
    for key, value in results['contrasts'].items():
        value['grade'] = get_contrast_grade(value['ratio'])
    
    return results


def suggest_improvements(analysis):
    """개선 제안"""
    suggestions = []
    
    for key, contrast in analysis['contrasts'].items():
        if contrast['ratio'] < 4.5:
            suggestions.append({
                'issue': key,
                'current_ratio': contrast['ratio'],
                'colors': contrast['colors'],
                'recommendation': 'Increase contrast to at least 4.5:1 for normal text'
            })
    
    return suggestions


def main():
    # theme.json 로드
    theme_path = Path('/Users/dolpaks/Downloads/project/chat-ai-agent/theme.json')
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme_config = json.load(f)
    
    print("=" * 80)
    print("THEME COLOR CONTRAST ANALYSIS")
    print("=" * 80)
    print()
    
    all_results = {}
    problem_themes = []
    
    for theme_name, theme_data in theme_config['themes'].items():
        analysis = analyze_theme(theme_name, theme_data)
        all_results[theme_name] = analysis
        
        print(f"Theme: {theme_name} ({analysis['type']})")
        print("-" * 80)
        
        has_issues = False
        for key, contrast in analysis['contrasts'].items():
            ratio = contrast['ratio']
            grade = contrast['grade']
            status = "✓" if ratio >= 4.5 else "✗"
            
            print(f"  {status} {key:30s}: {ratio:5.2f}:1  [{grade}]")
            
            if ratio < 4.5:
                has_issues = True
        
        if has_issues:
            problem_themes.append(theme_name)
            suggestions = suggest_improvements(analysis)
            print("\n  Suggestions:")
            for sug in suggestions:
                print(f"    - {sug['issue']}: {sug['recommendation']}")
        
        print()
    
    # 요약
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total themes analyzed: {len(all_results)}")
    print(f"Themes with contrast issues: {len(problem_themes)}")
    
    if problem_themes:
        print("\nThemes needing improvement:")
        for theme in problem_themes:
            print(f"  - {theme}")
    else:
        print("\nAll themes meet WCAG AA standards! ✓")
    
    # 권장 색상 생성
    print("\n" + "=" * 80)
    print("RECOMMENDED COLOR ADJUSTMENTS")
    print("=" * 80)
    
    for theme_name in problem_themes:
        theme_data = theme_config['themes'][theme_name]
        colors = theme_data.get('colors', {})
        theme_type = theme_data.get('type', 'unknown')
        
        print(f"\n{theme_name}:")
        
        # 다크 테마
        if theme_type == 'dark':
            print("  Recommended adjustments for dark theme:")
            print(f"    text_primary: '#f5f5f5' or brighter")
            print(f"    text_secondary: '#d0d0d0' or brighter")
            print(f"    surface: Lighter than current (increase RGB values by 10-20)")
        
        # 라이트 테마
        else:
            print("  Recommended adjustments for light theme:")
            print(f"    text_primary: '#1a1a1a' or darker")
            print(f"    text_secondary: '#4a4a4a' or darker")
            print(f"    surface: Ensure sufficient contrast with text")


if __name__ == "__main__":
    main()
