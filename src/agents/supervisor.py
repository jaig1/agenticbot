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
        
        # Initialize clarification tracking
        self.clarification_context = {}  # Stores active clarification sessions
        self.max_clarification_rounds = 3
        
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
    
    def handle_query(self, user_query: str, is_clarification_response: bool = False, clarification_key: str = None) -> Dict[str, Any]:
        """
        Main entry point for processing user queries.
        
        Orchestrates: Planner → Query Executor → Response Agent
        
        Args:
            user_query: Natural language question from user
            is_clarification_response: True if this is a response to a clarification question
            clarification_key: Key to lookup clarification context (if is_clarification_response=True)
            
        Returns:
            Dict with: success, user_query, sql, results, formatted_response, metadata
        """
        self.request_count += 1
        
        logger.info(f"[Request {self.request_count}] User query: {user_query}")
        
        # Handle clarification responses
        clarification_history = None
        clarification_round = 0
        original_clarification_key = None
        
        if is_clarification_response and clarification_key and clarification_key in self.clarification_context:
            # Retrieve clarification context using the key
            context = self.clarification_context[clarification_key]
            clarification_history = context["history"]
            clarification_round = context["round"]
            original_clarification_key = clarification_key
            
            logger.info(f"[Request {self.request_count}] Processing clarification round {clarification_round}")
            logger.info(f"[Request {self.request_count}] User response: {user_query}")
            
            # Add user's response to the history
            clarification_history[-1]["response"] = user_query
            
            # Check max rounds
            if clarification_round >= self.max_clarification_rounds:
                logger.warning(f"[Request {self.request_count}] Max clarification rounds reached")
                
                result = {
                    "success": False,
                    "user_query": user_query,
                    "sql": None,
                    "results": None,
                    "response": f"I've asked for clarification {self.max_clarification_rounds} times but still need more information. Please try rephrasing your question with more specific details about what you want to see.",
                    "formatted_response": None,
                    "metadata": {
                        "needs_clarification": False,
                        "max_rounds_reached": True,
                        "clarification_round": clarification_round
                    }
                }
                
                # Clear clarification context
                del self.clarification_context[original_clarification_key]
                
                # Store in history
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
        
        # Step 1: Query Planning - Validate and create execution plan
        logger.info(f"[Request {self.request_count}] Routing to Query Planner...")
        planning_result = self.planner.plan_query(user_query, self.static_context, clarification_history)
        
        # Step 2: Check planning result
        if planning_result["status"] == "needs_clarification":
            logger.warning(f"[Request {self.request_count}] Query needs clarification")
            
            # Increment clarification round
            new_round = clarification_round + 1
            
            # Determine clarification key
            if original_clarification_key:
                # Continue using the same key for follow-up clarifications
                clarification_key_to_store = original_clarification_key
            else:
                # First clarification - use original query as key
                clarification_key_to_store = user_query
            
            # Build history entry
            if clarification_history is None:
                # First clarification
                clarification_history = [{
                    "query": user_query,
                    "clarification": planning_result["clarification_question"]
                }]
            else:
                # Add new clarification to existing history
                clarification_history.append({
                    "query": user_query,
                    "clarification": planning_result["clarification_question"]
                })
            
            # Store context for next interaction
            self.clarification_context[clarification_key_to_store] = {
                "history": clarification_history,
                "round": new_round,
                "original_query": clarification_history[0]["query"]
            }
            
            result = {
                "success": False,
                "user_query": user_query,
                "sql": None,
                "results": None,
                "response": planning_result["clarification_question"],
                "formatted_response": None,
                "metadata": {
                    "needs_clarification": True,
                    "planning_status": "needs_clarification",
                    "clarification_round": new_round,
                    "max_rounds": self.max_clarification_rounds,
                    "clarification_key": clarification_key_to_store
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
        
        # Clear clarification context if query is answerable
        if original_clarification_key and original_clarification_key in self.clarification_context:
            del self.clarification_context[original_clarification_key]
        
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
    
    def handle_clarification_response(self, clarification_key: str, user_response: str) -> Dict[str, Any]:
        """
        Handle user's response to a clarification question.
        
        This is a convenience method that wraps handle_query() with the clarification flag.
        
        Args:
            clarification_key: The key used to store clarification context (usually the original query)
            user_response: User's response to the clarification question
            
        Returns:
            Dict with query result (may include another clarification or final result)
        """
        logger.info(f"Handling clarification response for key: {clarification_key}")
        
        # Verify clarification context exists
        if clarification_key not in self.clarification_context:
            logger.warning(f"No clarification context found for key: {clarification_key}")
            return {
                "success": False,
                "user_query": user_response,
                "sql": None,
                "results": None,
                "response": "I seem to have lost track of our conversation. Could you please rephrase your complete question?",
                "formatted_response": None,
                "metadata": {
                    "error": "clarification_context_not_found"
                }
            }
        
        # Call handle_query with clarification flag
        return self.handle_query(user_response, is_clarification_response=True, clarification_key=clarification_key)
    
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
        self.clarification_context = {}
        self.request_count = 0
        logger.info("Conversation history and clarification context cleared")
    
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
