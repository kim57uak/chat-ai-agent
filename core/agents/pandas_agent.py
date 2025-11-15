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
    """Load and analyze Excel/CSV/Parquet files. Read, filter, query, search data. Calculate statistics (mean, median, std, variance, sum, count, min, max, quantile, correlation). Group-by aggregations (groupby, pivot_table, crosstab). Sort, rank, and order data. Merge, join, concat DataFrames. Handle missing data (fillna, dropna, interpolate). Data transformation (apply, map, replace, rename). Column operations (add, drop, select, reorder). Row operations (filter, slice, sample, drop_duplicates). Data type conversion (astype, to_datetime, to_numeric). String operations (str.contains, str.split, str.replace). Date/time operations (dt.year, dt.month, resample). Export results (to_csv, to_excel, to_json). Any data analysis or statistical calculation task using Pandas."""
    
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
        # 절대 경로 패턴 (Windows: C:\, D:\, macOS/Linux: /)
        abs_path_pattern = r'(?:[A-Za-z]:[/\\]|/)[^\s]+\.(?:csv|xlsx?)'
        # 상대 경로 패턴
        rel_path_pattern = r'[\w/\-\.]+\.(?:csv|xlsx?)'
        
        if self.current_df is None:
            # 절대 경로 우선 검색
            match = re.search(abs_path_pattern, query, re.IGNORECASE)
            if not match:
                match = re.search(rel_path_pattern, query, re.IGNORECASE)
            
            if match:
                file_path = match.group(0)
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
        # Auto-load file if path detected
        abs_path_pattern = r'(?:[A-Za-z]:[/\\]|/)[^\s]+\.(?:csv|xlsx?)'
        rel_path_pattern = r'[\w/\-\.]+\.(?:csv|xlsx?)'
        
        match = re.search(abs_path_pattern, query, re.IGNORECASE)
        if not match:
            match = re.search(rel_path_pattern, query, re.IGNORECASE)
        
        if match:
            file_path = match.group(0)
            if Path(file_path).exists():
                self.load_from_file("data", file_path)
        
        # Only handle if DataFrame loaded
        if self.current_df is None:
            return False
        
        prompt = f"""Does this query require data analysis, statistics, or calculations?

Query: {query}

DataFrame info:
- Shape: {self.current_df.shape}
- Columns: {list(self.current_df.columns)}

Select YES if user wants:
- Data analysis, statistics, calculations
- Summaries, aggregations, insights
- Mathematical operations on data
- Processing or manipulating data

Select NO if user wants:
- Simple file reading/viewing
- Display content without analysis

Answer only 'YES' or 'NO'."""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            decision = response.content.strip().upper()
            result = "YES" in decision
            logger.info(f"Pandas Agent can_handle: {result}")
            return result
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
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
            early_stopping_method="force",
            handle_parsing_errors=True,
            prefix=f"""You are working with a pandas dataframe named 'df'.

CRITICAL RULES:
1. ALWAYS use the FULL dataframe 'df' - NEVER use df.head() or df.sample()
2. The dataframe has {self.current_df.shape[0]} rows and {self.current_df.shape[1]} columns
3. Columns: {list(self.current_df.columns)}
4. After getting results → IMMEDIATELY provide Final Answer
5. Maximum 3 operations then MUST answer

Dataframe info:""",
            suffix="""IMPORTANT: When analyzing data, use the ENTIRE dataframe.

Example - CORRECT:
df.groupby('이름')['점수'].mean()  # Uses ALL rows

Example - WRONG:
df.head().groupby('이름')['점수'].mean()  # Only uses first 5 rows!

Begin!"""
        )
        
        logger.info(f"Pandas agent created with dataframe shape: {self.current_df.shape}")
        return executor
    

