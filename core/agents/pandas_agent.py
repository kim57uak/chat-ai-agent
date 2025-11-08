"""
PandasAgent
LangChain create_pandas_dataframe_agent 기반
"""

from typing import List, Dict, Optional
import pandas as pd
import re
from pathlib import Path
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain.agents import AgentExecutor, AgentType
from langchain.schema import HumanMessage
from langchain.tools import BaseTool
from core.logging import get_logger
from .base_agent import BaseAgent, AgentResult

logger = get_logger("pandas_agent")


class PandasAgent(BaseAgent):
    """Pandas DataFrame analysis agent"""
    
    def __init__(self, llm, dataframes: Optional[Dict[str, pd.DataFrame]] = None):
        """
        Initialize Pandas agent
        
        Args:
            llm: LangChain LLM
            dataframes: Dict of dataframe name -> DataFrame
        """
        super().__init__(llm, tools=[])
        self.dataframes = dataframes or {}
        self.current_df = None
    
    def execute(self, query: str, context: Optional[Dict] = None) -> AgentResult:
        """
        Execute with auto file loading
        """
        # 파일 경로 감지 및 자동 로드
        if self.current_df is None and re.search(r'\.(csv|xlsx?)', query, re.IGNORECASE):
            match = re.search(r'([\w/\-\.]+\.(?:csv|xlsx?))', query, re.IGNORECASE)
            if match:
                file_path = match.group(1)
                if Path(file_path).exists():
                    logger.info(f"Auto-loading file: {file_path}")
                    self.load_from_file("data", file_path)
        
        # BaseAgent의 execute 호출
        return super().execute(query, context)
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> bool:
        """
        Check if query requires data analysis using LLM
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            True if query needs data analysis
        """
        # 파일 경로 감지 및 자동 로드
        if re.search(r'\.(csv|xlsx?)', query, re.IGNORECASE):
            match = re.search(r'([\w/\-\.]+\.(?:csv|xlsx?))', query, re.IGNORECASE)
            if match:
                file_path = match.group(1)
                if Path(file_path).exists():
                    self.load_from_file("data", file_path)
        
        # DataFrame이 로드되어 있으면 LLM으로 판단
        if self.current_df is not None:
            prompt = f"""Does this query require data analysis or manipulation?

Query: {query}

DataFrame info:
- Shape: {self.current_df.shape}
- Columns: {list(self.current_df.columns)}

Answer only 'YES' or 'NO'."""
            
            try:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                decision = response.content.strip().upper()
                return "YES" in decision
            except Exception as e:
                logger.error(f"LLM decision failed: {e}")
                return False
        
        return False
    
    def load_from_file(self, name: str, filepath: str):
        """Load dataframe from file"""
        try:
            path = Path(filepath)
            if not path.exists():
                logger.error(f"File not found: {filepath}")
                return False
            
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            elif filepath.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filepath)
            else:
                raise ValueError(f"Unsupported file type: {filepath}")
            
            self.dataframes[name] = df
            self.current_df = df
            logger.info(f"Loaded dataframe: {name} ({df.shape})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load file: {e}")
            return False
    
    def _create_executor(self) -> AgentExecutor:
        """Create Pandas agent executor"""
        if self.current_df is None:
            logger.warning("PandasAgent not initialized - no dataframe loaded")
            return None
        
        executor = create_pandas_dataframe_agent(
            llm=self.llm,
            df=self.current_df,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            allow_dangerous_code=True,
            max_iterations=3,
            max_execution_time=30,
            agent_executor_kwargs={
                "early_stopping_method": "force",
                "handle_parsing_errors": True
            },
            prefix="""You are working with a pandas dataframe. 

CRITICAL - RAG Mode Rules:
1. After you get the analysis result → IMMEDIATELY provide Final Answer
2. DO NOT run multiple queries unless absolutely necessary
3. Maximum 3 operations - then MUST provide Final Answer
4. If you have the data → Stop and answer

Dataframe info:"""
        )
        
        logger.info(f"Pandas agent created with dataframe shape: {self.current_df.shape}")
        return executor
    

