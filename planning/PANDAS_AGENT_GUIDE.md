# 🐼 PandasAgent 사용 가이드

## 빠른 시작

### 1. 기본 사용법

```python
from core.agents.pandas_agent import PandasAgent
from langchain_openai import ChatOpenAI
import pandas as pd

# LLM 초기화
llm = ChatOpenAI(model="gpt-4", temperature=0)

# DataFrame 생성
df = pd.DataFrame({
    'product': ['Laptop', 'Mouse', 'Keyboard'],
    'price': [1000, 50, 100],
    'quantity': [10, 50, 30]
})

# PandasAgent 생성 및 DataFrame 추가
agent = PandasAgent(llm)
agent.add_dataframe("products", df)

# 질문하기
result = agent.execute("Calculate total revenue")
print(result.output)
```

### 2. CSV 파일 사용

```python
agent = PandasAgent(llm)
agent.load_from_file("sales", "sales.csv")

result = agent.execute("What is the average sales?")
print(result.output)
```

### 3. Excel 파일 사용

```python
agent = PandasAgent(llm)
agent.load_from_file("data", "data.xlsx")

result = agent.execute("Show me top 10 rows")
print(result.output)
```

## 고급 사용법

### 여러 DataFrame 동시 사용

```python
# 제품 정보
products = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['A', 'B', 'C'],
    'price': [100, 200, 150]
})

# 판매 정보
sales = pd.DataFrame({
    'product_id': [1, 2, 1],
    'quantity': [10, 5, 8]
})

agent = PandasAgent(llm)
agent.add_dataframe("products", products)
agent.add_dataframe("sales", sales)

result = agent.execute("Join products and sales, calculate total revenue")
print(result.output)
```

### Multi-Agent Orchestrator와 함께 사용

```python
from core.agents.multi_agent_orchestrator import MultiAgentOrchestrator

# PandasAgent 준비
pandas_agent = PandasAgent(llm)
pandas_agent.load_from_file("sales", "sales.csv")

# Orchestrator에 등록
orchestrator = MultiAgentOrchestrator(llm, [pandas_agent])

# 자동으로 적절한 Agent 선택
result = orchestrator.run("Analyze sales trends")
print(result)
```

## 실전 예제

### 1. 매출 분석

```python
df = pd.read_csv("sales_2024.csv")
agent = PandasAgent(llm)
agent.add_dataframe("sales", df)

# 월별 매출
result = agent.execute("Group by month and sum sales amount")

# 상위 제품
result = agent.execute("Show top 5 products by revenue")

# 성장률
result = agent.execute("Calculate month-over-month growth rate")
```

### 2. 데이터 정제

```python
result = agent.execute("Remove rows with missing values")
result = agent.execute("Convert date column to datetime format")
result = agent.execute("Fill missing prices with median")
```

### 3. 통계 분석

```python
result = agent.execute("Calculate mean, median, std of sales")
result = agent.execute("Find correlation between price and quantity")
result = agent.execute("Detect outliers using IQR method")
```

## 주의사항

⚠️ **보안**: `allow_dangerous_code=True` 설정으로 Python 코드 실행 가능
⚠️ **성능**: 대용량 데이터는 사전 필터링 권장
⚠️ **에러**: 잘못된 질문 시 에러 메시지 확인

## 지원 파일 형식

- ✅ CSV (`.csv`)
- ✅ Excel (`.xlsx`, `.xls`)
- ✅ Pandas DataFrame

## 질문 예시

```python
# 기본 통계
"What is the average price?"
"Show me the total quantity"
"Calculate sum of revenue"

# 필터링
"Show rows where price > 100"
"Filter products with quantity < 10"

# 그룹화
"Group by category and sum sales"
"Count products by brand"

# 정렬
"Sort by price descending"
"Show top 10 by revenue"

# 조인
"Merge products and sales on product_id"
"Join with customer data"
```

## 문제 해결

### Agent가 실행되지 않을 때
```python
# LLM 연결 확인
print(llm.invoke("test"))

# DataFrame 확인
print(df.head())
```

### 에러 발생 시
```python
result = agent.execute("your query")
if result.metadata.get("error"):
    print("Error:", result.output)
```

## 더 알아보기

- 예제 코드: `examples/pandas_agent_example.py`
- 테스트: `tests/integration/test_multi_agent.py`
- 소스: `core/agents/pandas_agent.py`
