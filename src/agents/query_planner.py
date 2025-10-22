"""
Query Planning Agent - LLM-based Query Analysis and Planning

This agent uses Vertex AI LLM to analyze natural language queries,
determine answerability, and generate detailed execution plans.

Responsibilities:
- Analyze query intent and validate against schema
- Determine if query can be answered with available data
- Generate detailed execution plans for answerable queries
- Generate smart clarification questions for unanswerable queries
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryPlanningAgent:
    """
    Query Planning Agent - Uses LLM for intelligent query analysis.
    
    Analyzes queries to determine:
    - Can the query be answered with available schema?
    - What tables and columns are needed?
    - What operations are required (joins, aggregations, etc.)?
    - What clarifications are needed if query is ambiguous?
    """
    
    # Prompt template file location
    PROMPT_FILE = Path(__file__).parent.parent.parent / "prompt" / "query_planner_prompt.txt"
    
    def __init__(self):
        """
        Initialize Query Planning Agent with Vertex AI.
        
        Uses LLM to analyze queries and create detailed execution plans.
        """
        load_dotenv()
        
        # Get Vertex AI configuration
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
        
        # Validate and cache prompt template
        self._validate_prompt_file()
        self._prompt_template = self._load_prompt_template()
        
        logger.info(f"Query Planning Agent initialized with Vertex AI - Model: {self.model_name}")
    
    def _validate_prompt_file(self) -> None:
        """Validate that prompt file exists at startup"""
        if not self.PROMPT_FILE.exists():
            raise FileNotFoundError(
                f"Query Planner prompt not found: {self.PROMPT_FILE}\n"
                f"Expected location: prompt/query_planner_prompt.txt"
            )
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file (called once at init)"""
        try:
            return self.PROMPT_FILE.read_text(encoding='utf-8')
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt template: {e}")
    
    def plan_query(self, user_query: str, schema_context: str, clarification_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Analyze query with LLM and create execution plan.
        
        Args:
            user_query: Natural language question from user
            schema_context: Complete schema context string
            clarification_history: Optional list of previous clarifications
                Format: [{"query": "original", "clarification": "Q?", "response": "A"}]
            
        Returns:
            Dict with:
            - status: "answerable" or "needs_clarification"
            - plan: detailed execution plan (if answerable)
            - clarification_question: question for user (if needs clarification)
        """
        if clarification_history:
            logger.info(f"Planning query with {len(clarification_history)} clarification(s): {user_query}")
        else:
            logger.info(f"Planning query with LLM: {user_query}")
        
        # Build prompt for LLM
        prompt = self._build_planning_prompt(user_query, schema_context, clarification_history)
        
        # Call Vertex AI
        try:
            response = self.model.generate_content(prompt)
            plan_text = response.text.strip()
            
            # Parse JSON response
            plan_data = self._parse_llm_response(plan_text)
            
            if plan_data["status"] == "answerable":
                logger.info(f"Query is answerable. Tables: {plan_data['analysis']['tables_needed']}")
            else:
                logger.warning(f"Query needs clarification: {plan_data['clarification'][:100]}")
            
            return {
                "status": plan_data["status"],
                "plan": plan_data.get("analysis"),
                "clarification_question": plan_data.get("clarification")
            }
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return {
                "status": "needs_clarification",
                "plan": None,
                "clarification_question": f"Unable to analyze query: {str(e)}"
            }
    
    def _build_history_section(self, clarification_history: List[Dict], current_input: str) -> str:
        """
        Build conversation history section as a formatted string.
        
        Args:
            clarification_history: List of conversation entries
            current_input: Current user input
            
        Returns:
            Formatted history string or empty string if no history
        """
        if not clarification_history:
            return ""
        
        history_text = "\n\nCONVERSATION HISTORY:\n"
        
        for idx, entry in enumerate(clarification_history, 1):
            history_text += f"Round {idx}:\n"
            history_text += f"  User asked: \"{entry['query']}\"\n"
            
            if 'clarification' in entry:
                history_text += f"  System asked: \"{entry['clarification']}\"\n"
            
            if 'response' in entry:
                history_text += f"  User clarified: \"{entry['response']}\"\n"
        
        history_text += f"\nCurrent user input: \"{current_input}\"\n"
        history_text += "\nIMPORTANT: Synthesize the complete user intent by merging the conversation history above. "
        history_text += "Understand what the user wants based on ALL the context, not just the latest message.\n"
        
        return history_text
    
    def _build_planning_prompt(self, user_query: str, schema_context: str, clarification_history: Optional[List[Dict]] = None) -> str:
        """
        Build prompt for LLM to analyze query and create plan.
        
        Args:
            user_query: User's natural language question
            schema_context: Complete schema context
            clarification_history: Optional conversation history for context
            
        Returns:
            Formatted prompt string
        """
        # Build history section (empty string if no history)
        history_section = ""
        if clarification_history:
            history_section = self._build_history_section(clarification_history, user_query)
        
        # Substitute all variables into the cached template
        prompt = self._prompt_template.format(
            schema_context=schema_context,
            history_section=history_section,
            user_query=user_query
        )
        
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate LLM JSON response.
        
        Args:
            response_text: Raw text from LLM
            
        Returns:
            Parsed and validated plan dictionary
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "").strip()
        elif text.startswith("```"):
            text = text.replace("```", "").strip()
        
        # Parse JSON
        try:
            plan = json.loads(text)
            
            # Validate required fields
            if "status" not in plan:
                raise ValueError("Missing 'status' field")
            
            if plan["status"] not in ["answerable", "needs_clarification"]:
                raise ValueError(f"Invalid status: {plan['status']}")
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {text[:500]}")
            raise ValueError(f"LLM returned invalid JSON: {e}")
    
    def main(self):
        """Run internal tests for Query Planning Agent."""
        print("\n" + "="*80)
        print("Query Planning Agent - Internal Tests (with LLM)")
        print("="*80 + "\n")
        
        # Load schema context from file
        context_file = Path(__file__).parent.parent.parent / "config" / "systemcontext.md"
        print(f"Loading schema context from: {context_file}")
        
        if not context_file.exists():
            print(f"✗ ERROR: Schema context file not found: {context_file}")
            print("Please run: uv run python scripts/generate_context.py")
            return
        
        with open(context_file, 'r', encoding='utf-8') as f:
            schema_context = f.read()
        
        print(f"✓ Schema loaded: {len(schema_context)} chars\n")
        
        # Test cases - mix of answerable and unanswerable queries
        test_queries = [
            "How many insurance customers are there?",
            "Show me top 5 customers by revenue",
            "Get employee salary information",  # Should need clarification
            "What is the total claim amount?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"Test {i}: {query}")
            print("-" * 80)
            
            result = self.plan_query(query, schema_context)
            
            if result["status"] == "answerable":
                print(f"✓ Status: ANSWERABLE")
                print(f"  Intent: {result['plan']['intent']}")
                print(f"  Tables: {result['plan']['tables_needed']}")
                print(f"  Complexity: {result['plan'].get('complexity', 'unknown')}")
            else:
                print(f"⚠ Status: NEEDS CLARIFICATION")
                print(f"  Question: {result['clarification_question'][:200]}")
            
            print()
        
        print("="*80)
        print("Query Planning Tests Complete")
        print("="*80 + "\n")


if __name__ == "__main__":
    try:
        planner = QueryPlanningAgent()
        planner.main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
