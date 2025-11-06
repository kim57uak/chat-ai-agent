"""
Python REPL Agent for code execution
Python 코드 실행을 위한 Agent
"""

from typing import Dict, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_experimental.tools import PythonREPLTool
from langchain.prompts import PromptTemplate
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("python_repl_agent")


class PythonREPLAgent(BaseAgent):
    """Python 코드 실행 Agent"""
    
    def __init__(self, llm):
        """
        Initialize Python REPL Agent
        
        Args:
            llm: LangChain LLM instance
        """
        self.tool = PythonREPLTool()
        super().__init__(llm, tools=[self.tool])
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """
        Check if this agent can handle the query using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if can handle
        """
        # 캠싱 키 생성
        cache_key = hash(query)
        if cache_key in self._can_handle_cache:
            result = self._can_handle_cache[cache_key]
            logger.info(f"[CACHE HIT] PythonREPLAgent.can_handle: {result}")
            return result
        
        from langchain.schema import HumanMessage
        
        prompt = f"""Does this query require Python code execution or programming?

Query: {query}

Consider:
- Mathematical calculations
- Data processing
- Algorithm implementation
- Code execution requests
- Programming tasks

Answer only 'YES' or 'NO'."""
        
        try:
            logger.info(f"[LLM REQ] PythonREPLAgent.can_handle: {query[:30]}...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            logger.info(f"[LLM RES] PythonREPLAgent.can_handle completed")
            decision = response.content.strip().upper() if hasattr(response, 'content') else str(response).strip().upper()
            result = "YES" in decision
            
            # 캠싱 저장
            self._can_handle_cache[cache_key] = result
            logger.info(f"Python REPL Agent can_handle: {result}")
            return result
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False
    
    def _create_executor(self) -> AgentExecutor:
        """
        Create ReAct agent with Python REPL tool
        
        Returns:
            Agent executor
        """
        # ReAct prompt template - 자동 코드 실행
        template = """You are a Python code execution assistant. When users ask for calculations, data processing, or programming tasks, you MUST:

1. ALWAYS write and execute Python code to get accurate results
2. DO NOT just explain - actually run the code
3. Use the Python_REPL tool to execute code and get real results

You have access to the following tools:
{tools}

Tool names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: I need to write Python code to solve this
Action: Python_REPL
Action Input: [write complete Python code here]
Observation: [execution result]
Thought: I now have the result
Final Answer: [present the result in a clear way]

CRITICAL RULES:
- When asked to calculate, compute, find, execute code -> ALWAYS use Python_REPL
- Write complete, executable Python code
- Use print() to show results
- DO NOT just describe what the code would do - EXECUTE IT

Safety Guidelines:
- Only execute safe calculations and data processing
- No file system modifications
- No network requests
- No system commands

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
        # Gemini용 커스텀 파서
        model_name = str(getattr(self.llm, 'model_name', '') or getattr(self.llm, 'model', ''))
        is_gemini = 'gemini' in model_name.lower()
        
        if is_gemini:
            from core.parsers.custom_react_parser import CustomReActParser
            custom_parser = CustomReActParser()
            agent = create_react_agent(
                llm=self.llm,
                tools=[self.tool],
                prompt=prompt,
                output_parser=custom_parser
            )
        else:
            agent = create_react_agent(
                llm=self.llm,
                tools=[self.tool],
                prompt=prompt
            )
        
        return AgentExecutor(
            agent=agent,
            tools=[self.tool],
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    

    
    def _check_safety_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Check if query is safe using LLM analysis
        
        Args:
            query: User query
            
        Returns:
            {"is_safe": bool, "reason": str}
        """
        from langchain.schema import HumanMessage
        
        prompt = f"""Analyze if the following Python code request is SAFE to execute.

Request: {query}

Consider these security risks:
1. File system modifications (writing, deleting files)
2. Network requests (HTTP, sockets)
3. System commands (os.system, subprocess)
4. Dangerous functions (eval, exec, __import__)
5. Infinite loops or resource exhaustion
6. Access to sensitive data

Respond with ONLY:
- "SAFE" if the request is safe to execute
- "UNSAFE: [reason]" if the request is dangerous

Response:"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            
            if result.startswith("SAFE"):
                return {"is_safe": True, "reason": ""}
            elif result.startswith("UNSAFE"):
                reason = result.replace("UNSAFE:", "").strip()
                logger.warning(f"LLM safety check failed: {reason}")
                return {"is_safe": False, "reason": reason}
            else:
                # 불분명한 경우 안전하게 차단
                logger.warning(f"Unclear LLM response: {result}")
                return {"is_safe": False, "reason": "Unable to verify safety"}
        
        except Exception as e:
            logger.error(f"LLM safety check failed: {e}")
            # LLM 실패 시 안전하게 차단
            return {"is_safe": False, "reason": "Safety check error"}
    
    def execute_code_directly(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code directly (bypass agent)
        
        Args:
            code: Python code to execute
            
        Returns:
            Execution result
        """
        try:
            # LLM 기반 보안 판단
            safety_check = self._check_safety_with_llm(code)
            if not safety_check["is_safe"]:
                return {
                    "success": False,
                    "error": f"Safety check failed: {safety_check['reason']}"
                }
            
            result = self.tool.run(code)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Direct code execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
