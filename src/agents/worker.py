"""
Worker Agent - Stateless Text2SQL Service

This agent is a stateless service that generates and executes SQL queries.
Schema context must be provided by the caller (typically Supervisor Agent).

Responsibilities:
- Generate SQL from natural language using Vertex AI
- Execute SQL queries via DatabaseConnector
- Format results for return to caller
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

from src.database.connector import DatabaseConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerAgent:
    """
    Stateless Text2SQL service agent.
    
    This agent does NOT load schema context - it must be provided by the caller.
    
    Components:
    - SQL Generation: Uses Vertex AI Gemini for text-to-SQL conversion
    - Query Execution: Uses DatabaseConnector to execute SQL
    """
    
    def __init__(self):
        """Initialize WorkerAgent with Vertex AI and Database Connector."""
        load_dotenv()
        
        # Get configuration from environment
        self.project_id = os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID not found in environment")
        
        self.location = os.getenv("VERTEX_AI_LOCATION")
        if not self.location:
            raise ValueError("VERTEX_AI_LOCATION not found in environment")
        
        self.model_name = os.getenv("GEMINI_MODEL_NAME")
        if not self.model_name:
            raise ValueError("GEMINI_MODEL_NAME not found in environment")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(self.model_name)
        
        # Initialize Database Connector
        self.db_connector = DatabaseConnector()
        
        logger.info(f"WorkerAgent initialized (service mode) - Model: {self.model_name}")
    
    def process_query(self, user_query: str, schema_context: str, execution_plan: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process natural language query with provided schema context and optional execution plan.
        
        Args:
            user_query: Natural language question from user
            schema_context: Complete schema context string (provided by caller)
            execution_plan: Optional detailed execution plan from Query Planner
            
        Returns:
            Dict with: success, user_query, sql, results, response, metadata
        """
        logger.info(f"Processing query: {user_query}")
        
        # Step 1: Generate SQL using provided schema context and execution plan
        sql = self._generate_sql(user_query, schema_context, execution_plan)
        
        if not sql:
            return {
                "success": False,
                "user_query": user_query,
                "sql": None,
                "results": None,
                "response": "Failed to generate SQL",
                "metadata": {"error": "SQL generation failed"}
            }
        
        logger.info(f"Generated SQL: {sql[:200]}...")
        
        # Step 3: Execute SQL using Database Connector
        results, db_metadata = self.db_connector.execute_query(sql)
        
        # Step 4: Format response
        if db_metadata["success"]:
            response = self._format_response(user_query, results, db_metadata)
            
            return {
                "success": True,
                "user_query": user_query,
                "sql": sql,
                "results": results,
                "response": response,
                "metadata": db_metadata
            }
        else:
            return {
                "success": False,
                "user_query": user_query,
                "sql": sql,
                "results": None,
                "response": f"Query execution failed: {db_metadata['error']}",
                "metadata": db_metadata
            }
    
    def _generate_sql(self, user_query: str, schema_context: str, execution_plan: Dict[str, Any] = None) -> Optional[str]:
        """
        Generate SQL from natural language using Vertex AI.
        
        Args:
            user_query: User's natural language question
            schema_context: Complete schema context from systemcontext.md
            execution_plan: Optional execution plan from Query Planner
            
        Returns:
            Generated SQL string or None if generation fails
        """
        # Build prompt with schema context + user query
        prompt_parts = [schema_context]
        
        # Add execution plan if provided
        if execution_plan:
            prompt_parts.append("\n\nEXECUTION PLAN:")
            prompt_parts.append(json.dumps(execution_plan, indent=2))
            prompt_parts.append("\nUse this plan as guidance to generate the SQL query.")
        
        prompt_parts.append(f"\n\nUser Query: {user_query}")
        prompt_parts.append("\n\nGenerate SQL:")
        
        prompt = "".join(prompt_parts)
        
        try:
            # Call Vertex AI to generate SQL
            response = self.model.generate_content(prompt)
            
            # Extract SQL from response
            sql = response.text.strip()
            
            # Clean up response - remove markdown if present
            if sql.startswith("```sql"):
                sql = sql.replace("```sql", "").replace("```", "").strip()
            elif sql.startswith("```"):
                sql = sql.replace("```", "").strip()
            
            # Remove any explanatory text before/after SQL
            # Take only the SQL statement
            lines = sql.split('\n')
            sql_lines = []
            for line in lines:
                stripped = line.strip()
                # Include lines that look like SQL
                if stripped and not stripped.startswith('#') and not stripped.startswith('--'):
                    sql_lines.append(line)
            
            sql = '\n'.join(sql_lines).strip()
            
            return sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None
    
    def _format_response(
        self,
        user_query: str,
        results: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Format query results into human-readable response.
        
        Args:
            user_query: Original user query
            results: Query results (list of dicts)
            metadata: Query execution metadata
            
        Returns:
            Formatted response string
        """
        if not results:
            return "No results found."
        
        # Single value result (e.g., COUNT, SUM)
        if len(results) == 1 and len(results[0]) == 1:
            key = list(results[0].keys())[0]
            value = results[0][key]
            return f"Result: {value}"
        
        # Multiple rows - format as text
        response_lines = [f"Found {len(results)} result(s):\n"]
        
        # Show first 10 rows
        for i, row in enumerate(results[:10], 1):
            row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
            response_lines.append(f"{i}. {row_str}")
        
        if len(results) > 10:
            response_lines.append(f"\n... and {len(results) - 10} more rows")
        
        return "\n".join(response_lines)
    
    def main(self):
        """Run internal tests to validate Worker Agent in service mode."""
        print("\n" + "="*80)
        print("Worker Agent - Internal Tests (Service Mode)")
        print("="*80 + "\n")
        
        # Load schema context for testing
        context_file = Path(__file__).parent.parent.parent / "config" / "systemcontext.md"
        print(f"Loading schema context from: {context_file}")
        
        if not context_file.exists():
            print(f"✗ ERROR: Schema context file not found: {context_file}")
            print("Please run: uv run python scripts/generate_context.py")
            return
        
        with open(context_file, 'r', encoding='utf-8') as f:
            schema_context = f.read()
        
        print(f"✓ Schema context loaded ({len(schema_context)} chars)\n")
        
        # Generic test queries (not insurance-specific)
        test_queries = [
            "How many tables are in the dataset?",
            "What is the current date?",
            "Show me 3 table names from the dataset",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"Test {i}: {query}")
            print("-" * 80)
            
            result = self.process_query(query, schema_context)
            
            if result["success"]:
                print(f"✓ Success")
                print(f"  SQL: {result['sql'][:200]}...")
                print(f"  Response: {result['response'][:300]}...")
                print(f"  Rows: {result['metadata']['row_count']}")
                print(f"  Time: {result['metadata']['execution_time_seconds']}s")
            else:
                print(f"✗ Failed: {result['response']}")
            
            print()
        
        print("="*80)
        print("Worker Tests Complete (Service Mode)")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        agent = WorkerAgent()
        agent.main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
