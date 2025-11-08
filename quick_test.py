"""
Quick PandasAgent Test
"""

import sys
sys.path.insert(0, '/Users/dolpaks/Downloads/project/chat-ai-agent')

from core.agents.pandas_agent import PandasAgent
from langchain_google_genai import ChatGoogleGenerativeAI

# Gemini 사용 (빠름)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0)

# Agent 생성
agent = PandasAgent(llm)

# 파일 로드
file_path = "/Users/dolpaks/Downloads/project/chat-ai-agent/sales_data.csv"
print(f"파일 로드 중: {file_path}")
success = agent.load_from_file("sales", file_path)

if success:
    print(f"✓ 파일 로드 성공: {agent.current_df.shape}")
    print(f"컬럼: {list(agent.current_df.columns)}")
    
    # 질문
    query = "월별, 상품별 매출현황을 표로 보여줘"
    print(f"\n질문: {query}")
    print("분석 중...\n")
    
    result = agent.execute(query)
    print("=" * 60)
    print("결과:")
    print("=" * 60)
    print(result.output)
else:
    print("✗ 파일 로드 실패")
