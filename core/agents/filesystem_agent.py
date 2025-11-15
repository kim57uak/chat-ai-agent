"""
File System Agent
Manages file operations in workspace
"""

from typing import List, Dict, Optional
from pathlib import Path
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain.tools import Tool
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("filesystem_agent")


class FileSystemAgent(BaseAgent):
    """Directory inspection (list files, list directories). Check file existence, file metadata. Path management, folder traversal. Reading or scanning file/folder structure."""
    
    def __init__(self, llm, root_dir: str = "./workspace", tools: Optional[List] = None):
        """
        Initialize File System agent
        
        Args:
            llm: LangChain LLM
            root_dir: Root directory for file operations (supports absolute paths)
            tools: Additional tools (optional)
        """
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        
        # Custom absolute path read tool
        def read_absolute_file(file_path: str) -> str:
            """Read file from absolute path"""
            try:
                path = Path(file_path)
                if not path.exists():
                    return f"Error: File not found at {file_path}"
                if not path.is_file():
                    return f"Error: {file_path} is not a file"
                return path.read_text(encoding='utf-8')
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        absolute_read_tool = Tool(
            name="read_absolute_file",
            description="Read file content from absolute path (e.g., /Users/..., C:\\...). Input should be absolute file path as string.",
            func=read_absolute_file
        )
        
        # File management toolkit
        try:
            toolkit = FileManagementToolkit(
                root_dir=str(self.root_dir),
                selected_tools=["read_file", "write_file", "list_directory", "file_delete", "move_file", "copy_file"]
            )
            file_tools = toolkit.get_tools()
            
            all_tools = [absolute_read_tool] + file_tools
            if tools:
                all_tools.extend(tools)
            
            super().__init__(llm, all_tools)
            logger.info(f"File System Agent initialized with absolute path support")
            
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
            
            # Tool names and descriptions
            tool_names = ", ".join([tool.name for tool in self.tools])
            tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            
            # ReAct template for file operations
            react_template = """You are a file system management assistant. Perform file operations safely.

Available Tools: {tool_names}
{tools}

IMPORTANT RULES:
1. For ABSOLUTE paths (/Users/..., C:\\..., D:\\...) → Use 'read_absolute_file' tool
2. For RELATIVE paths → Use 'read_file' tool
3. Always use proper error handling
4. Confirm before deleting files

Use this format:

Question: the input question
Thought: think about what file operation to perform
Action: tool_name
Action Input: "/absolute/path/to/file" or "relative/path"
Observation: operation result
... (repeat if needed)
Thought: I have completed the task
Final Answer: summary in Korean

Question: {input}
Thought:{agent_scratchpad}"""
            
            prompt = PromptTemplate.from_template(
                react_template,
                partial_variables={
                    "tool_names": tool_names
                }
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
        Check if query requires file system operations using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if file operations needed
        """
        prompt = f"""Does this query require simple file operations (reading, copying, moving, deleting files)?

Query: {query}

Select YES if:
- User wants to read/view/show file content without analysis
- User wants to copy/move/delete files
- User wants to list directories
- Simple file operations only

Select NO if:
- User wants data analysis, statistics, calculations
- User wants to process or manipulate data
- Complex data operations needed

Answer only 'YES' or 'NO'."""
        
        try:
            from langchain.schema import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            result = "YES" in decision
            logger.info(f"File System Agent can_handle: {result}")
            return result
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return False
