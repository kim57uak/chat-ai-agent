# RAG Agent 재설계 필요

## 현재 문제

### ConversationalRetrievalChain 사용 시 문제
```python
# RAG Agent는 Chain 사용
self.chain = ConversationalRetrievalChain(...)

# 병렬 실행 시
RAGAgent.execute() → Chain.invoke({"question": ..., "chat_history": []})
MCPAgent.execute() → AgentExecutor.invoke({"input": ...})

# LangChain 내부에서 키 충돌
# Chain이 내부적으로 intermediate_steps, question 등을 추가
# 같은 메모리 공간에서 실행되면 다른 Agent에 영향
```

## 해결 방안

### Option 1: RAG Agent를 일반 AgentExecutor로 변경 (권장)

```python
class RAGAgent(BaseAgent):
    def _create_executor(self):
        # RAG를 Tool로 래핑
        rag_tool = self._create_rag_tool()
        
        # 일반 AgentExecutor 생성 (다른 Agent와 동일)
        return AgentExecutor(
            agent=create_react_agent(self.llm, [rag_tool], prompt),
            tools=[rag_tool],
            ...
        )
    
    def _create_rag_tool(self):
        """RAG 검색을 Tool로 래핑"""
        from langchain.tools import Tool
        
        def search_documents(query: str) -> str:
            docs = self.vectorstore.search(query, k=5)
            return "\n\n".join([doc.page_content for doc in docs])
        
        return Tool(
            name="search_documents",
            description="Search relevant documents from vector database",
            func=search_documents
        )
```

### Option 2: 순차 실행으로 변경 (임시)

```python
# Orchestrator에서 병렬 실행 비활성화
if len(suitable_agents) == 1:
    return suitable_agents[0].execute(query).output
else:
    # 병렬 대신 순차 실행
    for agent in suitable_agents:
        result = agent.execute(query)
        if not result.metadata.get("error"):
            return result.output
```

## 권장 사항

**Option 1 적용:**
- RAG Agent를 Tool로 래핑하여 다른 Agent와 동일한 구조로 변경
- 병렬 실행 시 키 충돌 완전 해결
- 코드 일관성 향상

**작업 시간: 30분**
