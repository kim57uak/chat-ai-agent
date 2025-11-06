"""
PandasAgent 사용 예제
"""

from core.agents.pandas_agent import PandasAgent
from langchain_openai import ChatOpenAI
import pandas as pd


# 1. 기본 사용법
def basic_usage():
    """DataFrame으로 PandasAgent 사용"""
    
    # LLM 초기화
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    
    # DataFrame 생성
    df = pd.DataFrame({
        'product': ['Laptop', 'Mouse', 'Keyboard', 'Monitor'],
        'price': [1000, 50, 100, 300],
        'quantity': [10, 50, 30, 15]
    })
    
    # PandasAgent 생성
    agent = PandasAgent(llm)
    agent.add_dataframe("products", df)
    
    # 질문하기
    result = agent.execute("Calculate total revenue (price * quantity)")
    print(result.output)


# 2. CSV 파일 사용
def csv_usage():
    """CSV 파일로 PandasAgent 사용"""
    
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    agent = PandasAgent(llm)
    
    # CSV 파일 로드
    agent.load_from_file("sales", "sales.csv")
    
    # 분석
    result = agent.execute("What is the average sales amount?")
    print(result.output)


# 3. Excel 파일 사용
def excel_usage():
    """Excel 파일로 PandasAgent 사용"""
    
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    agent = PandasAgent(llm)
    
    # Excel 파일 로드
    agent.load_from_file("data", "data.xlsx")
    
    result = agent.execute("Show me top 10 rows")
    print(result.output)


if __name__ == "__main__":
    basic_usage()
