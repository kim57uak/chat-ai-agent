"""Universal response formatter for consistent AI model outputs"""
import re
import markdown
from typing import Dict, Any


class ResponseFormatter:
    """Formats all AI model responses to consistent format using markdown library"""
    
    def __init__(self):
        """Initialize markdown parser"""
        try:
            extensions = ['tables', 'fenced_code', 'codehilite', 'nl2br', 'sane_lists']
            
            # Add pymdown-extensions if available
            try:
                import pymdownx
                extensions.extend([
                    'pymdownx.tasklist',
                    'pymdownx.tilde',
                    'pymdownx.mark',
                    'pymdownx.superfences'
                ])
            except ImportError:
                pass
            
            self.md = markdown.Markdown(extensions=extensions)
        except Exception:
            self.md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    
    def format_response(self, content: str) -> str:
        """Format response to consistent format using markdown library"""
        if not content or not content.strip():
            return "응답을 생성할 수 없습니다."
        
        formatted = content.strip()
        formatted = self._remove_meta_text(formatted)
        
        # Use markdown library for consistent formatting
        try:
            html = self.md.convert(formatted)
            self.md.reset()
            return html
        except Exception:
            # Fallback to manual formatting
            formatted = self._standardize_markdown(formatted)
            formatted = self._standardize_lists(formatted)
            formatted = self._standardize_code_blocks(formatted)
            return formatted
    
    def _remove_meta_text(self, content: str) -> str:
        """Remove AI model meta text"""
        meta_patterns = [
            r'^(Assistant|AI|Bot):\s*',
            r'^(답변|응답):\s*',
            r'^\*\*답변\*\*:\s*',
            r'^Here\'s.*?:\s*',
            r'^Based on.*?:\s*',
        ]
        
        for pattern in meta_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content.strip()
    
    def _standardize_markdown(self, content: str) -> str:
        """Standardize markdown format"""
        # Headers: use ###
        content = re.sub(r'^#{1,2}\s+', '### ', content, flags=re.MULTILINE)
        content = re.sub(r'^#{4,}\s+', '### ', content, flags=re.MULTILINE)
        
        # Bold: use **text**
        content = re.sub(r'\*([^*]+)\*(?!\*)', r'**\1**', content)
        content = re.sub(r'__([^_]+)__', r'**\1**', content)
        
        return content
    
    def _standardize_lists(self, content: str) -> str:
        """Standardize list format"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Numbered lists: use 1. format
            if re.match(r'^\s*\d+[\.\)]\s+', line):
                line = re.sub(r'^\s*(\d+)[\.\)]\s+', r'\1. ', line)
            # Bullet lists: use - format
            elif re.match(r'^\s*[•·*+]\s+', line):
                line = re.sub(r'^\s*[•·*+]\s+', '- ', line)
            
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _standardize_code_blocks(self, content: str) -> str:
        """Standardize code block format"""
        # Inline code
        content = re.sub(r'`([^`]+)`', r'`\1`', content)
        
        # Code blocks
        content = re.sub(r'```(\w*)\n(.*?)\n```', r'```\1\n\2\n```', content, flags=re.DOTALL)
        
        return content


class SystemPromptEnhancer:
    """Enhances system prompts for consistent output format"""
    
    @staticmethod
    def get_format_instructions() -> str:
        """Universal format instructions for all AI models"""
        return """
**Output Format Guidelines:**
- Respond naturally in Korean language
- Use ### for headers
- Use **bold text** for important content
- Use - for bullet lists, 1. for numbered lists
- Use `inline code` or ```code blocks``` for code
- Use markdown table format for tables
- Remove meta text like "답변:", "AI:", "Assistant:"
- Structure information logically
- Explain technical terms simply
- Include all essential information
- Be helpful and user-friendly
"""
    
    @staticmethod
    def enhance_prompt(original_prompt: str) -> str:
        """Add format instructions to existing prompt"""
        format_instructions = SystemPromptEnhancer.get_format_instructions()
        return f"{original_prompt}\n\n{format_instructions}"