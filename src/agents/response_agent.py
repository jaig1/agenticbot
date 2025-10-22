"""
Response Agent - Phase 2.2

Responsibilities:
- Format raw query results into natural language
- Explain methodology and reasoning
- Provide context and insights
- Make technical results accessible to business users

Part of 3-agent architecture:
    Supervisor → Query Planner → Query Execution Agent → Response Agent
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ResponseAgent:
    """
    Response Agent - Formats query results into user-friendly responses.
    
    This agent takes raw SQL query results and transforms them into natural
    language explanations that are easy to understand for business users.
    """
    
    # Path to external prompt template
    PROMPT_FILE = Path(__file__).parent.parent.parent / "prompt" / "response_agent_prompt.txt"
    
    def __init__(self):
        """
        Initialize Response Agent.
        
        Responsibilities:
        - Format raw query results into natural language
        - Explain methodology and reasoning
        - Provide context and insights
        - Make technical results accessible to business users
        """
        load_dotenv()
        
        # Get Vertex AI configuration
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.location = os.getenv("VERTEX_AI_LOCATION")
        self.model_name = os.getenv("GEMINI_MODEL_NAME")
        
        if not all([self.project_id, self.location, self.model_name]):
            raise ValueError("Missing required environment variables")
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(self.model_name)
        
        # Validate and cache prompt template
        self._validate_prompt_file()
        self._prompt_template = self._load_prompt_template()
        
        logger.info("Response Agent initialized")
    
    def format_response(
        self, 
        user_query: str,
        system_context: str,
        execution_plan: Dict[str, Any],
        sql: str, 
        results: List[Dict[str, Any]], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format raw results into user-friendly response with complete display content.
        
        This is the SINGLE SOURCE OF TRUTH for all user-facing content.
        The Response Agent has access to complete query state and returns
        everything needed for display - no downstream extraction required.
        
        Args:
            user_query: Original user question
            system_context: Complete schema/system context
            execution_plan: Query plan from Planner with intent, tables, operations
            sql: SQL query that was executed
            results: Raw query results (list of dicts)
            metadata: Execution metadata (row_count, execution_time, etc.)
            
        Returns:
            Dict with COMPLETE display content:
            - formatted_response: Natural language explanation
            - explanation: Detailed explanation of query logic
            - ai_reasoning: Step-by-step reasoning breakdown
            - sql_query: The SQL executed (for display)
            - execution_time: Formatted execution time string
            - row_count: Number of rows returned
            - bytes_processed: Formatted data size
            - query_interpretation: How the query was understood
            - confidence_score: Planning confidence (if available)
            - results_data: Raw query results for tabular display
        """
        logger.info(f"Formatting response for: {user_query}")
        
        # Extract plan details
        intent = execution_plan.get("intent", "Unknown query type")
        tables_needed = execution_plan.get("tables_needed", [])
        operations = execution_plan.get("operations", {})
        confidence = execution_plan.get("confidence", None)
        
        # Format execution details
        exec_time = metadata.get('execution_time_seconds', 0)
        row_count = metadata.get('row_count', len(results))
        bytes_processed = metadata.get('bytes_processed', 0)
        
        # Handle empty results
        if not results:
            return {
                "formatted_response": f"I searched for data related to '{user_query}', but no results were found.",
                "explanation": "The query executed successfully but returned no matching records. This could mean the filtering criteria were too restrictive or the requested data doesn't exist in the database.",
                "ai_reasoning": self._generate_reasoning_steps(sql, execution_plan, system_context),
                "sql_query": sql,
                "execution_time": f"{exec_time:.3f}s",
                "row_count": 0,
                "bytes_processed": self._format_bytes(bytes_processed),
                "query_interpretation": f"Query understood as: {intent}",
                "confidence_score": f"{confidence * 100:.0f}%" if confidence else "N/A",
                "results_data": []
            }
        
        # Use LLM to format response
        formatted_text = self._format_with_llm(user_query, sql, results, metadata)
        
        # Generate detailed explanation
        detailed_explanation = self._generate_detailed_explanation(
            user_query, sql, execution_plan, system_context, results, metadata
        )
        
        # Generate AI reasoning steps
        reasoning_steps = self._generate_reasoning_steps(sql, execution_plan, system_context)
        
        # Build complete display package
        return {
            "formatted_response": formatted_text,
            "explanation": detailed_explanation,
            "ai_reasoning": reasoning_steps,
            "sql_query": sql,
            "execution_time": f"{exec_time:.3f}s",
            "row_count": row_count,
            "bytes_processed": self._format_bytes(bytes_processed),
            "query_interpretation": f"Query understood as: {intent}",
            "confidence_score": f"{confidence * 100:.0f}%" if confidence else "N/A",
            "results_data": results
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
        Load the response formatting prompt template from file.
        Called once at initialization and cached in memory.
        
        Returns:
            Prompt template string with placeholders
        """
        try:
            return self.PROMPT_FILE.read_text()
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt template: {e}")
    
    def _format_with_llm(self, user_query: str, sql: str, results: List[Dict[str, Any]], 
                         metadata: Dict[str, Any]) -> str:
        """
        Use LLM to create natural language explanation of results.
        
        Args:
            user_query: User's question
            sql: Executed SQL
            results: Query results
            metadata: Execution metadata
            
        Returns:
            Formatted natural language response
        """
        # Limit results for prompt (first 10 rows)
        sample_results = results[:10]
        
        # Format the cached prompt template with current values
        prompt = self._prompt_template.format(
            user_query=user_query,
            sql=sql,
            sample_results=json.dumps(sample_results, indent=2, default=str),
            total_rows=metadata.get('row_count', len(results)),
            sample_count=len(sample_results),
            execution_time=metadata.get('execution_time_seconds', 0)
        )
        
        try:
            response = self.model.generate_content(prompt)
            formatted = response.text.strip()
            
            logger.info(f"Response formatted: {len(formatted)} chars")
            return formatted
            
        except Exception as e:
            logger.error(f"LLM formatting failed: {e}")
            # Fallback to simple formatting
            return self._simple_format(user_query, results, metadata)
    
    def _simple_format(self, user_query: str, results: List[Dict[str, Any]], 
                      metadata: Dict[str, Any]) -> str:
        """
        Simple fallback formatting without LLM.
        
        Args:
            user_query: User's question
            results: Query results
            metadata: Execution metadata
            
        Returns:
            Basic formatted response
        """
        row_count = metadata.get('row_count', len(results))
        
        # Single value result
        if len(results) == 1 and len(results[0]) == 1:
            key = list(results[0].keys())[0]
            value = results[0][key]
            return f"Based on your question '{user_query}', the result is: {value}"
        
        # Multiple rows
        response_lines = [f"Based on your question '{user_query}', here are the results:\n"]
        
        for i, row in enumerate(results[:10], 1):
            row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
            response_lines.append(f"{i}. {row_str}")
        
        if row_count > 10:
            response_lines.append(f"\n... and {row_count - 10} more results")
        
        response_lines.append(f"\n\nTotal results: {row_count}")
        
        return "\n".join(response_lines)
    
    def _extract_summary(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        """
        Create brief summary of results.
        
        Args:
            results: Query results
            metadata: Execution metadata
            
        Returns:
            Brief summary string
        """
        row_count = metadata.get('row_count', len(results))
        
        if row_count == 0:
            return "No results found"
        elif row_count == 1:
            return "1 result found"
        else:
            return f"{row_count} results found"
    
    def _explain_sql_brief(self, sql: str) -> str:
        """
        Create brief explanation of what the SQL does.
        
        Args:
            sql: SQL query
            
        Returns:
            Brief methodology explanation
        """
        sql_upper = sql.upper()
        
        operations = []
        
        if "JOIN" in sql_upper:
            operations.append("joined multiple tables")
        if "GROUP BY" in sql_upper:
            operations.append("grouped data")
        if "SUM" in sql_upper or "COUNT" in sql_upper or "AVG" in sql_upper:
            operations.append("calculated aggregations")
        if "ORDER BY" in sql_upper:
            operations.append("sorted results")
        if "LIMIT" in sql_upper:
            operations.append("limited output")
        if "WHERE" in sql_upper:
            operations.append("filtered data")
        
        if operations:
            return "Analysis " + ", ".join(operations) + "."
        else:
            return "Queried database for requested information."
    
    def _format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes into human-readable string.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., "1.5MB", "0.00MB")
        """
        if bytes_value == 0:
            return "0.00MB"
        
        mb = bytes_value / (1024 * 1024)
        if mb < 0.01:
            return "0.00MB"
        elif mb < 1:
            return f"{mb:.2f}MB"
        elif mb < 1024:
            return f"{mb:.1f}MB"
        else:
            gb = mb / 1024
            return f"{gb:.2f}GB"
    
    def _generate_detailed_explanation(
        self, 
        user_query: str,
        sql: str,
        execution_plan: Dict[str, Any],
        system_context: str,
        results: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate detailed explanation of query logic and approach.
        
        Args:
            user_query: User's question
            sql: Generated SQL
            execution_plan: Query plan details
            system_context: Schema context
            results: Query results
            metadata: Execution metadata
            
        Returns:
            Detailed explanation paragraph
        """
        import re
        
        sql_upper = sql.upper()
        intent = execution_plan.get("intent", "answer your question")
        tables = execution_plan.get("tables_needed", [])
        operations = execution_plan.get("operations", {})
        
        explanation_parts = []
        
        # Start with intent
        explanation_parts.append(f"This query {intent.lower()}.")
        
        # Explain table joins if present
        if "JOIN" in sql_upper and len(tables) > 1:
            table_list = ", ".join(tables)
            explanation_parts.append(f"It utilizes a join pattern between {table_list} tables from the system context to link related data.")
        
        # Explain aggregations
        if "GROUP BY" in sql_upper:
            agg_type = "count" if "COUNT" in sql_upper else "calculate"
            if "SUM" in sql_upper:
                agg_type = "sum"
            elif "AVG" in sql_upper:
                agg_type = "average"
            explanation_parts.append(f"Then it aggregates the results to {agg_type} the relevant metrics per group.")
        
        # Explain filtering
        if "HAVING" in sql_upper:
            explanation_parts.append("A HAVING clause filters the aggregated results based on business rules.")
        elif "WHERE" in sql_upper:
            explanation_parts.append("The WHERE clause filters data based on specific criteria.")
        
        # Explain sorting
        if "ORDER BY" in sql_upper:
            if "DESC" in sql_upper:
                explanation_parts.append("Results are sorted in descending order to show the highest values first.")
            else:
                explanation_parts.append("Results are sorted to present them in a logical order.")
        
        # Explain limit
        if "LIMIT" in sql_upper:
            limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
            if limit_match:
                limit_val = limit_match.group(1)
                explanation_parts.append(f"The output is limited to the top {limit_val} records as a best practice for exploratory queries.")
        
        return " ".join(explanation_parts)
    
    def _generate_reasoning_steps(
        self,
        sql: str,
        execution_plan: Dict[str, Any],
        system_context: str
    ) -> List[str]:
        """
        Generate step-by-step AI reasoning breakdown.
        
        Args:
            sql: Generated SQL query
            execution_plan: Query plan from Planner
            system_context: Schema context
            
        Returns:
            List of reasoning steps
        """
        import re
        
        steps = []
        sql_upper = sql.upper()
        tables = execution_plan.get("tables_needed", [])
        operations = execution_plan.get("operations", {})
        
        # Step 1: Identify join pattern
        if "JOIN" in sql_upper and len(tables) > 1:
            # Extract join condition from SQL
            join_match = re.search(r'ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)', sql, re.IGNORECASE)
            if join_match:
                steps.append(f"Applied the {tables[0]}↔{tables[1]} join pattern using the foreign key relationship specified in the system context.")
            else:
                steps.append(f"Joined {' and '.join(tables)} tables based on their relationships in the schema.")
        
        # Step 2: Aggregation functions
        agg_funcs = []
        if "COUNT(" in sql_upper:
            count_match = re.search(r'COUNT\(([^)]+)\)', sql, re.IGNORECASE)
            if count_match:
                agg_funcs.append(f"COUNT({count_match.group(1)})")
        if "SUM(" in sql_upper:
            sum_match = re.search(r'SUM\(([^)]+)\)', sql, re.IGNORECASE)
            if sum_match:
                agg_funcs.append(f"SUM({sum_match.group(1)})")
        if "AVG(" in sql_upper:
            avg_match = re.search(r'AVG\(([^)]+)\)', sql, re.IGNORECASE)
            if avg_match:
                agg_funcs.append(f"AVG({avg_match.group(1)})")
        
        if agg_funcs:
            steps.append(f"Used {', '.join(agg_funcs)} aggregate function(s) to calculate the required metrics.")
        
        # Step 3: GROUP BY clause
        if "GROUP BY" in sql_upper:
            group_match = re.search(r'GROUP BY\s+([^\n]+?)(?:HAVING|ORDER|LIMIT|$)', sql, re.IGNORECASE)
            if group_match:
                group_by = group_match.group(1).strip()
                steps.append(f"Included a GROUP BY clause on {group_by} because aggregate functions are used.")
        
        # Step 4: HAVING clause
        if "HAVING" in sql_upper:
            having_match = re.search(r'HAVING\s+([^\n]+?)(?:ORDER|LIMIT|$)', sql, re.IGNORECASE)
            if having_match:
                having_cond = having_match.group(1).strip()
                steps.append(f"Applied a HAVING {having_cond} clause to filter aggregated results based on business rules.")
        
        # Step 5: WHERE clause
        elif "WHERE" in sql_upper:
            steps.append("Applied WHERE clause to filter data based on specified criteria.")
        
        # Step 6: ORDER BY
        if "ORDER BY" in sql_upper:
            order_match = re.search(r'ORDER BY\s+([^\n]+?)(?:LIMIT|$)', sql, re.IGNORECASE)
            if order_match:
                order_by = order_match.group(1).strip()
                steps.append(f"Added ORDER BY {order_by} to present results in the most relevant order.")
        
        # Step 7: LIMIT
        if "LIMIT" in sql_upper:
            limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
            if limit_match:
                limit_val = limit_match.group(1)
                steps.append(f"Set LIMIT {limit_val} as a best practice for exploratory queries in BigQuery.")
        
        return steps if steps else ["Executed a straightforward query against the database."]
    
    def main(self):
        """Run internal tests for Response Agent."""
        print("\n" + "="*80)
        print("Response Agent - Internal Tests")
        print("="*80 + "\n")
        
        # Load schema context for tests
        schema_path = "config/systemcontext.md"
        with open(schema_path, 'r') as f:
            system_context = f.read()
        
        print(f"Schema loaded: {len(system_context)} chars\n")
        
        # Test cases
        test_cases = [
            {
                "user_query": "How many insurance customers do we have?",
                "execution_plan": {
                    "intent": "Count total insurance customers",
                    "tables_needed": ["insurance_customers"],
                    "operations": {"aggregation": {"function": "COUNT"}},
                    "confidence": 0.95
                },
                "sql": "SELECT COUNT(*) as customer_count FROM `gen-lang-client-0454606702.insurance_analytics.insurance_customers`",
                "results": [{"customer_count": 60}],
                "metadata": {"row_count": 1, "execution_time_seconds": 0.15, "bytes_processed": 1024}
            },
            {
                "user_query": "Show me top 5 customers by total premium amount",
                "execution_plan": {
                    "intent": "Retrieve top customers by premium amount",
                    "tables_needed": ["customers", "policies"],
                    "operations": {"aggregation": {"function": "SUM"}, "sorting": "DESC", "limit": 5},
                    "confidence": 0.90
                },
                "sql": "SELECT c.customer_name, SUM(p.premium_amount) as total_premium FROM customers c JOIN policies p ON c.id = p.customer_id GROUP BY c.customer_name ORDER BY total_premium DESC LIMIT 5",
                "results": [
                    {"customer_name": "John Doe", "total_premium": 50000},
                    {"customer_name": "Jane Smith", "total_premium": 45000},
                    {"customer_name": "Bob Wilson", "total_premium": 40000},
                    {"customer_name": "Alice Brown", "total_premium": 35000},
                    {"customer_name": "Charlie Davis", "total_premium": 30000}
                ],
                "metadata": {"row_count": 5, "execution_time_seconds": 0.45, "bytes_processed": 2048}
            },
            {
                "user_query": "What is the total claim amount?",
                "execution_plan": {
                    "intent": "Calculate total claim amounts",
                    "tables_needed": ["insurance_claims"],
                    "operations": {"aggregation": {"function": "SUM", "column": "claim_amount"}},
                    "confidence": 0.98
                },
                "sql": "SELECT SUM(claim_amount) as total_claims FROM `gen-lang-client-0454606702.insurance_analytics.insurance_claims`",
                "results": [{"total_claims": 1696950}],
                "metadata": {"row_count": 1, "execution_time_seconds": 0.12, "bytes_processed": 512}
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"Test {i}: {test['user_query']}")
            print("-" * 80)
            
            response = self.format_response(
                user_query=test['user_query'],
                system_context=system_context,
                execution_plan=test['execution_plan'],
                sql=test['sql'],
                results=test['results'],
                metadata=test['metadata']
            )
            
            print(f"Formatted Response:")
            print(response['formatted_response'])
            print(f"\nExplanation: {response['explanation'][:200]}...")
            print(f"Execution Time: {response['execution_time']}")
            print(f"Row Count: {response['row_count']}")
            print(f"Confidence: {response['confidence_score']}")
            print()
        
        print("="*80)
        print("Response Agent Tests Complete")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        agent = ResponseAgent()
        agent.main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
