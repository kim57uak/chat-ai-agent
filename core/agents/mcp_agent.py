"""
MCP Agent
기존 MCP 도구를 LangChain Tool로 래핑
"""

from typing import List, Dict, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("mcp_agent")


class MCPAgent(BaseAgent):
    """External tools and web services. Use for: web search, API calls, real-time information, external databases, online resources. NOT for internal documents - use RAGAgent for knowledge base search."""
    
    def __init__(self, llm, mcp_client, tools: Optional[List[BaseTool]] = None):
        """
        Initialize MCP agent
        
        Args:
            llm: LangChain LLM
            mcp_client: MCP client instance
            tools: Pre-wrapped MCP tools
        """
        super().__init__(llm, tools)
        self.mcp_client = mcp_client
        
        # MCP 도구를 LangChain Tool로 변환
        if not self.tools and mcp_client:
            self.tools = self._wrap_mcp_tools()
    
    def _wrap_mcp_tools(self) -> List[BaseTool]:
        """
        Wrap MCP tools as LangChain tools
        
        Returns:
            List of LangChain BaseTool
        """
        from tools.langchain.mcp_tool_wrapper import MCPToolWrapper
        
        wrapped_tools = []
        
        try:
            # MCP 클라이언트에서 도구 목록 가져오기
            if hasattr(self.mcp_client, 'list_tools'):
                mcp_tools = self.mcp_client.list_tools()
                
                for tool in mcp_tools:
                    wrapped = MCPToolWrapper(
                        name=tool.name,
                        description=tool.description,
                        mcp_client=self.mcp_client,
                        tool_name=tool.name
                    )
                    wrapped_tools.append(wrapped)
                
                logger.info(f"Wrapped {len(wrapped_tools)} MCP tools")
        
        except Exception as e:
            logger.error(f"Failed to wrap MCP tools: {e}")
        
        return wrapped_tools
    
    def _create_executor(self) -> AgentExecutor:
        """Create agent with MCP tools (model-specific)"""
        if not self.tools:
            logger.warning("No MCP tools available")
            return None
        
        try:
            # 모델 타입 감지
            from ui.prompts import prompt_manager
            
            model_name = str(getattr(self.llm, 'model_name', '') or getattr(self.llm, 'model', ''))
            model_type = prompt_manager.get_provider_from_model(model_name)
            is_gemini = 'gemini' in model_name.lower()
            is_perplexity = 'sonar' in model_name.lower() or 'perplexity' in model_name.lower()
            
            logger.info(f"Model: {model_name}, Type: {model_type}, Gemini: {is_gemini}, Perplexity: {is_perplexity}")
            
            if is_gemini or is_perplexity:
                # Gemini/Perplexity: ReAct Agent with centralized prompt
                from langchain.agents import create_react_agent
                from langchain.prompts import PromptTemplate
                
                # RAG 모드 전용 추가 지침
                rag_mode_instruction = """

CRITICAL - RAG Mode Rules:
1. After you get the information from tools → IMMEDIATELY output Final Answer
2. DO NOT search for additional information unless absolutely necessary
3. DO NOT repeat the same tool multiple times
4. Maximum 3 tool uses - then you MUST provide Final Answer with available information
5. If Observation contains the answer → Stop and provide Final Answer
"""
                
                if is_perplexity:
                    # Perplexity: Tool 모드와 동일한 상세 프롬프트 사용
                    from ui.prompts import ModelType
                    tool_usage_rules = prompt_manager.get_tool_prompt(ModelType.PERPLEXITY.value)
                    execution_rules = prompt_manager.get_custom_prompt(ModelType.COMMON.value, "execution_rules")
                    
                    react_template = f"""You are an expert data analyst that uses tools to gather information and provides comprehensive analysis.
{rag_mode_instruction}

**CRITICAL: THOROUGH OBSERVATION ANALYSIS REQUIRED**

{tool_usage_rules}

{execution_rules}

**EXACT FORMAT (MANDATORY):**

Thought: [Analyze what information is needed for the user's question]
Action: [exact_tool_name]
Action Input: {{{{"exact_parameter_name_from_schema": "value"}}}}

(System provides Observation with tool results)

Thought: [CRITICAL ANALYSIS STEP: Read the ENTIRE Observation carefully. Extract ALL key information including names, numbers, dates, details. Identify patterns and relationships. Organize findings logically. This analysis determines the quality of your Final Answer.]
Final Answer: [Comprehensive Korean response based EXCLUSIVELY on Observation data. Include specific details, exact numbers, names, and all relevant information from the tool results. Structure the response clearly with proper formatting. Do NOT add external knowledge - use ONLY the data provided in the Observation.]

**ANALYSIS REQUIREMENTS:**
1. **COMPLETE DATA PROCESSING**: Read every part of the Observation
2. **EXTRACT SPECIFICS**: Include exact names, numbers, dates from results
3. **LOGICAL ORGANIZATION**: Structure information clearly
4. **COMPREHENSIVE COVERAGE**: Address all aspects relevant to user's question
5. **DATA-ONLY RESPONSES**: Base answer EXCLUSIVELY on Observation data

**PARSING RULES:**
- Use EXACT keywords: "Thought:", "Action:", "Action Input:", "Final Answer:"
- Action Input MUST be valid JSON with EXACT parameter names from inputSchema
- NEVER use generic names like "param", "value" - check the tool's inputSchema
- NEVER mix Action and Final Answer
- Analyze Observation thoroughly before Final Answer

Tools: {{tools}}
Tool names: {{tool_names}}

Question: {{input}}
Thought:{{agent_scratchpad}}"""
                else:
                    # Gemini: 중앙 관리 프롬프트 사용
                    react_template = prompt_manager.get_react_template(model_type)
                    if not react_template:
                        # Fallback: 기본 ReAct 템플릿
                        react_template = f"""Answer the following questions as best you can. You have access to the following tools:
{rag_mode_instruction}

{{tools}}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{{tool_names}}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {{input}}
Thought:{{agent_scratchpad}}"""
                
                prompt = PromptTemplate.from_template(react_template)
                
                # Perplexity/Gemini는 커스텀 파서 사용
                if is_perplexity:
                    from core.perplexity_output_parser import PerplexityOutputParser
                    custom_parser = PerplexityOutputParser()
                    agent = create_react_agent(self.llm, self.tools, prompt, output_parser=custom_parser)
                elif is_gemini:
                    from core.parsers.custom_react_parser import CustomReActParser
                    custom_parser = CustomReActParser()
                    agent = create_react_agent(self.llm, self.tools, prompt, output_parser=custom_parser)
                else:
                    agent = create_react_agent(self.llm, self.tools, prompt)
            else:
                # OpenAI: Functions Agent with system prompt
                system_prompt = prompt_manager.get_agent_prompt(model_type) or "You are a helpful assistant with access to various tools."
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ])
                agent = create_openai_functions_agent(self.llm, self.tools, prompt)
            
            # AgentExecutor 생성 - 무한 반복 방지
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=3,  # 3회로 제한
                max_execution_time=30,  # 30초로 제한
                return_intermediate_steps=True,
                handle_parsing_errors=True,
                early_stopping_method="force"  # 강제 종료
            )
            
            logger.info(f"MCP agent executor created: {len(self.tools)} tools, Model: {model_type}")
            return executor
            
        except Exception as e:
            logger.error(f"Failed to create agent executor: {e}")
            return None
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires MCP tools using LLM context understanding
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if MCP tools needed
        """
        if not self.tools:
            return False
        
        # 캠싱 키 생성
        cache_key = hash(query)
        if cache_key in self._can_handle_cache:
            result = self._can_handle_cache[cache_key]
            logger.info(f"[CACHE HIT] MCPAgent.can_handle: {result}")
            return result
        
        from langchain.schema import HumanMessage
        
        # 도구 목록 생성 (최대 10개)
        tool_descriptions = "\n".join([
            f"- {t.name}: {t.description}" 
            for t in self.tools[:10]
        ])
        
        # Context 정보 추가
        context_info = ""
        if context:
            context_info = f"\n\nContext: {str(context)[:200]}"
        
        prompt = f"""Analyze if this query requires using any of the available tools.

Query: {query}{context_info}

Available Tools:
{tool_descriptions}

Consider:
1. Does the query mention files, databases, APIs, or external services?
2. Can the tools help answer this query?
3. Is this a simple conversation or does it need tool execution?

Answer ONLY 'YES' or 'NO':"""
        
        try:
            logger.info(f"[LLM REQ] MCPAgent.can_handle: {query[:30]}...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper() if hasattr(response, 'content') else str(response).strip().upper()
            logger.info(f"[LLM RES] MCPAgent.can_handle: {decision}")
            result = "YES" in decision
            
            # 캠싱 저장
            self._can_handle_cache[cache_key] = result
            logger.info(f"MCP Agent can_handle: {result}")
            return result
        except Exception as e:
            logger.error(f"MCP Agent can_handle failed: {e}")
            return False
