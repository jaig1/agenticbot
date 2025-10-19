"""
Supervisor Agent - Orchestrator for Multi-Agent Text2SQL System (Phase 2.2)

This agent orchestrates the 3-agent Text2SQL pipeline:
    User Query → Query Planner → Query Execution Agent → Response Agent

Responsibilities:
- Load and cache schema context
- Initialize and manage all agents (Planner, Executor, Response)
- Route queries through the pipeline
- Track conversation history
- Provide session statistics
"""

import os
import sys
import logging
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
from src.agents.query_planner import QueryPlanningAgent
from src.agents.query_execution import QueryExecutionAgent
from src.agents.response_agent import ResponseAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent - Orchestrates the 3-agent Text2SQL pipeline.
    
    Architecture:
    - Loads and caches schema context
    - Initializes Query Planning Agent (validates queries)
    - Initializes Query Execution Agent (generates SQL + executes)
    - Initializes Response Agent (formats results)
    - Routes queries through: Planner → Executor → Response Agent
    - Tracks conversation history
    - Provides session statistics
    """
    
    def __init__(self):
        """
        Initialize Supervisor Agent.
        
        Responsibilities:
        - Load and manage schema context
        - Initialize Query Planning Agent (with LLM)
        - Initialize Query Execution Agent (SQL generation + execution)
        - Initialize Response Agent (natural language formatting)
        - Manage conversation state
        - Orchestrate query processing pipeline
        """
        load_dotenv()
        
        logger.info("Initializing Supervisor Agent...")
        
        # Load schema context from file
        logger.info("Loading schema context...")
        self.static_context = self._load_schema_context()
        
        # Calculate context statistics
        context_chars = len(self.static_context)
        estimated_tokens = context_chars // 4  # Rough estimate: 1 token ≈ 4 chars
        logger.info(f"Static context ready: {context_chars} chars, ~{estimated_tokens} tokens")
        
        # Initialize Query Planning Agent (with LLM)
        logger.info("Initializing Query Planning Agent (with LLM)...")
        self.planner = QueryPlanningAgent()
        
        # Initialize Query Execution Agent
        logger.info("Initializing Query Execution Agent...")
        self.query_executor = QueryExecutionAgent()
        
        # Initialize Response Agent
        logger.info("Initializing Response Agent...")
        self.response_agent = ResponseAgent()
        
        # Initialize conversation state
        self.conversation_history = []
        self.request_count = 0
        
        logger.info("Supervisor Agent initialized successfully")
    
    def _load_schema_context(self) -> str:
        """
        Load schema context from config/systemcontext.md.
        
        Returns:
            Complete schema context as string
        """
        context_file = Path(__file__).parent.parent.parent / "config" / "systemcontext.md"
        
        if not context_file.exists():
            raise FileNotFoundError(
                f"Schema context file not found: {context_file}\n"
                "Please run: uv run python scripts/generate_context.py"
            )
        
        with open(context_file, 'r', encoding='utf-8') as f:
            context = f.read()
        
        return context
    
    def handle_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point for processing user queries.
        
        Orchestrates: Planner → Query Executor → Response Agent
        
        Args:
            user_query: Natural language question from user
            
        Returns:
            Dict with: success, user_query, sql, results, formatted_response, metadata
        """
        self.request_count += 1
        
        logger.info(f"[Request {self.request_count}] User query: {user_query}")
        
        # Step 1: Query Planning - Validate and create execution plan
        logger.info(f"[Request {self.request_count}] Routing to Query Planner...")
        planning_result = self.planner.plan_query(user_query, self.static_context)
        
        # Step 2: Check planning result
        if planning_result["status"] == "needs_clarification":
            logger.warning(f"[Request {self.request_count}] Query needs clarification")
            
            result = {
                "success": False,
                "user_query": user_query,
                "sql": None,
                "results": None,
                "response": planning_result["clarification_question"],
                "formatted_response": None,
                "metadata": {
                    "needs_clarification": True,
                    "planning_status": "needs_clarification"
                }
            }
            
            # Store in conversation history
            history_entry = {
                "request_number": self.request_count,
                "user_query": user_query,
                "success": False,
                "sql": None,
                "response": result["response"],
                "metadata": result["metadata"]
            }
            self.conversation_history.append(history_entry)
            
            return result
        
        # Step 3: Execute query (generate SQL + execute)
        logger.info(f"[Request {self.request_count}] Routing to Query Execution Agent...")
        execution_plan = planning_result["plan"]
        
        execution_result = self.query_executor.execute_query(
            user_query,
            self.static_context,
            execution_plan
        )
        
        # Step 4: Check execution result
        if not execution_result["success"]:
            logger.error(f"[Request {self.request_count}] Query execution failed")
            
            result = {
                "success": False,
                "user_query": user_query,
                "sql": execution_result.get("sql"),
                "results": None,
                "response": f"Query execution failed: {execution_result['metadata'].get('error', 'Unknown error')}",
                "formatted_response": None,
                "metadata": execution_result["metadata"]
            }
            
            # Store in history
            history_entry = {
                "request_number": self.request_count,
                "user_query": user_query,
                "success": False,
                "sql": result["sql"],
                "response": result["response"],
                "metadata": result["metadata"]
            }
            self.conversation_history.append(history_entry)
            
            return result
        
        # Step 5: Format response
        logger.info(f"[Request {self.request_count}] Routing to Response Agent...")
        
        formatting_result = self.response_agent.format_response(
            user_query=user_query,
            system_context=self.static_context,
            execution_plan=execution_plan,
            sql=execution_result["sql"],
            results=execution_result["results"],
            metadata=execution_result["metadata"]
        )
        
        # Step 6: Build final result
        result = {
            "success": True,
            "user_query": user_query,
            "sql": execution_result["sql"],
            "results": execution_result["results"],
            "response": formatting_result["formatted_response"],
            "display_data": formatting_result,  # Complete display package from Response Agent
            "metadata": execution_result["metadata"]
        }
        
        logger.info(f"[Request {self.request_count}] Success - "
                   f"{formatting_result['row_count']} rows in "
                   f"{formatting_result['execution_time']}")
        
        # Step 7: Store in conversation history
        history_entry = {
            "request_number": self.request_count,
            "user_query": user_query,
            "success": True,
            "sql": result["sql"],
            "response": result["response"],
            "display_data": formatting_result,
            "metadata": result["metadata"],
            "execution_plan": execution_plan
        }
        self.conversation_history.append(history_entry)
        
        return result
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Returns:
            List of all queries and responses in this session
        """
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history and reset request count."""
        self.conversation_history = []
        self.request_count = 0
        logger.info("Conversation history cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get Supervisor statistics.
        
        Returns:
            Dict with request count, success rate, etc.
        """
        if self.request_count == 0:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "success_rate": 0.0
            }
        
        successful = sum(1 for entry in self.conversation_history if entry["success"])
        failed = self.request_count - successful
        
        return {
            "total_requests": self.request_count,
            "successful_requests": successful,
            "failed_requests": failed,
            "success_rate": successful / self.request_count
        }
    
    def main(self):
        """Run internal tests to validate Supervisor Agent."""
        print("\n" + "="*80)
        print("Supervisor Agent - Internal Tests (3-Agent Architecture)")
        print("="*80 + "\n")
        
        print("Architecture: Planner → Query Executor → Response Agent\n")
        
        # Test queries
        test_queries = [
            "How many insurance customers are there?",
            "What is the total claim amount?",
            "Show me employee salary data",  # Should need clarification
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"Query {i}: {query}")
            print("-" * 80)
            
            result = self.handle_query(query)
            
            if result["success"]:
                print(f"✓ Success")
                print(f"\nSQL: {result['sql'][:150]}...")
                print(f"\nFormatted Response:")
                print(result['response'][:500])
                if len(result['response']) > 500:
                    print("...")
                print(f"\nExecution: {result['metadata']['execution_time_seconds']}s")
            else:
                print(f"✗ Failed or Needs Clarification")
                print(f"\nResponse: {result['response'][:300]}")
            
            print()
        
        # Show statistics
        print("="*80)
        print("Session Statistics")
        print("="*80)
        stats = self.get_stats()
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful: {stats['successful_requests']}")
        print(f"Failed: {stats['failed_requests']}")
        print(f"Success Rate: {stats['success_rate']:.1%}")
        print()
        
        print("="*80)
        print("Supervisor Tests Complete")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        supervisor = SupervisorAgent()
        supervisor.main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
