"""
Session Export Utilities
세션 내용을 다양한 형태로 내보내는 유틸리티
"""

import json
import html
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from core.logging import get_logger

logger = get_logger("session_exporter")

# 테마 매니저 import
try:
    from ui.styles.material_theme_manager import material_theme_manager
except ImportError:
    material_theme_manager = None


class SessionExporter:
    """세션 내보내기 클래스"""
    
    @staticmethod
    def export_to_text(session_data: Dict, messages: List[Dict], file_path: str) -> bool:
        """텍스트 파일로 내보내기"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 헤더 정보
                f.write(f"세션: {session_data['title']}\n")
                if session_data.get('topic_category'):
                    f.write(f"카테고리: {session_data['topic_category']}\n")
                f.write(f"생성일: {session_data['created_at']}\n")
                f.write(f"메시지 수: {len(messages)}개\n")
                f.write("=" * 50 + "\n\n")
                
                # 메시지 내용
                for msg in messages:
                    timestamp = msg.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            time_str = timestamp
                    else:
                        time_str = ""
                    
                    role_name = "사용자" if msg['role'] == 'user' else "AI"
                    f.write(f"[{time_str}] {role_name}:\n")
                    f.write(f"{msg['content']}\n\n")
                    
                    if msg.get('token_count', 0) > 0:
                        f.write(f"(토큰: {msg['token_count']}개)\n\n")
                    
                    f.write("-" * 30 + "\n\n")
            
            return True
            
        except Exception as e:
            logger.error(f"텍스트 내보내기 오류: {e}")
            return False
    
    @staticmethod
    def export_to_html(session_data: Dict, messages: List[Dict], file_path: str) -> bool:
        """HTML 파일로 내보내기"""
        try:
            # 현재 테마 정보 가져오기
            theme_css = SessionExporter._get_theme_css()
            mermaid_theme = SessionExporter._get_mermaid_theme()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                # HTML 헤더
                f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Session Export</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <style>
{theme_css}
    </style>
</head>
<body>
""")
                
                # 헤더 정보
                f.write(f"""
    <div class="header">
        <h1>{html.escape(session_data['title'])}</h1>
        <p>카테고리: {html.escape(session_data.get('topic_category') or '없음')}</p>
        <p>생성일: {session_data['created_at']}</p>
        <p>메시지 수: {len(messages)}개</p>
    </div>
""")
                
                # 메시지 내용
                for msg in messages:
                    timestamp = msg.get('timestamp', '')
                    if timestamp and timestamp is not None:
                        try:
                            timestamp_str = str(timestamp)
                            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            time_str = str(timestamp)
                    else:
                        time_str = ""
                    
                    role_name = "사용자" if msg['role'] == 'user' else "AI"
                    css_class = "user-message" if msg['role'] == 'user' else "ai-message"
                    
                    # content_html이 있으면 HTML 이스케이프 없이 직접 사용
                    content_html = msg.get('content_html')
                    if content_html and content_html.strip():
                        # HTML 태그를 그대로 렌더링하기 위해 이스케이프하지 않음
                        content = content_html
                    else:
                        # 순수 텍스트를 HTML로 변환 (None 체크 포함)
                        msg_content = msg.get('content')
                        if msg_content is None:
                            msg_content = ''
                        content = SessionExporter._convert_text_to_html(msg_content)
                    
                    f.write(f"""
    <div class="message {css_class}">
        <div class="message-header">
            {role_name} <span class="timestamp">{time_str}</span>
        </div>
        <div class="message-content">
            {content}
        </div>
""")
                    
                    if msg.get('token_count', 0) > 0:
                        f.write(f'        <div class="token-info">토큰: {msg["token_count"]}개</div>\n')
                    
                    f.write("    </div>\n")
                
                # HTML 푸터
                f.write(f"""
    <script>
        // Mermaid 초기화 및 렌더링
        mermaid.initialize({{ 
            startOnLoad: false,
            theme: '{mermaid_theme}',
            themeVariables: {{
                primaryColor: '#bb86fc',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#bb86fc',
                lineColor: '#bb86fc',
                secondaryColor: '#03dac6',
                tertiaryColor: '#2d2d2d',
                background: '#121212',
                mainBkg: '#1e1e1e',
                secondBkg: '#2d2d2d',
                tertiaryBkg: '#404040'
            }}
        }});
        
        // DOM 로드 후 Mermaid 렌더링
        document.addEventListener('DOMContentLoaded', function() {{
            const mermaidElements = document.querySelectorAll('.mermaid');
            if (mermaidElements.length > 0) {{
                mermaid.run();
            }}
        }});
    </script>
</body>
</html>
""")
            
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"HTML 내보내기 오류: {e}")
            logger.error(f"스택 트레이스: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def _get_theme_css() -> str:
        """현재 테마에 맞는 CSS 반환"""
        if material_theme_manager:
            try:
                # Material 테마 CSS 생성
                colors = material_theme_manager.get_theme_colors()
                is_dark = material_theme_manager.is_dark_theme()
                
                return f"""
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: {colors.get('background', '#121212' if is_dark else '#f5f5f5')};
            color: {colors.get('text_primary', '#ffffff' if is_dark else '#333')};
        }}
        .header {{
            background: linear-gradient(135deg, {colors.get('primary', '#bb86fc')} 0%, {colors.get('primary_variant', '#3700b3')} 100%);
            color: {colors.get('on_primary', '#000000')};
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .message {{
            background: {colors.get('surface', '#1e1e1e' if is_dark else 'white')};
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,{'0.3' if is_dark else '0.1'});
            color: {colors.get('text_primary', '#ffffff' if is_dark else '#333')};
        }}
        .user-message {{
            border-left: 4px solid {colors.get('user_border', '#bb86fc')};
            background: {colors.get('user_bg', 'rgba(187, 134, 252, 0.12)')};
        }}
        .ai-message {{
            border-left: 4px solid {colors.get('ai_border', '#03dac6')};
            background: {colors.get('ai_bg', 'rgba(3, 218, 198, 0.12)')};
        }}
        .message-header {{
            font-weight: bold;
            color: {colors.get('text_secondary', '#b3b3b3' if is_dark else '#666')};
            font-size: 14px;
            margin-bottom: 8px;
        }}
        .message-content {{
            line-height: 1.6;
            color: {colors.get('text_primary', '#ffffff' if is_dark else '#333')};
        }}
        .token-info {{
            font-size: 12px;
            color: {colors.get('text_secondary', '#b3b3b3' if is_dark else '#999')};
            margin-top: 8px;
        }}
        .timestamp {{
            font-size: 12px;
            color: {colors.get('text_secondary', '#b3b3b3' if is_dark else '#999')};
        }}
        .mermaid {{
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: {colors.get('code_bg', '#2d2d2d' if is_dark else '#f8f9fa')};
            border-radius: 8px;
            border: 1px solid {colors.get('code_border', '#404040' if is_dark else '#dee2e6')};
        }}
        pre {{
            background: {colors.get('code_bg', '#2d2d2d' if is_dark else '#f8f9fa')};
            border: 1px solid {colors.get('code_border', '#404040' if is_dark else '#dee2e6')};
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            overflow-x: auto;
            color: {colors.get('text_primary', '#e8e8e8' if is_dark else '#2d3748')};
        }}
        code {{
            background: {colors.get('code_bg', '#2d2d2d' if is_dark else '#f8f9fa')};
            border: 1px solid {colors.get('code_border', '#404040' if is_dark else '#dee2e6')};
            border-radius: 4px;
            padding: 2px 6px;
            color: {colors.get('text_primary', '#e8e8e8' if is_dark else '#2d3748')};
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {colors.get('text_primary', '#ffffff' if is_dark else '#333')};
        }}
        strong {{
            color: {colors.get('text_primary', '#ffffff' if is_dark else '#333')};
        }}
        a {{
            color: {colors.get('primary', '#bb86fc')};
        }}
        a:hover {{
            color: {colors.get('primary_variant', '#3700b3')};
        }}
        blockquote {{
            border-left: 3px solid {colors.get('primary', '#bb86fc')};
            padding-left: 16px;
            margin: 12px 0;
            color: {colors.get('text_secondary', '#b3b3b3' if is_dark else '#666')};
            background: {colors.get('surface', '#1e1e1e' if is_dark else '#f8f9fa')};
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
            background: {colors.get('surface', '#1e1e1e' if is_dark else 'white')};
            border: 1px solid {colors.get('code_border', '#404040' if is_dark else '#dee2e6')};
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: {colors.get('primary', '#bb86fc')};
            color: {colors.get('on_primary', '#000000')};
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid {colors.get('divider', '#333333' if is_dark else '#dee2e6')};
            color: {colors.get('text_primary', '#ffffff' if is_dark else '#333')};
        }}
        tr:nth-child(even) {{
            background: {colors.get('code_bg', '#2d2d2d' if is_dark else '#f8f9fa')};
        }}
        """
            except Exception as e:
                logger.error(f"테마 CSS 생성 오류: {e}")
        
        # 기본 CSS (테마 매니저가 없거나 오류 발생시)
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .message {
            background: white;
            margin: 10px 0;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .user-message {
            border-left: 4px solid #007acc;
        }
        .ai-message {
            border-left: 4px solid #28a745;
        }
        .message-header {
            font-weight: bold;
            color: #666;
            font-size: 14px;
            margin-bottom: 8px;
        }
        .message-content {
            line-height: 1.6;
        }
        .token-info {
            font-size: 12px;
            color: #999;
            margin-top: 8px;
        }
        .timestamp {
            font-size: 12px;
            color: #999;
        }
        .mermaid {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        """
    
    @staticmethod
    def _get_mermaid_theme() -> str:
        """현재 테마에 맞는 Mermaid 테마 반환"""
        if material_theme_manager:
            try:
                is_dark = material_theme_manager.is_dark_theme()
                return 'dark' if is_dark else 'default'
            except Exception:
                pass
        return 'default'
    
    @staticmethod
    def _convert_text_to_html(text: str) -> str:
        """순수 텍스트를 HTML로 변환 (마크다운 및 mermaid 지원)"""
        import re
        
        # None 또는 빈 문자열 처리
        if text is None or text == '':
            return ''
        
        # 문자열로 변환 (안전장치)
        text = str(text)
        
        # 순수 텍스트인 경우에만 HTML 이스케이프 적용
        # 이미 HTML 태그가 있는 경우는 이스케이프하지 않음
        if '<' in text and '>' in text:
            # HTML 태그가 있는 경우 그대로 반환
            return text
        
        # 순수 텍스트인 경우 HTML 이스케이프
        text = html.escape(text)
        
        # 마크다운 기본 변환
        # 굵은 글씨
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        
        # 기울임
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
        
        # 코드 블록
        text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
        
        # 인라인 코드
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        
        # mermaid 코드 블록 처리
        mermaid_pattern = r'<pre><code>(?:mermaid\s*\n)?((?:graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|journey|gantt|pie|gitgraph).*?)</code></pre>'
        
        def replace_mermaid(match):
            mermaid_code = match.group(1).strip()
            return f'<div class="mermaid">{mermaid_code}</div>'
        
        text = re.sub(mermaid_pattern, replace_mermaid, text, flags=re.DOTALL)
        
        # 줄바꿈 처리 (안전장치 추가)
        if text:
            text = text.replace('\n', '<br>')
        
        return text or ''
    
    @staticmethod
    def export_to_json(session_data: Dict, messages: List[Dict], file_path: str) -> bool:
        """JSON 파일로 내보내기"""
        try:
            export_data = {
                'session': session_data,
                'messages': messages,
                'export_date': datetime.now().isoformat(),
                'total_messages': len(messages),
                'total_tokens': sum(msg.get('token_count', 0) for msg in messages)
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"JSON 내보내기 오류: {e}")
            return False
    
    @staticmethod
    def export_to_markdown(session_data: Dict, messages: List[Dict], file_path: str) -> bool:
        """Markdown 파일로 내보내기"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 헤더 정보
                f.write(f"# {session_data['title']}\n\n")
                f.write(f"**카테고리**: {session_data.get('topic_category', '없음')}  \n")
                f.write(f"**생성일**: {session_data['created_at']}  \n")
                f.write(f"**메시지 수**: {len(messages)}개  \n\n")
                f.write("---\n\n")
                
                # 메시지 내용
                for i, msg in enumerate(messages, 1):
                    timestamp = msg.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            time_str = timestamp
                    else:
                        time_str = ""
                    
                    role_name = "🧑 사용자" if msg['role'] == 'user' else "🤖 AI"
                    
                    f.write(f"## {i}. {role_name}\n")
                    if time_str:
                        f.write(f"*{time_str}*\n\n")
                    
                    f.write(f"{msg['content']}\n\n")
                    
                    if msg.get('token_count', 0) > 0:
                        f.write(f"*토큰: {msg['token_count']}개*\n\n")
                    
                    f.write("---\n\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Markdown 내보내기 오류: {e}")
            return False