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
    
    # primary RGB 추출
    primary_hex = primary.lstrip('#')
    primary_rgb = f"{int(primary_hex[0:2], 16)}, {int(primary_hex[2:4], 16)}, {int(primary_hex[4:6], 16)}"
    
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
            --primary-rgb: {primary_rgb};
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
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        .message.selected {
            border: 2px solid var(--primary);
            box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.15), 0 8px 32px rgba(0, 0, 0, 0.15);
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
            border: 1px solid var(--border);
            background: var(--surface);
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            color: var(--text);
            transition: all 0.2s;
        }
        
        .message-btn:hover { 
            background: var(--primary);
            border-color: var(--primary);
            color: var(--bg);
        }
        
        .btn-primary { 
            color: var(--primary);
            border-color: var(--primary);
        }
        
        .btn-primary:hover {
            background: var(--primary);
            color: var(--bg);
        }
        
        .btn-secondary { 
            color: var(--secondary);
            border-color: var(--secondary);
        }
        
        .btn-secondary:hover {
            background: var(--secondary);
            color: var(--bg);
        }
        
        .btn-error { 
            color: var(--error);
            border-color: var(--error);
        }
        
        .btn-error:hover {
            background: var(--error);
            color: var(--bg);
        }
        
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
        
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--surface);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(to right, var(--text-dim), var(--primary));
            border-radius: 4px;
            min-height: 20px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--primary);
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
            background: var(--surface) !important;
        }
        
        /* Mermaid 노드 스타일 */
        .mermaid .node rect,
        .mermaid .node circle,
        .mermaid .node ellipse,
        .mermaid .node polygon,
        .mermaid .node path {
            fill: var(--surface) !important;
            stroke: var(--primary) !important;
            stroke-width: 2px !important;
        }
        
        /* Mermaid 텍스트 스타일 - 가독성 최우선 */
        .mermaid text,
        .mermaid .nodeLabel,
        .mermaid .label,
        .mermaid .node .label,
        .mermaid tspan,
        .mermaid foreignObject,
        .mermaid foreignObject div,
        .mermaid foreignObject span,
        .mermaid foreignObject p {
            fill: var(--text) !important;
            color: var(--text) !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }
        
        /* Edge 레이블 배경 */
        .mermaid .edgeLabel,
        .mermaid .edgeLabel rect,
        .mermaid .edgeLabel span,
        .mermaid .edgeLabel foreignObject {
            background-color: var(--surface) !important;
            fill: var(--surface) !important;
        }
        
        /* Edge 레이블 텍스트 */
        .mermaid .edgeLabel text,
        .mermaid .edgeLabel tspan,
        .mermaid .edgeLabel div,
        .mermaid .edgeLabel span,
        .mermaid .edgeLabel p {
            fill: var(--text) !important;
            color: var(--text) !important;
            font-weight: 600 !important;
        }
        
        /* Edge 경로 */
        .mermaid .edgePath .path,
        .mermaid .flowchart-link,
        .mermaid path.path {
            stroke: var(--primary) !important;
            stroke-width: 2px !important;
        }
        
        /* 화살표 */
        .mermaid .marker,
        .mermaid .arrowheadPath,
        .mermaid marker path {
            fill: var(--primary) !important;
            stroke: var(--primary) !important;
        }
        
        /* 클러스터 */
        .mermaid .cluster rect {
            fill: var(--bg) !important;
            stroke: var(--primary) !important;
            stroke-width: 2px !important;
        }
        
        .mermaid .cluster text,
        .mermaid .cluster .label,
        .mermaid .cluster tspan {
            fill: var(--text) !important;
            color: var(--text) !important;
            font-weight: 700 !important;
        }
        
        /* 시퀀스 다이어그램 */
        .mermaid .actor,
        .mermaid .actor-box {
            fill: var(--surface) !important;
            stroke: var(--primary) !important;
        }
        
        .mermaid .actor text,
        .mermaid .actor-box text {
            fill: var(--text) !important;
        }
        
        .mermaid .messageLine0,
        .mermaid .messageLine1 {
            stroke: var(--primary) !important;
        }
        
        .mermaid .messageText {
            fill: var(--text) !important;
            stroke: none !important;
        }
        
        .mermaid .labelBox {
            fill: var(--surface) !important;
            stroke: var(--primary) !important;
        }
        
        .mermaid .labelText,
        .mermaid .loopText,
        .mermaid .loopLine {
            fill: var(--text) !important;
            stroke: var(--primary) !important;
        }
        
        .mermaid .note {
            fill: var(--surface) !important;
            stroke: var(--secondary) !important;
        }
        
        .mermaid .noteText {
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
        
        /* 코드 블록 버튼 스타일 */
        .code-btn {
            position: absolute;
            top: 8px;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            font-weight: 500;
            z-index: 10;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: all 0.2s;
        }
        
        .code-copy-btn {
            right: 8px;
            background: #444 !important;
            color: #fff !important;
        }
        
        .code-copy-btn:hover {
            background: #555 !important;
            transform: scale(1.05);
        }
        
        .code-exec-btn {
            right: 82px;
            background: #4CAF50 !important;
            color: #fff !important;
        }
        
        .code-exec-btn:hover {
            background: #45a049 !important;
            transform: scale(1.05);
        }
    """
