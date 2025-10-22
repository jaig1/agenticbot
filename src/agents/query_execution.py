"""
Query Execution Agent - Phase 2.2

Responsibilities:
- Generate SQL from execution plan using LLM
- Execute SQL using Database Connector
- Return raw results and metadata

Part of 3-agent architecture:
    Supervisor → Query Planner → Query Execution Agent → Response Agent
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.connector import DatabaseConnector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QueryExecutionAgent:
    """
    Query Execution Agent - Generates and executes SQL queries.
    
    This agent combines SQL generation (using LLM) and execution (using BigQuery)
    into a single service. It takes an execution plan from the Query Planner
    and returns raw results.
    """
    
    # Path to external prompt template
    PROMPT_FILE = Path(__file__).parent.parent.parent / "prompt" / "query_execution_prompt.txt"
    
    def __init__(self):
        """
        Initialize Query Execution Agent.
        
        Responsibilities:
        - Generate SQL from execution plan using LLM
        - Execute SQL using Database Connector
        - Return raw results and metadata
        """
        load_dotenv()
        
        # Get configuration
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("VERTEX_AI_LOCATION")
        self.model_name = os.getenv("GEMINI_MODEL_NAME")
        self.dataset_id = os.getenv("BQ_DATASET_ID")
        
        if not all([self.project_id, self.location, self.model_name, self.dataset_id]):
            raise ValueError("Missing required environment variables")
        
        # Initialize Vertex AI for SQL generation
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(self.model_name)
        
        # Initialize Database Connector for execution
        self.db_connector = DatabaseConnector()
        
        # Validate and cache prompt template
        self._validate_prompt_file()
        self._prompt_template = self._load_prompt_template()
        
        logger.info(f"Query Execution Agent initialized - Model: {self.model_name}")
    
    def execute_query(self, user_query: str, schema_context: str, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SQL from plan and execute it.
        
        Args:
            user_query: Original user question
            schema_context: Complete schema context
            execution_plan: Detailed execution plan from Query Planner
            
        Returns:
            Dict with: success, user_query, sql, results, metadata
        """
        logger.info(f"Processing query: {user_query}")
        
        # Step 1: Generate SQL
        sql = self._generate_sql(user_query, schema_context, execution_plan)
        
        if not sql:
            return {
                "success": False,
                "user_query": user_query,
                "sql": None,
                "results": None,
                "metadata": {"error": "SQL generation failed"}
            }
        
        logger.info(f"SQL generated: {sql[:200]}...")
        
        # Step 2: Execute SQL
        results, db_metadata = self.db_connector.execute_query(sql)
        
        # Step 3: Return combined result
        return {
            "success": db_metadata["success"],
            "user_query": user_query,
            "sql": sql,
            "results": results,
            "metadata": db_metadata
        }
    
    def _validate_prompt_file(self):
        """
        Validate that the prompt template file exists.
        Fails fast at initialization if template is missing.
        """
        if not self.PROMPT_FILE.exists():
            raise FileNotFoundError(
                f"Prompt template not found: {self.PROMPT_FILE}\n"
                f"Please ensure the prompt file exists in the correct location."
            )
    
    def _load_prompt_template(self) -> str:
        """
        Load the SQL generation prompt template from file.
        Called once at initialization and cached in memory.
        
        Returns:
            Prompt template string with placeholders
        """
        try:
            return self.PROMPT_FILE.read_text()
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt template: {e}")
    
    def _generate_sql(self, user_query: str, schema_context: str, execution_plan: Dict[str, Any]) -> Optional[str]:
        """
        Generate SQL from execution plan using Vertex AI.
        
        Args:
            user_query: User's question
            schema_context: Schema information
            execution_plan: Plan from Query Planner
            
        Returns:
            SQL string or None if generation fails
        """
        import json
        
        # Format the cached prompt template with current values
        dataset_reference = f"{self.project_id}.{self.dataset_id}"
        execution_plan_str = json.dumps(execution_plan, indent=2)
        
        prompt = self._prompt_template.format(
            schema_context=schema_context,
            user_query=user_query,
            execution_plan=execution_plan_str,
            dataset_reference=dataset_reference
        )
        
        try:
            response = self.model.generate_content(prompt)
            sql = response.text.strip()
            
            # Clean SQL
            sql = self._clean_sql(sql)
            
            if not sql or len(sql) < 10:
                logger.error("Generated SQL is empty or too short")
                return None
            
            return sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None
    
    def _clean_sql(self, sql: str) -> str:
        """
        Clean SQL response from LLM.
        
        Args:
            sql: Raw SQL from LLM
            
        Returns:
            Cleaned SQL string
        """
        # Remove markdown code blocks
        if sql.startswith("```sql"):
            sql = sql.replace("```sql", "").replace("```", "").strip()
        elif sql.startswith("```"):
            sql = sql.replace("```", "").strip()
        
        # Remove comment lines
        lines = sql.split('\n')
        sql_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('--'):
                sql_lines.append(line)
        
        return '\n'.join(sql_lines).strip()
    
    def main(self):
        """Run internal tests for Query Execution Agent."""
        print("\n" + "="*80)
        print("Query Execution Agent - Internal Tests")
        print("="*80 + "\n")
        
        # Load schema context directly from file
        schema_path = "config/systemcontext.md"
        with open(schema_path, 'r') as f:
            schema_context = f.read()
        
        print(f"Schema loaded: {len(schema_context)} chars\n")
        
        # Test cases
        test_cases = [
            {
                "user_query": "How many insurance customers do we have?",
                "execution_plan": {
                    "intent": "Count total insurance customers",
                    "tables_needed": ["insurance_customers"],
                    "operations": {
                        "aggregation": {"function": "COUNT"}
                    }
                }
            },
            {
                "user_query": "What is the total amount of all claims?",
                "execution_plan": {
                    "intent": "Calculate total claim amounts",
                    "tables_needed": ["insurance_claims"],
                    "operations": {
                        "aggregation": {"function": "SUM", "column": "claim_amount"}
                    }
                }
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"Test {i}: {test['user_query']}")
            print("-" * 80)
            
            result = self.execute_query(
                test['user_query'],
                schema_context,
                test['execution_plan']
            )
            
            if result["success"]:
                print(f"✓ Success")
                print(f"  SQL: {result['sql'][:150]}...")
                print(f"  Rows: {result['metadata']['row_count']}")
                print(f"  Time: {result['metadata']['execution_time_seconds']}s")
                if result['results']:
                    print(f"  Sample result: {result['results'][0]}")
            else:
                print(f"✗ Failed")
                print(f"  Error: {result['metadata'].get('error', 'Unknown')}")
            
            print()
        
        print("="*80)
        print("Query Execution Tests Complete")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        agent = QueryExecutionAgent()
        agent.main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
