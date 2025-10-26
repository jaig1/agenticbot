"""
Supervisor Agent - LLM-Driven Orchestrator for Multi-Agent Text2SQL System

This agent uses LLM-based orchestration to intelligently route queries through:
    User Query → Query Planner → Query Execution Agent → Response Agent

Key Innovation: LLM-Driven Orchestration
- Uses an LLM to decide routing at each step (no hardcoded if/else)
- Intelligently determines when to clarify vs. execute
- Adapts workflow based on context and agent outputs
- Follows Google ADK LLM-driven orchestration pattern

Responsibilities:
- Load and cache schema context
- Initialize orchestration LLM for routing decisions
- Initialize and manage all agents (Planner, Executor, Response)
- Use LLM to decide each orchestration step dynamically
- Track conversation history and state
- Provide session statistics
"""

import os

# Suppress gRPC and ALTS warnings before any Google Cloud imports
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum

# Add query logging capability
try:
    from src.utils.query_logger import get_query_logger
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

from src.agents.query_planner import QueryPlanningAgent
from src.agents.query_execution import QueryExecutionAgent
from src.agents.response_agent import ResponseAgent
from src.agents.gcp_pricing_agent import GCPPricingAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrchestrationAction(Enum):
    """
    Possible orchestration actions decided by the LLM.
    
    The orchestration LLM analyzes current context and chooses one of these actions
    to determine the next step in the workflow.
    """
    CALL_PRICING_AGENT = "CALL_PRICING_AGENT"
    CALL_PLANNER = "CALL_PLANNER"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    CALL_EXECUTOR = "CALL_EXECUTOR"
    CALL_RESPONSE_AGENT = "CALL_RESPONSE_AGENT"
    RETRY_PLANNING = "RETRY_PLANNING"
    GIVE_UP = "GIVE_UP"
    COMPLETE = "COMPLETE"


