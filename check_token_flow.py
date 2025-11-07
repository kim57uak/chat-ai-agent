#!/usr/bin/env python3
"""토큰 저장 전체 흐름 체크"""

import sys
import sqlite3
from pathlib import Path

print("=" * 60)
print("토큰 저장 전체 흐름 체크")
print("=" * 60)

# 1. 파일 존재 확인
print("\n[1] 핵심 파일 존재 확인")
files = [
    "core/ai_client.py",
    "core/ai_agent_v2.py", 
    "core/client/chat_client.py",
    "core/chat/base_chat_processor.py",
    "core/chat/simple_chat_processor.py",
    "core/chat/tool_chat_processor.py",
    "core/chat/rag_chat_processor.py",
    "ui/components/ai_processor.py",
    "ui/chat_widget_message.py"
]

for f in files:
    exists = Path(f).exists()
    print(f"  {'✅' if exists else '❌'} {f}")

# 2. session_id 속성 확인
print("\n[2] session_id 속성 확인")

# BaseChatProcessor
with open("core/chat/base_chat_processor.py") as f:
    content = f.read()
    has_session_id = "self.session_id = None" in content
    print(f"  {'✅' if has_session_id else '❌'} BaseChatProcessor.session_id")

# AIAgentV2
with open("core/ai_agent_v2.py") as f:
    content = f.read()
    has_session_id = "self.session_id = None" in content
    print(f"  {'✅' if has_session_id else '❌'} AIAgentV2.session_id")

# 3. session_id 설정 확인
print("\n[3] session_id 설정 코드 확인")

# AIClient.set_session_id
with open("core/ai_client.py") as f:
    content = f.read()
    has_method = "def set_session_id" in content
    print(f"  {'✅' if has_method else '❌'} AIClient.set_session_id() 메서드")

# ai_processor에서 session_id 전달
with open("ui/components/ai_processor.py") as f:
    content = f.read()
    has_param = "session_id=None" in content and "client.set_session_id(session_id)" in content
    print(f"  {'✅' if has_param else '❌'} ai_processor.process_request(session_id)")

# chat_widget_message에서 session_id 전달
with open("ui/chat_widget_message.py") as f:
    content = f.read()
    has_call = "session_id=self.current_session_id" in content
    print(f"  {'✅' if has_call else '❌'} chat_widget_message에서 session_id 전달")

# 4. processor에 session_id 전달 확인
print("\n[4] processor에 session_id 전달 확인")

# simple_chat_with_history
with open("core/ai_agent_v2.py") as f:
    content = f.read()
    lines = content.split('\n')
    found = False
    for i, line in enumerate(lines):
        if "def simple_chat_with_history" in line:
            # 다음 5줄 확인
            next_lines = '\n'.join(lines[i:i+5])
            if "self.simple_processor.session_id = self.session_id" in next_lines:
                found = True
                break
    print(f"  {'✅' if found else '❌'} simple_chat_with_history에서 session_id 설정")

# _process_simple
with open("core/ai_agent_v2.py") as f:
    content = f.read()
    lines = content.split('\n')
    found = False
    for i, line in enumerate(lines):
        if "def _process_simple" in line:
            next_lines = '\n'.join(lines[i:i+15])
            if "self.simple_processor.session_id = self.session_id" in next_lines:
                found = True
                break
    print(f"  {'✅' if found else '❌'} _process_simple에서 session_id 설정")

# _process_with_tools
with open("core/ai_agent_v2.py") as f:
    content = f.read()
    has_tool = "self.tool_processor.session_id = self.session_id" in content
    has_rag = "session_id=self.session_id" in content
    print(f"  {'✅' if has_tool else '❌'} _process_with_tools에서 tool_processor session_id")
    print(f"  {'✅' if has_rag else '❌'} _process_with_tools에서 RAG processor session_id")

# 5. ChatClient가 AIAgentV2 사용하는지 확인
print("\n[5] ChatClient 확인")
with open("core/client/chat_client.py") as f:
    content = f.read()
    uses_v2 = "from core.ai_agent_v2 import AIAgentV2" in content and "AIAgentV2(api_key, model_name)" in content
    print(f"  {'✅' if uses_v2 else '❌'} ChatClient가 AIAgentV2 사용")

# 6. DB 테이블 확인
print("\n[6] DB 테이블 확인")
try:
    from core.security.secure_path_manager import secure_path_manager
    db_path = secure_path_manager.get_database_path()
    print(f"  DB 경로: {db_path}")
    
    if Path(db_path).exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('token_usage', 'session_token_summary')")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"  {'✅' if 'token_usage' in tables else '❌'} token_usage 테이블")
        print(f"  {'✅' if 'session_token_summary' in tables else '❌'} session_token_summary 테이블")
        
        conn.close()
    else:
        print(f"  ❌ DB 파일 없음")
except Exception as e:
    print(f"  ❌ DB 확인 실패: {e}")

print("\n" + "=" * 60)
print("체크 완료")
print("=" * 60)
