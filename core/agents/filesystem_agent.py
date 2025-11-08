"""
File System Agent
Manages file operations in workspace
"""

from typing import List, Dict, Optional
from pathlib import Path
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits import FileManagementToolkit
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("filesystem_agent")


class FileSystemAgent(BaseAgent):
    """Manages file system operations including read, write, delete, move, and directory management. Handles local file access and manipulation in workspace."""
    
    def __init__(self, llm, root_dir: str = "./workspace", tools: Optional[List] = None):
        """
        Initialize File System agent
        
        Args:
            llm: LangChain LLM
            root_dir: Root directory for file operations
            tools: Additional tools (optional)
        """
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        
        # File management toolkit
        try:
            toolkit = FileManagementToolkit(
                root_dir=str(self.root_dir),
                selected_tools=["read_file", "write_file", "list_directory", "file_delete", "move_file", "copy_file"]
            )
            file_tools = toolkit.get_tools()
            
            all_tools = file_tools
            if tools:
                all_tools.extend(tools)
            
            super().__init__(llm, all_tools)
            logger.info(f"File System Agent initialized with root: {self.root_dir}")
            
        except Exception as e:
            logger.error(f"Failed to initialize File System Agent: {e}")
            super().__init__(llm, tools or [])
    
    def _create_executor(self) -> AgentExecutor:
        """Create agent with file management tools"""
        if not self.tools:
            logger.warning("No file management tools available")
            return None
        
        try:
            from ui.prompts import prompt_manager
            
            model_name = str(getattr(self.llm, 'model_name', '') or getattr(self.llm, 'model', ''))
            model_type = prompt_manager.get_provider_from_model(model_name)
            
            # ReAct template for file operations
            react_template = """You are a file system management assistant. Perform file operations safely.

Root Directory: {root_dir}

Available Tools:
{tools}

IMPORTANT RULES:
1. All file paths are relative to root directory
2. Always check if file exists before reading
3. Confirm before deleting files
4. Use proper error handling

Use this format:

Question: the input question
Thought: think about what file operation to perform
Action: tool_name
Action Input: {{"parameter": "value"}}
Observation: operation result
... (repeat if needed)
Thought: I have completed the task
Final Answer: summary in Korean

Question: {input}
Thought:{agent_scratchpad}"""
            
            prompt = PromptTemplate.from_template(
                react_template,
                partial_variables={"root_dir": str(self.root_dir)}
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
            
            logger.info(f"File System agent executor created with {len(self.tools)} tools")
            return executor
            
        except Exception as e:
            logger.error(f"Failed to create File System agent executor: {e}")
            return None
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires file system operations
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if file operations needed
        """
        # Keywords indicating file operations
        file_keywords = [
            'file', 'read', 'write', 'save', 'delete', 'move', 'copy',
            'directory', 'folder', 'create', 'remove',
            '파일', '읽기', '쓰기', '저장', '삭제', '이동', '복사',
            '디렉토리', '폴더', '생성', '제거'
        ]
        
        query_lower = query.lower()
        result = any(keyword in query_lower for keyword in file_keywords)
        
        logger.info(f"File System Agent can_handle: {result}")
        return result
