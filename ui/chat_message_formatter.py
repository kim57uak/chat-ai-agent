import re
import json
import uuid
from typing import Dict, Any
from ui.intelligent_formatter import IntelligentContentFormatter


class ChatMessageFormatter:
    """Enhanced chat message formatter with AI-driven content analysis"""
    
    def __init__(self, llm=None):
        self.intelligent_formatter = IntelligentContentFormatter(llm)
    
    def format_text(self, text: str) -> str:
        """Simplified text formatting - delegate to intelligent formatter"""
        # Use intelligent formatter for all content
        return self.intelligent_formatter.format_content(text)
    

    

    
    def create_message_html(self, sender: str, text: str) -> str:
        """Enhanced message HTML generation with intelligent formatting"""
        # 발신자별 스타일
        if sender == '사용자':
            bg_color = 'rgba(163,135,215,0.15)'
            border_color = 'rgb(163,135,215)'
            text_color = '#ffffff'
            icon = '💬'
            sender_color = 'rgb(163,135,215)'
        elif sender in ['AI', '에이전트'] or '에이전트' in sender:
            bg_color = 'rgba(135,163,215,0.15)'
            border_color = 'rgb(135,163,215)'
            text_color = '#ffffff'
            icon = '🤖'
            sender_color = 'rgb(135,163,215)'
        else:
            bg_color = 'rgba(215,163,135,0.15)'
            border_color = 'rgb(215,163,135)'
            text_color = '#ffffff'
            icon = '⚙️'
            sender_color = 'rgb(215,163,135)'
        
        formatted_text = self.format_text(text)
        
        return f"""
        <div style="
            margin: 12px 0;
            padding: 16px;
            background: linear-gradient(135deg, {bg_color}33, {bg_color}11);
            border-radius: 12px;
            border-left: 4px solid {border_color};
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        ">
            <div style="
                margin: 0 0 12px 0;
                font-weight: 700;
                color: {sender_color};
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">
                <span style="font-size: 16px;">{icon}</span>
                <span>{sender}</span>
            </div>
            <div style="
                margin: 0;
                padding-left: 24px;
                line-height: 1.6;
                color: {text_color};
                font-size: 13px;
                word-wrap: break-word;
                font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            ">
                {formatted_text}
            </div>
        </div>
        """