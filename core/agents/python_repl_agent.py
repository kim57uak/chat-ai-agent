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
        super().__init__("python_repl", llm)
        self.tool = PythonREPLTool()
        self.agent = self._create_agent()
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """
        Check if this agent can handle the query using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if can handle
        """
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
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            return "YES" in decision
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False
    
    def _create_agent(self) -> AgentExecutor:
        """
        Create ReAct agent with Python REPL tool
        
        Returns:
            Agent executor
        """
        # ReAct prompt template
        template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Only execute safe Python code. Do not execute code that:
- Accesses file system (except reading)
- Makes network requests
- Modifies system settings
- Runs infinite loops

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        
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
    
    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Python code
        
        Args:
            query: Code execution request
            context: Additional context
            
        Returns:
            Execution result
        """
        try:
            # LLM 기반 보안 판단
            safety_check = self._check_safety_with_llm(query)
            if not safety_check["is_safe"]:
                return {
                    "success": False,
                    "error": f"Safety check failed: {safety_check['reason']}"
                }
            
            logger.info(f"Executing Python REPL query: {query[:100]}")
            result = self.agent.invoke({"input": query})
            
            # Extract output
            if isinstance(result, dict):
                output = result.get("output", str(result))
            else:
                output = str(result)
            
            return {
                "success": True,
                "result": output
            }
            
        except Exception as e:
            logger.error(f"Python REPL execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
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
            result = response.content.strip()
            
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
