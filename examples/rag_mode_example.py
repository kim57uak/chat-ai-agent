"""
RAG Mode Example
RAG 모드 사용 예제
"""

from core.ai_agent import AIAgent
from core.rag.vector_store.lancedb_store import LanceDBVectorStore
from core.rag.embeddings.korean_embeddings import KoreanEmbeddings
from mcp.servers.mcp import MCPClient

# 1. AI Agent 초기화
agent = AIAgent(api_key="your-api-key", model_name="gpt-4")

# 2. 벡터 스토어 초기화 (RAG용)
embeddings = KoreanEmbeddings()
vectorstore = LanceDBVectorStore(
    db_path="./data/lancedb",
    embeddings=embeddings
)

# 3. MCP 클라이언트 초기화 (도구용)
mcp_client = MCPClient()

# 4. RAG 모드 설정
agent.set_chat_mode("rag")
agent.set_vectorstore(vectorstore)
agent.set_mcp_client(mcp_client)

# 5. RAG 채팅 실행
response, tools = agent.process_message("문서에서 주요 내용을 요약해주세요")
print(response)
