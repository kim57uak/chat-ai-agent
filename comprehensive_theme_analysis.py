"""
Comprehensive Theme Color Analysis
전체 애플리케이션의 CSS 색상 대비 종합 분석
"""

import json
from pathlib import Path


def hex_to_rgb(hex_color):
    """HEX 색상을 RGB로 변환"""
    hex_color = hex_color.lstrip('#')
    if 'rgba' in hex_color or 'rgb' in hex_color:
        return (128, 128, 128)  # 기본값
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return (128, 128, 128)


def calculate_luminance(rgb):
    """상대 휘도 계산"""
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


def get_grade(ratio):
    """대비율 등급"""
    if ratio >= 7.0:
        return "AAA"
    elif ratio >= 4.5:
        return "AA"
    elif ratio >= 3.0:
        return "AA-Large"
    else:
        return "FAIL"


def suggest_color_adjustment(bg_color, target_ratio=4.5, is_light_text=True):
    """배경색에 맞는 텍스트 색상 제안"""
    bg_lum = calculate_luminance(hex_to_rgb(bg_color))
    
    if is_light_text:
        # 밝은 텍스트 (흰색 계열)
        if bg_lum < 0.18:  # 어두운 배경
            return "#ffffff", "Use white text"
        else:
            return "#000000", "Background too light for white text, use dark text"
    else:
        # 어두운 텍스트 (검은색 계열)
        if bg_lum > 0.18:  # 밝은 배경
            return "#000000", "Use black text"
        else:
            return "#ffffff", "Background too dark for black text, use light text"


def analyze_comprehensive_theme(theme_name, theme_data):
    """테마의 모든 색상 조합 분석"""
    colors = theme_data.get('colors', {})
    
    # 주요 색상 추출
    bg = colors.get('background', '#000000')
    surface = colors.get('surface', '#000000')
    primary = colors.get('primary', '#6366f1')
    primary_variant = colors.get('primary_variant', primary)
    secondary = colors.get('secondary', '#8dc4d4')
    text_primary = colors.get('text_primary', '#ffffff')
    text_secondary = colors.get('text_secondary', '#cccccc')
    border = colors.get('border', '#475569')
    surface_variant = colors.get('surface_variant', surface)
    
    # 모든 중요한 조합 분석
    combinations = {
        # 기본 텍스트
        'text_on_background': (text_primary, bg, 'Primary text on background'),
        'text_on_surface': (text_primary, surface, 'Primary text on surface'),
        'secondary_text_on_bg': (text_secondary, bg, 'Secondary text on background'),
        'secondary_text_on_surface': (text_secondary, surface, 'Secondary text on surface'),
        
        # 버튼
        'white_on_primary': ('#ffffff', primary, 'Button text (white on primary)'),
        'white_on_primary_variant': ('#ffffff', primary_variant, 'Button hover (white on primary_variant)'),
        'white_on_secondary': ('#ffffff', secondary, 'Secondary button text'),
        
        # 입력 필드
        'text_on_surface_variant': (text_primary, surface_variant, 'Input field text'),
        'border_on_surface': (border, surface, 'Border visibility on surface'),
        
        # 특수 상태
        'primary_on_surface': (primary, surface, 'Primary color on surface (links, icons)'),
        'secondary_on_surface': (secondary, surface, 'Secondary color on surface'),
    }
    
    results = {}
    issues = []
    
    for key, (fg, bg_color, desc) in combinations.items():
        ratio = calculate_contrast_ratio(fg, bg_color)
        grade = get_grade(ratio)
        
        results[key] = {
            'ratio': ratio,
            'grade': grade,
            'description': desc,
            'colors': f"{fg} on {bg_color}"
        }
        
        if ratio < 4.5:
            issues.append({
                'key': key,
                'description': desc,
                'ratio': ratio,
                'grade': grade,
                'suggestion': suggest_color_adjustment(bg_color, 4.5, fg.startswith('#f') or fg.startswith('#e'))
            })
    
    return {
        'theme': theme_name,
        'type': theme_data.get('type', 'unknown'),
        'results': results,
        'issues': issues,
        'issue_count': len(issues)
    }


def generate_theme_recommendations(analysis):
    """테마별 구체적인 색상 권장사항 생성"""
    recommendations = {}
    
    if analysis['issue_count'] == 0:
        return {"status": "✓ All combinations meet WCAG AA standards"}
    
    colors = {}
    
    # 문제별 권장사항
    for issue in analysis['issues']:
        key = issue['key']
        
        if 'text_on' in key:
            if 'primary' in key:
                colors['text_primary'] = issue['suggestion'][0]
            elif 'secondary' in key:
                colors['text_secondary'] = issue['suggestion'][0]
        
        elif 'white_on_primary' in key:
            colors['primary'] = "Darken primary color by 15-20%"
        
        elif 'white_on_secondary' in key:
            colors['secondary'] = "Darken secondary color by 15-20%"
    
    return colors


def main():
    theme_path = Path('/Users/dolpaks/Downloads/project/chat-ai-agent/theme.json')
    with open(theme_path, 'r', encoding='utf-8') as f:
        theme_config = json.load(f)
    
    print("=" * 100)
    print("COMPREHENSIVE THEME COLOR CONTRAST ANALYSIS")
    print("=" * 100)
    print()
    
    all_analyses = {}
    problem_themes = []
    
    for theme_name, theme_data in theme_config['themes'].items():
        analysis = analyze_comprehensive_theme(theme_name, theme_data)
        all_analyses[theme_name] = analysis
        
        print(f"Theme: {theme_name} ({analysis['type']})")
        print("-" * 100)
        
        # 결과 출력
        for key, result in analysis['results'].items():
            ratio = result['ratio']
            grade = result['grade']
            status = "✓" if ratio >= 4.5 else "✗"
            
            print(f"  {status} {result['description']:45s}: {ratio:5.2f}:1  [{grade:8s}]")
        
        if analysis['issue_count'] > 0:
            problem_themes.append(theme_name)
            print(f"\n  ⚠ Issues found: {analysis['issue_count']}")
            
            recommendations = generate_theme_recommendations(analysis)
            if recommendations and 'status' not in recommendations:
                print("  Recommendations:")
                for key, value in recommendations.items():
                    print(f"    • {key}: {value}")
        
        print()
    
    # 요약
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total themes: {len(all_analyses)}")
    print(f"Themes with issues: {len(problem_themes)}")
    print(f"Pass rate: {((len(all_analyses) - len(problem_themes)) / len(all_analyses) * 100):.1f}%")
    
    if problem_themes:
        print("\nThemes needing improvement:")
        for theme in problem_themes:
            issue_count = all_analyses[theme]['issue_count']
            print(f"  • {theme}: {issue_count} issues")
    else:
        print("\n✓ All themes meet WCAG AA standards!")
    
    # 가장 문제가 많은 테마
    print("\n" + "=" * 100)
    print("TOP 5 THEMES WITH MOST ISSUES")
    print("=" * 100)
    
    sorted_themes = sorted(all_analyses.items(), key=lambda x: x[1]['issue_count'], reverse=True)[:5]
    for theme_name, analysis in sorted_themes:
        if analysis['issue_count'] > 0:
            print(f"\n{theme_name}: {analysis['issue_count']} issues")
            for issue in analysis['issues'][:3]:  # 상위 3개만
                print(f"  • {issue['description']}: {issue['ratio']:.2f}:1 [{issue['grade']}]")


if __name__ == "__main__":
    main()
