"""
CSS 변수 기반 테마 시스템 - 단순 레이어, 완전한 테마 지원
"""

def _calculate_luminance(hex_color: str) -> float:
    """색상의 밝기 계산"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    except:
        return 0.5

def _is_dark_background(bg_color: str) -> bool:
    """배경색이 어두운지 판단"""
    return _calculate_luminance(bg_color) < 0.5

def generate_css_variables(colors: dict, is_dark: bool = True) -> str:
    """테마 색상을 CSS 변수로 변환 - 테마 기반"""
    bg = colors.get('background', '#121212' if is_dark else '#ffffff')
    surface = colors.get('surface', '#1e1e1e' if is_dark else '#f8fafc')
    auto_dark = _is_dark_background(bg)
    
    # 테마에서 텍스트 색상 가져오기 - on_surface 우선, 없으면 text_primary
    text = colors.get('on_surface', colors.get('text_primary', '#ffffff' if auto_dark else '#1a1a1a'))
    text_dim = colors.get('text_secondary', '#a0a0a0' if auto_dark else '#666666')
    border = colors.get('divider', 'rgba(255, 255, 255, 0.12)' if auto_dark else 'rgba(0, 0, 0, 0.12)')
    
    # 테마 색상
    primary = colors.get('primary', '#bb86fc' if auto_dark else '#5b21b6')
    secondary = colors.get('secondary', '#03dac6' if auto_dark else '#0891b2')
    error = colors.get('error', '#cf6679' if auto_dark else '#dc2626')
    
    # 글래스모피즘 설정
    glass = colors.get('glass', {})
    glass_bg = glass.get('background', surface)
    glass_border = glass.get('border', border)
    glass_blur = glass.get('blur', '20px')
    glass_saturate = glass.get('saturate', '180%')
    
    return f"""
        :root {{
            --bg: {bg};
            --surface: {surface};
            --text: {text};
            --text-dim: {text_dim};
            --border: {border};
            --primary: {primary};
            --secondary: {secondary};
            --error: {error};
            --glass-bg: {glass_bg};
            --glass-border: {glass_border};
            --glass-blur: {glass_blur};
            --glass-saturate: {glass_saturate};
        }}
    """

def generate_base_css() -> str:
    """단순하고 강력한 기본 CSS"""
    return """
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box;
        }
        
        html, body {
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 15px;
            line-height: 1.6;
        }
        
        #messages { padding: 20px; min-height: 100vh; }
        
        .message {
            margin: 20px 0;
            padding: 20px;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            color: var(--text);
            backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
            -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .message-header {
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .message-sender-info {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: var(--text);
        }
        
        .message-buttons {
            display: flex;
            gap: 4px;
            opacity: 0.6;
            transition: opacity 0.2s;
        }
        
        .message:hover .message-buttons { opacity: 1; }
        
        .message-btn {
            border: none;
            background: transparent;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            color: var(--text);
        }
        
        .message-btn:hover { background: var(--border); }
        
        .btn-primary { color: var(--primary); }
        .btn-secondary { color: var(--secondary); }
        .btn-error { color: var(--error); }
        
        .message-content {
            color: var(--text) !important;
            line-height: 1.8;
        }
        
        .message-content *,
        .message-content p,
        .message-content div,
        .message-content span,
        .message-content li,
        .message-content td,
        .message-content th,
        .message-content strong,
        .message-content em,
        .message-content b,
        .message-content i,
        .message-content h1,
        .message-content h2,
        .message-content h3,
        .message-content h4,
        .message-content h5,
        .message-content h6 {
            color: var(--text) !important;
        }
        
        .message-timestamp {
            margin-top: 12px;
            padding-top: 8px;
            border-top: 1px solid var(--border);
            font-size: 12px;
            color: var(--text-dim);
            text-align: right;
        }
        
        a {
            color: var(--secondary);
            text-decoration: underline;
            transition: color 0.2s;
        }
        
        a:hover { color: var(--primary); }
        
        pre {
            background: var(--surface) !important;
            border: 1px solid var(--border);
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 12px 0;
        }
        
        pre code {
            background: transparent !important;
            color: var(--text) !important;
        }
        
        code {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            color: var(--text) !important;
            background: transparent;
        }
        
        p code {
            background: var(--surface) !important;
            border: 1px solid var(--border);
            padding: 2px 6px;
            border-radius: 3px;
            color: var(--text) !important;
        }
        
        .mermaid {
            background: var(--surface) !important;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
        }
        
        .mermaid svg {
            max-width: 100%;
            height: auto;
            background: transparent !important;
        }
        
        .mermaid .node rect,
        .mermaid .node circle,
        .mermaid .node ellipse,
        .mermaid .node polygon,
        .mermaid .node path {
            fill: var(--surface) !important;
            stroke: var(--primary) !important;
            stroke-width: 2px !important;
        }
        
        .mermaid text,
        .mermaid .nodeLabel,
        .mermaid .label,
        .mermaid .node .label,
        .mermaid tspan {
            fill: var(--text) !important;
            color: var(--text) !important;
            font-weight: 500 !important;
        }
        
        .mermaid .edgeLabel,
        .mermaid .edgeLabel rect,
        .mermaid .edgeLabel span {
            background-color: var(--surface) !important;
            fill: var(--surface) !important;
            color: var(--text) !important;
        }
        
        .mermaid .edgeLabel text {
            fill: var(--text) !important;
        }
        
        .mermaid .edgePath .path,
        .mermaid .flowchart-link {
            stroke: var(--text-dim) !important;
            stroke-width: 2px !important;
        }
        
        .mermaid .marker,
        .mermaid .arrowheadPath {
            fill: var(--text-dim) !important;
            stroke: var(--text-dim) !important;
        }
        
        .mermaid .cluster rect {
            fill: var(--surface) !important;
            stroke: var(--border) !important;
        }
        
        .mermaid .cluster text {
            fill: var(--text) !important;
        }
        
        ul, ol { margin: 8px 0; padding-left: 24px; }
        li { margin: 4px 0; }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
            background: transparent;
        }
        
        th, td {
            border: 1px solid var(--border);
            padding: 8px;
            text-align: left;
            color: var(--text) !important;
        }
        
        th { 
            font-weight: 600; 
            background: var(--primary);
            color: var(--text) !important;
        }
        
        td {
            background: transparent;
        }
        
        blockquote {
            border-left: 3px solid var(--primary);
            padding-left: 12px;
            margin: 12px 0;
            color: var(--text-dim);
        }
        
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--glass-bg);
            color: var(--text);
            border: 1px solid var(--glass-border);
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 9999;
            backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
            -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            animation: slideIn 0.3s;
        }
        
        .toast.success { border-color: var(--secondary); }
        .toast.error { border-color: var(--error); }
        
        @keyframes slideIn {
            from { transform: translateX(400px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .context-menu {
            position: absolute;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            padding: 4px 0;
            z-index: 9999;
            backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
            -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(var(--glass-saturate));
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }
        
        .context-menu-item {
            padding: 8px 16px;
            cursor: pointer;
            color: var(--text);
            transition: background 0.2s;
        }
        
        .context-menu-item:hover { background: var(--border); }
    """
