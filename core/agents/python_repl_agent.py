"""
Python REPL Agent
Executes Python code safely in isolated environment
"""

from typing import List, Dict, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_experimental.tools import PythonREPLTool
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("python_repl_agent")


class PythonREPLAgent(BaseAgent):
    """Execute Python code that is not purely Pandas-related. Perform complex computation or algorithmic tasks. Run Python scripts, loops, classes, or logic. Evaluate math expressions, perform simulations or calculations."""
    
    def __init__(self, llm, tools: Optional[List] = None):
        """
        Initialize Python REPL agent
        
        Args:
            llm: LangChain LLM
            tools: Additional tools (optional)
        """
        # Python REPL tool
        python_tool = PythonREPLTool()
        python_tool.name = "python_repl"
        python_tool.description = "Execute Python code. Input should be valid Python code. Use for calculations, data processing, and algorithm implementation."
        
        all_tools = [python_tool]
        if tools:
            all_tools.extend(tools)
        
        super().__init__(llm, all_tools)
        logger.info("Python REPL Agent initialized")
    
    def _create_executor(self) -> AgentExecutor:
        """Create agent with Python REPL tool"""
        if not self.tools:
            logger.warning("No Python REPL tool available")
            return None
        
        try:
            from ui.prompts import prompt_manager
            
            model_name = str(getattr(self.llm, 'model_name', '') or getattr(self.llm, 'model', ''))
            model_type = prompt_manager.get_provider_from_model(model_name)
            
            # ReAct template for code execution
            react_template = """You are a Python code execution assistant. Execute Python code to solve problems.

Available Tools:
{tools}

Tool Names:
{tool_names}

Use this format:

Question: the input question
Thought: think about what code to write
Action: python_repl
Action Input: valid Python code
Observation: execution result
... (repeat if needed)
Thought: I have the answer
Final Answer: the final answer in Korean

Question: {input}
Thought:{agent_scratchpad}"""
            
            prompt = PromptTemplate(
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
                template=react_template
            )
            
            # Create ReAct agent
            agent = create_react_agent(self.llm, self.tools, prompt)
            
            executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=5,
                max_execution_time=30,
                return_intermediate_steps=True,
                handle_parsing_errors=True
            )
            
            logger.info(f"Python REPL agent executor created with {len(self.tools)} tools")
            return executor
            
        except Exception as e:
            logger.error(f"Failed to create Python REPL agent executor: {e}")
            return None
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires Python code execution using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if Python execution needed
        """
        prompt = f"""Does this query require Python code execution for calculations, data processing, or algorithm implementation?

Query: {query}

Consider:
- Mathematical calculations
- Data transformations
- Algorithm implementations
- Code execution tasks

Answer only 'YES' or 'NO'."""
        
        try:
            from langchain.schema import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            result = "YES" in decision
            logger.info(f"Python REPL Agent can_handle: {result}")
            return result
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False
