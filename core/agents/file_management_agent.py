"""
File Management Agent for file operations
파일 관리를 위한 Agent
"""

from typing import Dict, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain.prompts import PromptTemplate
from pathlib import Path
from core.logging import get_logger
from .base_agent import BaseAgent, AgentResult

logger = get_logger("file_management_agent")


class FileManagementAgent(BaseAgent):
    """파일 관리 Agent"""
    
    def __init__(self, llm, root_dir: Optional[str] = None):
        """
        Initialize File Management Agent
        
        Args:
            llm: LangChain LLM instance
            root_dir: Root directory for file operations (None for dynamic)
        """
        super().__init__(llm, tools=[])
        self.root_dir = Path(root_dir) if root_dir else None
        self.toolkit = None
        self.executor = None
        
        if root_dir:
            self._initialize_toolkit(root_dir)
    
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
        
        prompt = f"""Analyze if this query requires file system operations.

Query: {query}
Context: {context}

Consider:
- File reading/writing
- Directory operations
- File search/listing
- File management tasks

Respond with ONLY "YES" or "NO":"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content.strip().upper()
            return result.startswith("YES")
        except Exception as e:
            logger.error(f"LLM can_handle check failed: {e}")
            return False
    
    def _initialize_toolkit(self, root_dir: str):
        """
        Initialize file management toolkit
        
        Args:
            root_dir: Root directory
        """
        try:
            self.root_dir = Path(root_dir)
            self.root_dir.mkdir(parents=True, exist_ok=True)
            
            self.toolkit = FileManagementToolkit(
                root_dir=str(self.root_dir),
                selected_tools=["read_file", "write_file", "list_directory"]
            )
            
            # ReAct agent 생성 - RAG 모드 최적화
            template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

CRITICAL - RAG Mode Rules:
1. After file operation completes → IMMEDIATELY provide Final Answer
2. DO NOT perform multiple operations unless absolutely necessary
3. Maximum 3 operations - then MUST provide Final Answer
4. If operation succeeds → Stop and report result

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Only perform safe file operations within the allowed directory.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

            prompt = PromptTemplate.from_template(template)
            
            agent = create_react_agent(
                llm=self.llm,
                tools=self.toolkit.get_tools(),
                prompt=prompt
            )
            
            self.executor = AgentExecutor(
                agent=agent,
                tools=self.toolkit.get_tools(),
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3,
                max_execution_time=30,
                early_stopping_method="force"
            )
            
            logger.info(f"File management toolkit initialized: {root_dir}")
            
        except Exception as e:
            logger.error(f"Failed to initialize toolkit: {e}")
    
    def _create_executor(self) -> AgentExecutor:
        """Create executor - BaseAgent compatibility"""
        if not self.executor:
            logger.warning("FileManagementAgent not initialized - no root_dir set")
            return None
        return self.executor
    
    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Execute file management operation
        
        Args:
            query: File operation request
            context: Additional context (root_dir, etc.)
            
        Returns:
            Operation result
        """
        try:
            # Initialize toolkit if root_dir provided
            if context and "root_dir" in context:
                self._initialize_toolkit(context["root_dir"])
            
            # Check if toolkit initialized
            if not self.toolkit or not self.executor:
                return AgentResult(
                    output="No root directory set. Please provide root_dir in context.",
                    metadata={"error": True}
                )
            
            # LLM 기반 안전성 판단
            safety_check = self._check_safety_with_llm(query)
            if not safety_check["is_safe"]:
                return AgentResult(
                    output=f"Safety check failed: {safety_check['reason']}",
                    metadata={"error": True}
                )
            
            logger.info(f"Executing file operation: {query[:100]}")
            result = self.executor.invoke({"input": query})
            
            # Extract output
            if isinstance(result, dict):
                output = result.get("output", str(result))
            else:
                output = str(result)
            
            return AgentResult(
                output=output,
                metadata={"root_dir": str(self.root_dir)}
            )
            
        except Exception as e:
            logger.error(f"File management execution failed: {e}", exc_info=True)
            return AgentResult(
                output=f"File operation failed: {str(e)}",
                metadata={"error": True}
            )
    
    def _check_safety_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Check if file operation is safe using LLM
        
        Args:
            query: User query
            
        Returns:
            {"is_safe": bool, "reason": str}
        """
        from langchain.schema import HumanMessage
        
        prompt = f"""Analyze if the following file operation request is SAFE.

Request: {query}
Root Directory: {self.root_dir}

Consider these risks:
1. Deleting important files
2. Overwriting existing files without confirmation
3. Accessing files outside allowed directory
4. Executing malicious code
5. Exposing sensitive information

Respond with ONLY:
- "SAFE" if the operation is safe
- "UNSAFE: [reason]" if the operation is dangerous

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
                logger.warning(f"Unclear LLM response: {result}")
                return {"is_safe": False, "reason": "Unable to verify safety"}
        
        except Exception as e:
            logger.error(f"LLM safety check failed: {e}")
            return {"is_safe": False, "reason": "Safety check error"}
    
    def set_root_dir(self, root_dir: str) -> bool:
        """
        Set root directory
        
        Args:
            root_dir: Root directory path
            
        Returns:
            Success status
        """
        try:
            self._initialize_toolkit(root_dir)
            return True
        except Exception as e:
            logger.error(f"Failed to set root directory: {e}")
            return False