class SupervisorAgent:
    """
    LLM-Driven Supervisor Agent - Intelligent orchestrator using LLM for routing decisions.
    
    Architecture (Google ADK LLM-Driven Pattern):
    - Uses an orchestration LLM to decide each workflow step
    - No hardcoded if/else routing logic
    - Dynamically adapts to query context and agent outputs
    - Existing agents remain unchanged (Planner, Executor, Response)
    
    Orchestration Flow:
    1. Analyze current context (query, state, agent results)
    2. Ask orchestration LLM: "What should I do next?"
    3. Execute LLM's chosen action (call agent, clarify, complete)
    4. Update context and repeat until complete
    
    Benefits:
    - Contextual intelligence in routing decisions
    - Flexible clarification (not rigid 3-round limit)
    - Smart error recovery and retry logic
    - Adaptable to new scenarios without code changes
    """
    
    def __init__(self, orchestration_model: str = "gemini-2.5-flash-lite"):
        """
        Initialize LLM-Driven Supervisor Agent.
        
        Args:
            orchestration_model: Model to use for orchestration decisions (default: gemini-2.5-flash-lite)
        
        Responsibilities:
        - Initialize orchestration LLM for routing decisions
        - Load and manage schema context
        - Initialize Query Planning Agent (with LLM)
        - Initialize Query Execution Agent (SQL generation + execution)
        - Initialize Response Agent (natural language formatting)
        - Manage conversation state and orchestration context
        """
        load_dotenv()
        
        # Initialize Vertex AI
        project_id = os.getenv("GCP_PROJECT_ID")
        location = os.getenv("GCP_LOCATION", "us-central1")
        vertexai.init(project=project_id, location=location)
        
        # Load schema context from file
        self.static_context = self._load_schema_context()
        
        # Initialize orchestration LLM (separate from agent LLMs)
        self.orchestration_llm = GenerativeModel(orchestration_model)
        self.orchestration_model_name = orchestration_model
        
        # Initialize agents
        self.planner = QueryPlanningAgent()
        self.query_executor = QueryExecutionAgent()
        self.response_agent = ResponseAgent()
        self.pricing_agent = GCPPricingAgent()
        
        # Load orchestration prompt template
        self.orchestration_prompt_template = self._load_orchestration_prompt()
        
        # Initialize conversation state
        self.conversation_history = []
        self.clarification_context = {}  # Store clarification state keyed by original query
        self.request_count = 0
        self.max_clarification_rounds = 3
        
        # Orchestration metrics
        self.orchestration_decisions = []  # Track all orchestration decisions for analysis
        
        print("🚀 AgenticBot System Ready")
        print(f"🔗 Connected to BigQuery ({project_id}.uqm)")
    
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
    
    def _load_orchestration_prompt(self) -> str:
        """
        Load orchestration prompt template from prompt/orchestration_prompt.txt.
        
        Returns:
            Orchestration prompt template as string with placeholders
        """
        prompt_file = Path(__file__).parent.parent.parent / "prompt" / "orchestration_prompt.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Orchestration prompt file not found: {prompt_file}\n"
                "Please ensure prompt/orchestration_prompt.txt exists"
            )
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            template = f.read()
        
        return template
    
    def _get_orchestration_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to decide next orchestration action.
        
        This is the core of the LLM-driven orchestration pattern. Instead of hardcoded
        if/else logic, we ask an LLM to analyze the current context and decide what
        action to take next.
        
        Args:
            context: Current orchestration context containing:
                - user_query: The user's question
                - current_state: Current workflow state (NEW_QUERY, PLANNING_COMPLETE, etc.)
                - clarification_count: Number of clarification rounds so far
                - clarification_history: Previous clarification exchanges
                - results: Outputs from agents called so far
                - completed: Whether workflow is complete
        
        Returns:
            Dict containing:
                - action: OrchestrationAction to take next
                - reason: Why this action was chosen
                - parameters: Any parameters needed for the action
                - next_state: Updated workflow state
        """
        
        # Prepare template variables
        state_warning = ""
        if context['current_state'] == 'RESPONSE_COMPLETE':
            state_warning = "⚠️  STATE IS RESPONSE_COMPLETE - YOU MUST CHOOSE 'COMPLETE' ACTION!"
        
        # Format the orchestration prompt with current context
        orchestration_prompt = self.orchestration_prompt_template.format(
            user_query=context['user_query'],
            current_state=context['current_state'],
            state_warning=state_warning,
            clarification_count=context['clarification_count'],
            max_clarification_rounds=self.max_clarification_rounds,
            is_clarification_response=context.get('is_clarification_response', False),
            results_json=json.dumps(context.get('results', {}), indent=2, default=str),
            conversation_history=json.dumps(self.conversation_history[-3:] if self.conversation_history else [], indent=2, default=str),
            valid_actions=[action.value for action in OrchestrationAction]
        )
        
        try:
            # Call orchestration LLM
            response = self.orchestration_llm.generate_content(orchestration_prompt)
            
            # Parse JSON response
            decision_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in decision_text:
                decision_text = decision_text.split("```json")[1].split("```")[0].strip()
            elif "```" in decision_text:
                decision_text = decision_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            decision = json.loads(decision_text)
            
            # Validate decision structure
            if "action" not in decision:
                raise ValueError("Decision missing 'action' field")
            
            # Track decision for metrics
            self.orchestration_decisions.append({
                "iteration": len(self.orchestration_decisions) + 1,
                "state": context["current_state"],
                "action": decision["action"],
                "reason": decision.get("reason", ""),
                "clarification_count": context["clarification_count"]
            })
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse orchestration decision as JSON: {e}")
            logger.error(f"LLM response: {decision_text}")
            # Fallback to safe default
            return {
                "action": OrchestrationAction.GIVE_UP.value,
                "reason": f"Orchestration error: Invalid JSON response from LLM",
                "parameters": {},
                "next_state": "COMPLETED"
            }
        except Exception as e:
            logger.error(f"Error in orchestration decision: {e}")
            # Fallback to safe default
            return {
                "action": OrchestrationAction.GIVE_UP.value,
                "reason": f"Orchestration error: {str(e)}",
                "parameters": {},
                "next_state": "COMPLETED"
            }
    
    def handle_query(self, user_query: str, is_clarification_response: bool = False, clarification_key: str = None) -> Dict[str, Any]:
        """
        LLM-Driven Orchestration Loop for processing user queries.
        
        Instead of hardcoded if/else routing, this method uses an orchestration LLM
        to decide what action to take at each step. The LLM analyzes the current
        context (query state, agent results, clarification history) and intelligently
        chooses the next action from: CALL_PLANNER, ASK_CLARIFICATION, CALL_EXECUTOR,
        CALL_RESPONSE_AGENT, RETRY_PLANNING, GIVE_UP, or COMPLETE.
        
        This follows the Google ADK LLM-driven delegation pattern where an
        orchestrator LLM dynamically routes work to specialized agents.
        
        Args:
            user_query: Natural language question from user
            is_clarification_response: True if this is a response to a clarification question
            clarification_key: Key to lookup clarification context (if is_clarification_response=True)
            
        Returns:
            Dict with: success, user_query, sql, results, formatted_response, metadata, orchestration_metrics
        """
        self.request_count += 1
        time_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{time_str}] 🎯 Query: \"{user_query[:50]}{'...' if len(user_query) > 50 else ''}\"")
        
        # Reset orchestration metrics for this request
        self.orchestration_decisions = []
        
        # Initialize orchestration context
        orchestration_context = {
            "user_query": user_query,
            "current_state": "NEW_QUERY",
            "clarification_count": 0,
            "clarification_history": [],
            "results": {},
            "completed": False,
            "is_clarification_response": is_clarification_response,
            "clarification_key": clarification_key
        }
        
        # Handle clarification response context
        if is_clarification_response and clarification_key and clarification_key in self.clarification_context:
            context = self.clarification_context[clarification_key]
            orchestration_context["clarification_history"] = context["history"]
            orchestration_context["clarification_count"] = context["round"]
            
            # Add user's response to history
            orchestration_context["clarification_history"][-1]["response"] = user_query
            
            logger.info(f"[Request {self.request_count}] 🔄 Processing clarification round {orchestration_context['clarification_count']}")
        
        # Orchestration loop - LLM decides each step
        max_iterations = 10
        iteration = 0
        
        while not orchestration_context["completed"] and iteration < max_iterations:
            iteration += 1
            # Orchestration iteration (trimmed logging)
            
            # Ask orchestration LLM what to do next
            decision = self._get_orchestration_decision(orchestration_context)
            action_str = decision["action"]
            
            try:
                action = OrchestrationAction(action_str)
            except ValueError:
                logger.error(f"Invalid action from orchestration LLM: {action_str}")
                action = OrchestrationAction.GIVE_UP
                decision["reason"] = f"Invalid action: {action_str}"
            
            # LLM decision made (trimmed logging)
            
            # Defensive check: Auto-complete terminal states to prevent infinite loops
            if orchestration_context["current_state"] in ["PRICING_COMPLETE", "RESPONSE_COMPLETE"]:
                if action != OrchestrationAction.COMPLETE:
                    logger.warning(f"⚠️ [Request {self.request_count}] LLM chose {action.value} in terminal state {orchestration_context['current_state']} - forcing COMPLETE")
                    orchestration_context["completed"] = True
                    continue
            
            # Execute the chosen action
            if action == OrchestrationAction.CALL_PRICING_AGENT:
                # Safety check: Don't re-call if already done
                if orchestration_context["current_state"] == "PRICING_COMPLETE":
                    logger.warning(f"⚠️ [Request {self.request_count}] LLM chose CALL_PRICING_AGENT but pricing query already complete - forcing COMPLETE")
                    # Force completion instead of infinite loop
                    orchestration_context["completed"] = True
                    continue
                else:
                    time_str = datetime.now().strftime("%H:%M:%S")
                    print(f"[{time_str}] � Pricing analysis...")
                    
                    pricing_result = self.pricing_agent.handle_pricing_query(user_query)
                    
                    orchestration_context["results"]["pricing"] = pricing_result
                    orchestration_context["current_state"] = "PRICING_COMPLETE"
                    
                    status = "✅ Success" if pricing_result.success else "❌ Failed"
                    logger.info(f"[Request {self.request_count}] {status}: Pricing query complete")
            
            # Safety check: if LLM chose CALL_PLANNER but plan already complete with answerable status, force CALL_EXECUTOR instead
            if action == OrchestrationAction.CALL_PLANNER and orchestration_context["current_state"] == "PLANNING_COMPLETE":
                planning_result = orchestration_context["results"].get("planning", {})
                if planning_result.get("status") == "answerable":
                    logger.warning(f"[Request {self.request_count}] ⚠️ LLM chose CALL_PLANNER but plan already complete - forcing CALL_EXECUTOR")
                    action = OrchestrationAction.CALL_EXECUTOR
            
            if action == OrchestrationAction.CALL_PLANNER:
                # Re-plan (e.g., after clarification where previous plan was not answerable)
                if orchestration_context["current_state"] == "PLANNING_COMPLETE":
                    planning_result = orchestration_context["results"].get("planning", {})
                    if planning_result.get("status") != "answerable":
                        logger.info(f"[Request {self.request_count}] 📞 Re-calling Query Planning Agent (previous status: {planning_result.get('status')})")
                        planning_result = self.planner.plan_query(
                            user_query,
                            self.static_context,
                            orchestration_context["clarification_history"] if orchestration_context["clarification_history"] else None
                        )
                        orchestration_context["results"]["planning"] = planning_result
                        orchestration_context["current_state"] = "PLANNING_COMPLETE"
                        logger.info(f"[Request {self.request_count}] ✅ Planning complete: status={planning_result['status']}")
                    else:
                        # Re-plan (e.g., after clarification where previous plan was not answerable)
                        logger.info(f"[Request {self.request_count}] 📞 Re-calling Query Planning Agent (previous status: {planning_result.get('status')})")
                        planning_result = self.planner.plan_query(
                            user_query,
                            self.static_context,
                            orchestration_context["clarification_history"] if orchestration_context["clarification_history"] else None
                        )
                        orchestration_context["results"]["planning"] = planning_result
                        orchestration_context["current_state"] = "PLANNING_COMPLETE"
                        logger.info(f"[Request {self.request_count}] ✅ Planning complete: status={planning_result['status']}")
                else:
                    # First time planning
                    time_str = datetime.now().strftime("%H:%M:%S")
                    print(f"[{time_str}] � Planning query...")
                    planning_result = self.planner.plan_query(
                        user_query,
                        self.static_context,
                        orchestration_context["clarification_history"] if orchestration_context["clarification_history"] else None
                    )
                    orchestration_context["results"]["planning"] = planning_result
                    orchestration_context["current_state"] = "PLANNING_COMPLETE"
                    time_str = datetime.now().strftime("%H:%M:%S")
                    print(f"[{time_str}] 📋 Planning complete")
            
            elif action == OrchestrationAction.ASK_CLARIFICATION:
                logger.info(f"[Request {self.request_count}] ❓ Asking for clarification...")
                
                # Safety check: if already at max clarification rounds, convert to GIVE_UP
                if orchestration_context["clarification_count"] >= self.max_clarification_rounds:
                    logger.warning(f"[Request {self.request_count}] ⚠️ At max clarification rounds ({orchestration_context['clarification_count']}/{self.max_clarification_rounds}), converting ASK_CLARIFICATION to GIVE_UP")
                    action = OrchestrationAction.GIVE_UP
                    decision["reason"] = f"Max clarification rounds reached ({self.max_clarification_rounds})"
                    # Fall through to GIVE_UP handler below
                else:
                    planning_result = orchestration_context["results"].get("planning", {})
                    clarification_question = planning_result.get("clarification_question", "Could you provide more details?")
                    
                    # Increment clarification count
                    orchestration_context["clarification_count"] += 1
                    
                    # Build clarification history
                    if not orchestration_context["clarification_history"]:
                        orchestration_context["clarification_history"] = [{
                            "query": user_query,
                            "clarification": clarification_question
                        }]
                    else:
                        orchestration_context["clarification_history"].append({
                            "query": user_query,
                            "clarification": clarification_question
                        })
                    
                    # Determine clarification key
                    if clarification_key:
                        clarification_key_to_store = clarification_key
                    else:
                        clarification_key_to_store = user_query
                    
                    # Store context for next interaction
                    self.clarification_context[clarification_key_to_store] = {
                        "history": orchestration_context["clarification_history"],
                        "round": orchestration_context["clarification_count"],
                        "original_query": orchestration_context["clarification_history"][0]["query"]
                    }
                    
                    # Return clarification to user
                    result = {
                        "success": False,
                        "user_query": user_query,
                        "sql": None,
                        "results": None,
                        "response": clarification_question,
                        "formatted_response": None,
                        "metadata": {
                            "needs_clarification": True,
                            "planning_status": "needs_clarification",
                            "clarification_round": orchestration_context["clarification_count"],
                            "max_rounds": self.max_clarification_rounds,
                            "clarification_key": clarification_key_to_store
                        },
                        "orchestration_metrics": {
                            "iterations": iteration,
                            "decisions": self.orchestration_decisions,
                            "final_action": action.value
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
                    
                    logger.info(f"[Request {self.request_count}] 🔄 Waiting for user clarification...")
                    return result
            
            # Check if action was converted to GIVE_UP (due to max clarification check above)
            elif action == OrchestrationAction.CALL_EXECUTOR:
                # Safety check: Don't re-execute if already done successfully
                if orchestration_context["current_state"] == "EXECUTION_COMPLETE":
                    execution_result = orchestration_context["results"].get("execution", {})
                    if execution_result and execution_result.get("success"):
                        logger.warning(f"⚠️ [Request {self.request_count}] LLM chose CALL_EXECUTOR but execution already complete - skipping")
                        # Don't execute again, just continue to next iteration
                        continue
                    else:
                        logger.info(f"[Request {self.request_count}] 🔄 Re-executing due to previous failure")
                        planning_result = orchestration_context["results"].get("planning", {})
                        execution_plan = planning_result.get("plan", {})
                        
                        execution_result = self.query_executor.execute_query(
                            user_query,
                            self.static_context,
                            execution_plan
                        )
                        
                        orchestration_context["results"]["execution"] = execution_result
                        orchestration_context["current_state"] = "EXECUTION_COMPLETE"
                        
                        status = "✅ Success" if execution_result["success"] else "❌ Failed"
                        logger.info(f"[Request {self.request_count}] {status}: Execution complete")
                else:
                    # First time execution
                    time_str = datetime.now().strftime("%H:%M:%S")
                    print(f"[{time_str}] ⚡ Executing SQL...")
                    planning_result = orchestration_context["results"].get("planning", {})
                    execution_plan = planning_result.get("plan", {})
                    
                    execution_result = self.query_executor.execute_query(
                        user_query,
                        self.static_context,
                        execution_plan
                    )
                    
                    orchestration_context["results"]["execution"] = execution_result
                    orchestration_context["current_state"] = "EXECUTION_COMPLETE"
                    
                    status = "✅ Success" if execution_result["success"] else "❌ Failed"
                    logger.info(f"[Request {self.request_count}] {status}: Execution complete")
            
            elif action == OrchestrationAction.CALL_RESPONSE_AGENT:
                # Safety check: Don't re-format if already done
                if orchestration_context["current_state"] == "RESPONSE_COMPLETE":
                    logger.warning(f"⚠️ [Request {self.request_count}] LLM chose CALL_RESPONSE_AGENT but response already formatted - skipping")
                    # Don't format again, just continue to next iteration
                    continue
                else:
                    time_str = datetime.now().strftime("%H:%M:%S")
                    print(f"[{time_str}] � Formatting response...")
                    planning_result = orchestration_context["results"].get("planning", {})
                    execution_result = orchestration_context["results"].get("execution", {})
                    
                    formatting_result = self.response_agent.format_response(
                        user_query=user_query,
                        system_context=self.static_context,
                        execution_plan=planning_result.get("plan", {}),
                        sql=execution_result.get("sql"),
                        results=execution_result.get("results"),
                        metadata=execution_result.get("metadata", {})
                    )
                    
                    orchestration_context["results"]["response"] = formatting_result
                    orchestration_context["current_state"] = "RESPONSE_COMPLETE"
            
            elif action == OrchestrationAction.RETRY_PLANNING:
                logger.info(f"[Request {self.request_count}] 🔄 Retrying planning with error context...")
                
                # Add error context to results and retry planning
                execution_result = orchestration_context["results"].get("execution", {})
                error_info = execution_result.get("metadata", {}).get("error", "Unknown error")
                
                # Re-plan with error context (planner can see error in clarification history)
                planning_result = self.planner.plan_query(
                    user_query,
                    self.static_context,
                    orchestration_context["clarification_history"]
                )
                
                orchestration_context["results"]["planning"] = planning_result
                orchestration_context["current_state"] = "PLANNING_COMPLETE"
                
                logger.info(f"[Request {self.request_count}] ✅ Re-planning complete")
            
            elif action == OrchestrationAction.GIVE_UP:
                logger.warning(f"[Request {self.request_count}] ⚠️ Giving up: {decision.get('reason')}")
                
                # Clear clarification context if exists
                if clarification_key and clarification_key in self.clarification_context:
                    del self.clarification_context[clarification_key]
                
                # Build error response
                execution_result = orchestration_context["results"].get("execution", {})
                error_message = decision.get("reason", "Unable to process query")
                
                if orchestration_context["clarification_count"] >= self.max_clarification_rounds:
                    error_message = f"I've asked for clarification {self.max_clarification_rounds} times but still need more information. Please try rephrasing your question with more specific details."
                elif execution_result and not execution_result.get("success"):
                    error_message = f"Query execution failed: {execution_result.get('metadata', {}).get('error', 'Unknown error')}"
                
                result = {
                    "success": False,
                    "user_query": user_query,
                    "sql": execution_result.get("sql") if execution_result else None,
                    "results": None,
                    "response": error_message,
                    "formatted_response": None,
                    "metadata": {
                        "needs_clarification": False,
                        "give_up_reason": decision.get("reason"),
                        "clarification_count": orchestration_context["clarification_count"],
                        "max_rounds_reached": orchestration_context["clarification_count"] >= self.max_clarification_rounds
                    },
                    "orchestration_metrics": {
                        "iterations": iteration,
                        "decisions": self.orchestration_decisions,
                        "final_action": action.value
                    }
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
            
            elif action == OrchestrationAction.COMPLETE:
                logger.info(f"[Request {self.request_count}] ✅ Workflow complete!")
                orchestration_context["completed"] = True
                orchestration_context["current_state"] = "COMPLETED"
            
            # Note: We do NOT update state from LLM's decision["next_state"] because
            # each action handler above sets the correct state. The LLM's suggested
            # next_state is often incorrect and causes infinite loops.
        
        # Check if we exceeded max iterations
        if iteration >= max_iterations:
            logger.error(f"[Request {self.request_count}] ⚠️ Max iterations reached without completion")
            
            result = {
                "success": False,
                "user_query": user_query,
                "sql": None,
                "results": None,
                "response": "Workflow exceeded maximum iterations. Please try a simpler query.",
                "formatted_response": None,
                "metadata": {
                    "max_iterations_reached": True,
                    "iterations": iteration
                },
                "orchestration_metrics": {
                    "iterations": iteration,
                    "decisions": self.orchestration_decisions,
                    "final_action": "MAX_ITERATIONS"
                }
            }
            
            return result
        
        # Handle pricing query failures
        pricing_result = orchestration_context["results"].get("pricing")
        if pricing_result and not pricing_result.success:
            logger.error(f"[Request {self.request_count}] ❌ Pricing query failed: {pricing_result.error_message}")
            
            result = {
                "success": False,
                "user_query": user_query,
                "sql": None,
                "results": None,
                "response": pricing_result.formatted_response,
                "formatted_response": None,
                "metadata": pricing_result.metadata,
                "orchestration_metrics": {
                    "iterations": iteration,
                    "decisions": self.orchestration_decisions,
                    "final_action": "PRICING_QUERY_FAILED"
                }
            }
            
            # Store in conversation history
            history_entry = {
                "request_number": self.request_count,
                "user_query": user_query,
                "success": False,
                "sql": None,
                "response": result["response"],
                "metadata": result["metadata"],
                "orchestration_metrics": result["orchestration_metrics"]
            }
            self.conversation_history.append(history_entry)
            
            return result
        
        # Build final successful result
        planning_result = orchestration_context["results"].get("planning", {})
        execution_result = orchestration_context["results"].get("execution", {})
        formatting_result = orchestration_context["results"].get("response", {})
        pricing_result = orchestration_context["results"].get("pricing")
        
        # Clear clarification context if exists
        if clarification_key and clarification_key in self.clarification_context:
            del self.clarification_context[clarification_key]
        
        # Handle pricing query results
        if pricing_result:
            result = {
                "success": pricing_result.success,
                "user_query": user_query,
                "sql": None,  # Pricing queries don't generate SQL
                "results": pricing_result.data,
                "response": pricing_result.formatted_response,
                "display_data": {
                    "formatted_response": pricing_result.formatted_response,
                    "pricing_data": pricing_result.data,
                    "query_type": pricing_result.metadata.get("query_type"),
                    "agent": pricing_result.metadata.get("agent")
                },
                "metadata": pricing_result.metadata,
                "orchestration_metrics": {
                    "iterations": iteration,
                    "decisions": self.orchestration_decisions,
                    "final_action": OrchestrationAction.COMPLETE.value
                }
            }
        else:
            # Handle SQL query results
            result = {
                "success": True,
                "user_query": user_query,
                "sql": execution_result.get("sql"),
                "results": execution_result.get("results"),
                "response": formatting_result.get("formatted_response"),
                "display_data": formatting_result,
                "metadata": execution_result.get("metadata", {}),
                "orchestration_metrics": {
                    "iterations": iteration,
                    "decisions": self.orchestration_decisions,
                    "final_action": OrchestrationAction.COMPLETE.value
                }
            }
        
        # Log final success message
        time_str = datetime.now().strftime("%H:%M:%S")
        if pricing_result:
            print(f"[{time_str}] ✅ Cost estimate sent")
        else:
            row_count = formatting_result.get('row_count', 0)
            exec_time = formatting_result.get('execution_time', 'N/A')
            if isinstance(exec_time, str) and 's' in exec_time:
                exec_time_display = exec_time
            else:
                exec_time_display = f"{float(exec_time):.1f}s" if exec_time != 'N/A' else 'N/A'
            print(f"[{time_str}] 📊 Results: {row_count:,} rows ({exec_time_display})")
            time_str = datetime.now().strftime("%H:%M:%S")
            print(f"[{time_str}] ✅ Response sent")
        
        # Store in conversation history
        history_entry = {
            "request_number": self.request_count,
            "user_query": user_query,
            "success": result["success"],
            "sql": result["sql"],
            "response": result["response"],
            "display_data": result["display_data"],
            "metadata": result["metadata"],
            "execution_plan": planning_result.get("plan") if not pricing_result else None,
            "orchestration_metrics": result["orchestration_metrics"]
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
            "How much does 3 million Gemini input tokens cost?",  # Pricing query
            "What is the cost for 1000 Cloud Functions invocations?",  # Pricing query
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
