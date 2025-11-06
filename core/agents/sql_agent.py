"""
SQL Agent for database queries
데이터베이스 쿼리를 위한 Agent
"""

from typing import Dict, Any, Optional
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.agents.agent_types import AgentType
from core.logging import get_logger
from .base_agent import BaseAgent

logger = get_logger("sql_agent")


class SQLAgent(BaseAgent):
    """SQL 데이터베이스 쿼리 Agent"""
    
    def __init__(self, llm):
        """
        Initialize SQL Agent
        
        Args:
            llm: LangChain LLM instance
        
        Note:
            DB connection is established dynamically via context['db_uri']
            Supports: MySQL, PostgreSQL, SQLite, Oracle, SQL Server
        """
        super().__init__("sql", llm)
        self.db = None
        self.agent = None
        self.current_db_uri = None
    
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
        
        prompt = f"""Analyze if this query requires SQL database operations.

Query: {query}
Context: {context}

Consider:
- Database queries (SELECT, INSERT, UPDATE, DELETE)
- Table operations
- Data retrieval from databases
- SQL-related tasks

Respond with ONLY "YES" or "NO":"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content.strip().upper()
            return result.startswith("YES")
        except Exception as e:
            logger.error(f"LLM can_handle check failed: {e}")
            return False
    
    def connect(self, db_uri: str) -> bool:
        """
        Connect to database with driver validation
        
        Args:
            db_uri: Database URI
                - MySQL: "mysql+pymysql://user:pass@host:port/db"
                - PostgreSQL: "postgresql://user:pass@host:port/db"
                - SQLite: "sqlite:///path/to/db.db"
                - Oracle: "oracle+cx_oracle://user:pass@host:port/db"
                - SQL Server: "mssql+pyodbc://user:pass@host:port/db"
            
        Returns:
            Success status
        """
        try:
            # 드라이버 체크
            driver_check = self._check_driver(db_uri)
            if not driver_check["available"]:
                logger.error(f"Driver not available: {driver_check['message']}")
                return False
            
            self.db = SQLDatabase.from_uri(db_uri)
            
            # Create SQL agent
            self.agent = create_sql_agent(
                llm=self.llm,
                db=self.db,
                agent_type=AgentType.OPENAI_FUNCTIONS,
                verbose=True
            )
            
            self.current_db_uri = db_uri
            logger.info(f"Connected to database: {db_uri.split('@')[0]}@***")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def _check_driver(self, db_uri: str) -> Dict[str, Any]:
        """
        Check if required database driver is installed (dynamic detection)
        
        Args:
            db_uri: Database URI
            
        Returns:
            {"available": bool, "message": str, "install_cmd": str}
        """
        try:
            # URI에서 DB 타입 추출
            db_type = db_uri.split(":")[0].split("+")[0]
            driver = db_uri.split("+")[1].split(":")[0] if "+" in db_uri else None
            
            # SQLite는 내장
            if db_type == "sqlite":
                return {
                    "available": True,
                    "message": "SQLite driver available (built-in)",
                    "install_cmd": ""
                }
            
            # 드라이버 모듈 추론
            if driver:
                module_name = driver
            else:
                # 기본 드라이버 매핑
                default_drivers = {
                    "mysql": "pymysql",
                    "postgresql": "psycopg2",
                    "oracle": "cx_Oracle",
                    "mssql": "pyodbc"
                }
                module_name = default_drivers.get(db_type)
            
            if not module_name:
                return {
                    "available": False,
                    "message": f"Unknown database type: {db_type}",
                    "install_cmd": ""
                }
            
            # 드라이버 설치 확인
            try:
                __import__(module_name)
                return {
                    "available": True,
                    "message": f"{module_name} driver available",
                    "install_cmd": ""
                }
            except ImportError:
                return {
                    "available": False,
                    "message": f"{module_name} driver not installed",
                    "install_cmd": f"pip install {module_name}"
                }
        
        except Exception as e:
            logger.error(f"Driver check failed: {e}")
            return {
                "available": False,
                "message": f"Driver check error: {str(e)}",
                "install_cmd": ""
            }
    
    def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute SQL query
        
        Args:
            query: SQL query or natural language query
            context: Additional context (db_uri, etc.)
            
        Returns:
            Query result
        """
        try:
            # Connect if db_uri provided
            if context and "db_uri" in context:
                if not self.connect(context["db_uri"]):
                    return {
                        "success": False,
                        "error": "Failed to connect to database"
                    }
            
            # Check if connected
            if self.db is None or self.agent is None:
                return {
                    "success": False,
                    "error": "No database connected. Please provide db_uri."
                }
            
            # Execute query
            logger.info(f"Executing SQL query: {query}")
            result = self.agent.invoke(query)
            
            # Extract output
            if isinstance(result, dict):
                output = result.get("output", str(result))
            else:
                output = str(result)
            
            return {
                "success": True,
                "result": output,
                "tables": self.get_table_names()
            }
            
        except Exception as e:
            logger.error(f"SQL agent execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_table_names(self) -> list:
        """
        Get list of table names
        
        Returns:
            List of table names
        """
        if self.db is None:
            return []
        
        try:
            return self.db.get_usable_table_names()
        except Exception as e:
            logger.error(f"Failed to get table names: {e}")
            return []
    
    def get_table_info(self, table_name: str) -> Optional[str]:
        """
        Get table schema information
        
        Args:
            table_name: Table name
            
        Returns:
            Table info or None
        """
        if self.db is None:
            return None
        
        try:
            return self.db.get_table_info([table_name])
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from database"""
        self.db = None
        self.agent = None
        logger.info("Disconnected from database")
