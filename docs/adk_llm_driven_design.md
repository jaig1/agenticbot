# Supervisor Agent Refactoring: LLM-Driven Orchestration Design

**Date:** October 22, 2025  
**Scope:** Refactor existing Supervisor Agent only (no new agents)  
**Pattern:** LLM-Based Orchestration with existing agents  
**Alignment:** Google ADK best practices

---

## 1. Executive Summary

This design refactors the **existing Supervisor Agent** from deterministic hardcoded routing to **LLM-driven orchestration**, while keeping all current agents (QueryPlanningAgent, QueryExecutionAgent, ResponseAgent) unchanged.

**Key Principle:** Replace if/else routing logic with LLM reasoning - the supervisor uses an LLM to decide which agent to call next and when to loop for clarification.

**Scope Constraints:**
- ✅ Refactor Supervisor Agent only
- ✅ Keep existing 3 agents unchanged (Planner, Executor, Response)
- ✅ Maintain current agent interfaces
- ✅ No new agent creation
- ✅ Minimal changes to existing codebase

---

## 2. Architecture Overview

### 2.1 Agent Hierarchy

```
CoordinatorAgent (LLM-driven root)
├── ClarificationAgent (LLM specialist)
├── QueryPlannerAgent (LLM specialist) 
├── QueryExecutorAgent (LLM specialist with BigQuery tool)
└── ResponseFormatterAgent (LLM specialist)
```

### 2.2 Communication Flow

```
User Query
    ↓
CoordinatorAgent (LLM decides routing)
    ↓
transfer_to_agent(agent_name="ClarificationAgent")  [if ambiguous]
    ↓
    ← User Response →
    ↓
transfer_to_agent(agent_name="QueryPlannerAgent")   [when clear]
    ↓
transfer_to_agent(agent_name="QueryExecutorAgent")  [after validation]
    ↓
transfer_to_agent(agent_name="ResponseFormatterAgent") [after execution]
    ↓
Final Response to User
```

### 2.3 State Management

All agents share `session.state` for communication:

```python
session.state = {
    "user_query": str,
    "clarification_history": List[Dict],
    "execution_plan": Dict,
    "sql_query": str,
    "query_results": List[Dict],
    "metadata": Dict,
    "formatted_response": str,
    "schema_context": str  # Loaded once, reused
}
```

---

## 3. Agent Specifications

### 3.1 CoordinatorAgent (Root LLM Agent)

**Role:** Intelligent orchestrator that routes queries through the system

**Configuration:**
```python
CoordinatorAgent = LlmAgent(
    name="Coordinator",
    model="gemini-2.5-flash",
    description="Main Text2SQL system orchestrator. Routes user queries to specialized agents.",
    instruction="""You are the coordinator for an enterprise Text2SQL system.

Your responsibilities:
1. Analyze incoming user queries
2. Determine if clarification is needed
3. Route to appropriate specialist agents
4. Handle errors and retry logic
5. Ensure user receives high-quality responses

Available Agents:
- ClarificationAgent: Handles ambiguous queries, asks clarifying questions
- QueryPlannerAgent: Validates queries and creates execution plans
- QueryExecutorAgent: Generates SQL and executes against BigQuery
- ResponseFormatterAgent: Formats results into natural language

Routing Logic:
- If query is ambiguous → transfer_to_agent(agent_name='ClarificationAgent')
- If query is clear → transfer_to_agent(agent_name='QueryPlannerAgent')
- After planning → transfer_to_agent(agent_name='QueryExecutorAgent')
- After execution → transfer_to_agent(agent_name='ResponseFormatterAgent')
- If any agent reports error → analyze and re-route or escalate to user

Important:
- Read session.state to understand current context
- Each agent saves results to session.state
- You orchestrate the flow, agents do the work
- Max 3 clarification rounds before giving up

Current session state: {state}
Conversation history: {history}
""",
    sub_agents=[
        ClarificationAgent(),
        QueryPlannerAgent(),
        QueryExecutorAgent(),
        ResponseFormatterAgent()
    ],
    tools=[],  # No direct tools, delegates to specialist agents
)
```

**State Interactions:**
- Reads: `state["user_query"]`, `state["clarification_history"]`, `state["execution_plan"]`
- Writes: None (pure orchestrator)
- Decisions: Routes based on state analysis

---

### 3.2 ClarificationAgent (Specialist LLM Agent)

**Role:** Handles ambiguous queries and multi-round clarification

**Configuration:**
```python
ClarificationAgent = LlmAgent(
    name="ClarificationAgent",
    model="gemini-2.5-flash",
    description="Specialist in query clarification. Identifies ambiguities and asks clarifying questions.",
    instruction="""You are a query clarification specialist.

Your job:
1. Analyze user queries for ambiguity
2. Identify what information is missing or unclear
3. Generate specific clarifying questions
4. Track clarification history
5. Determine when query is clear enough to proceed

Schema Context Available:
{schema_context}

Analysis Framework:
- Check if query references clear table/column names
- Identify vague terms ("top", "best", "recent")
- Detect missing filters, aggregations, or time ranges
- Assess if query is answerable with available data

Clarification History:
{clarification_history}

Current round: {clarification_round}
Max rounds: 3

Decision:
- If CLEAR → return {"status": "clear", "reason": "..."}
- If UNCLEAR → return {"status": "needs_clarification", "question": "...", "reason": "..."}
- If MAX_ROUNDS → return {"status": "give_up", "message": "..."}

Output format: JSON with status, question/reason, and updated clarification_history
""",
    output_schema=ClarificationResult,  # Pydantic model
    output_key="clarification_result",
    tools=[],
)
```

**State Interactions:**
- Reads: `state["user_query"]`, `state["clarification_history"]`, `state["schema_context"]`
- Writes: `state["clarification_result"]`, `state["clarification_history"]`
- Returns control: To Coordinator with decision

**Pydantic Schema:**
```python
from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict

class ClarificationResult(BaseModel):
    status: Literal["clear", "needs_clarification", "give_up"]
    question: Optional[str] = Field(None, description="Clarifying question to ask user")
    reason: str = Field(description="Why this decision was made")
    clarification_history: List[Dict] = Field(default_factory=list)
    clarification_round: int = Field(default=0)
```

---

### 3.3 QueryPlannerAgent (Specialist LLM Agent)

**Role:** Validates queries and creates structured execution plans

**Configuration:**
```python
QueryPlannerAgent = LlmAgent(
    name="QueryPlannerAgent",
    model="gemini-2.5-flash",
    description="Query validation and execution plan specialist. Creates structured plans for SQL generation.",
    instruction="""You are a query planning specialist for BigQuery Text2SQL.

Schema Context:
{schema_context}

User Query: {user_query}

Your job:
1. Validate query is answerable with available schema
2. Identify required tables and columns
3. Determine necessary JOINs
4. Specify filters, aggregations, ordering
5. Create structured execution plan

Validation Checks:
✓ All referenced tables exist
✓ All referenced columns exist
✓ JOIN relationships are valid
✓ Aggregations make sense for data types
✓ Query is within system capabilities

Execution Plan Format:
{
    "status": "valid",
    "tables": ["table1", "table2"],
    "columns": ["col1", "col2"],
    "joins": [{"type": "INNER JOIN", "table": "...", "on": "..."}],
    "filters": [{"column": "...", "operator": "...", "value": "..."}],
    "aggregations": [{"function": "SUM", "column": "..."}],
    "groupby": ["col1"],
    "orderby": [{"column": "...", "direction": "DESC"}],
    "limit": 10,
    "reasoning": "Detailed explanation of plan"
}

If invalid → return {"status": "invalid", "error": "...", "suggestion": "..."}
""",
    output_schema=ExecutionPlan,  # Pydantic model
    output_key="execution_plan",
    tools=[],
)
```

**State Interactions:**
- Reads: `state["user_query"]`, `state["schema_context"]`, `state["clarification_history"]`
- Writes: `state["execution_plan"]`
- Returns control: To Coordinator with validated plan

**Pydantic Schema:**
```python
class ExecutionPlan(BaseModel):
    status: Literal["valid", "invalid"]
    tables: List[str] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    joins: List[Dict] = Field(default_factory=list)
    filters: List[Dict] = Field(default_factory=list)
    aggregations: List[Dict] = Field(default_factory=list)
    groupby: List[str] = Field(default_factory=list)
    orderby: List[Dict] = Field(default_factory=list)
    limit: Optional[int] = None
    reasoning: str
    error: Optional[str] = None
    suggestion: Optional[str] = None
```

---

### 3.4 QueryExecutorAgent (Specialist LLM Agent with Tool)

**Role:** Generates SQL from execution plan and executes against BigQuery

**Configuration:**
```python
QueryExecutorAgent = LlmAgent(
    name="QueryExecutorAgent",
    model="gemini-2.5-flash",
    description="SQL generation and BigQuery execution specialist. Generates SQL from plans and executes queries.",
    instruction="""You are a BigQuery SQL generation and execution specialist.

Execution Plan: {execution_plan}
Schema Context: {schema_context}
Dataset: gen-lang-client-0454606702.insurance_analytics

Your job:
1. Generate BigQuery SQL from the execution plan
2. Ensure SQL follows BigQuery syntax and best practices
3. Execute SQL using the bigquery_execute tool
4. Return results and metadata

SQL Generation Rules:
- Use fully qualified table names: `project.dataset.table`
- Use table aliases (t1, t2, etc.)
- Follow execution plan exactly
- Add appropriate LIMIT if not specified (default 100)
- Handle NULLs properly
- Use appropriate data types

Available Tool:
- bigquery_execute(sql: str) → {"success": bool, "results": List[Dict], "metadata": Dict}

Process:
1. Generate SQL from plan
2. Validate SQL syntax
3. Call bigquery_execute(sql=generated_sql)
4. Return results

Output format: 
{
    "sql": "SELECT...",
    "success": bool,
    "results": [...],
    "metadata": {
        "execution_time": float,
        "rows_returned": int,
        "bytes_processed": int
    }
}
""",
    output_schema=ExecutionResult,  # Pydantic model
    output_key="execution_result",
    tools=[bigquery_execute_tool],  # Custom BigQuery tool
)
```

**Tool Specification:**
```python
from google.adk.tools import FunctionTool

def bigquery_execute(sql: str) -> Dict[str, Any]:
    """
    Execute SQL query against BigQuery.
    
    Args:
        sql: Valid BigQuery SQL query
        
    Returns:
        Dict with success, results, and metadata
    """
    from src.database.connector import DatabaseConnector
    
    connector = DatabaseConnector()
    result = connector.execute_query(sql)
    
    return {
        "success": result["success"],
        "results": result["results"],
        "metadata": {
            "execution_time": result["execution_time"],
            "rows_returned": len(result["results"]) if result["success"] else 0,
            "bytes_processed": result.get("bytes_processed", 0)
        }
    }

bigquery_execute_tool = FunctionTool(func=bigquery_execute)
```

**State Interactions:**
- Reads: `state["execution_plan"]`, `state["schema_context"]`
- Writes: `state["execution_result"]`, `state["sql_query"]`
- Returns control: To Coordinator with results

**Pydantic Schema:**
```python
class ExecutionResult(BaseModel):
    sql: str
    success: bool
    results: List[Dict] = Field(default_factory=list)
    metadata: Dict[str, Any]
    error: Optional[str] = None
```

---

### 3.5 ResponseFormatterAgent (Specialist LLM Agent)

**Role:** Formats query results into natural language explanations

**Configuration:**
```python
ResponseFormatterAgent = LlmAgent(
    name="ResponseFormatterAgent",
    model="gemini-2.5-flash",
    description="Response formatting specialist. Converts query results into natural language explanations.",
    instruction="""You are a response formatting specialist.

User Query: {user_query}
SQL Query: {sql_query}
Query Results: {query_results}
Metadata: {execution_metadata}

Your job:
1. Understand what the user asked
2. Analyze the query results
3. Format a clear, conversational response
4. Include key insights and context
5. Structure the response appropriately

Response Structure:
1. Direct Answer (1-2 sentences addressing the question)
2. Key Findings (bullet points or highlights)
3. Context/Explanation (how the data was retrieved)
4. Additional Insights (if relevant)

Formatting Guidelines:
- Use natural, conversational English
- Highlight important numbers with **bold**
- Use bullet points for multiple items
- Keep it concise but informative
- Avoid technical jargon unless necessary
- Don't show SQL unless user asks

Sample Results: {sample_results}  # First 10 rows
Total Rows: {total_rows}
Execution Time: {execution_time}s

Output format:
{
    "formatted_response": "Natural language response text",
    "response_structure": {
        "direct_answer": "...",
        "key_findings": [...],
        "context": "...",
        "insights": "..."
    },
    "metadata": {
        "response_length": int,
        "used_samples": bool
    }
}
""",
    output_schema=FormattedResponse,  # Pydantic model
    output_key="formatted_response",
    tools=[],
)
```

**State Interactions:**
- Reads: `state["user_query"]`, `state["sql_query"]`, `state["execution_result"]`
- Writes: `state["formatted_response"]`
- Returns control: To Coordinator with final response

**Pydantic Schema:**
```python
class FormattedResponse(BaseModel):
    formatted_response: str
    response_structure: Dict[str, Any]
    metadata: Dict[str, Any]
```

---

## 4. Implementation Structure

### 4.1 Directory Layout

```
src/agents/adk/
├── __init__.py
├── coordinator.py           # CoordinatorAgent
├── clarification.py         # ClarificationAgent
├── planner.py              # QueryPlannerAgent
├── executor.py             # QueryExecutorAgent
├── formatter.py            # ResponseFormatterAgent
├── schemas.py              # All Pydantic models
└── tools/
    ├── __init__.py
    ├── bigquery_tool.py    # BigQuery execution tool
    └── schema_tool.py      # Schema retrieval tool (optional)
```

### 4.2 Core Implementation

**src/agents/adk/coordinator.py:**
```python
"""
ADK Coordinator Agent - LLM-Driven Text2SQL Orchestrator
"""

from google.adk.agents import LlmAgent
from google.adk.sessions import Session
from google.adk.runners import Runner
from google.genai import types

from .clarification import create_clarification_agent
from .planner import create_query_planner_agent
from .executor import create_query_executor_agent
from .formatter import create_response_formatter_agent
from .schemas import CoordinatorInstruction


def create_coordinator_agent(schema_context: str) -> LlmAgent:
    """
    Create the root coordinator agent with all specialist sub-agents.
    
    Args:
        schema_context: Database schema context
        
    Returns:
        Configured LlmAgent coordinator
    """
    
    # Initialize specialist agents
    clarification_agent = create_clarification_agent(schema_context)
    planner_agent = create_query_planner_agent(schema_context)
    executor_agent = create_query_executor_agent(schema_context)
    formatter_agent = create_response_formatter_agent()
    
    # Create coordinator with LLM-driven routing
    coordinator = LlmAgent(
        name="Coordinator",
        model="gemini-2.5-flash",
        description="Main Text2SQL system orchestrator",
        
        instruction="""You are the coordinator for an enterprise Text2SQL system.

Available Agents and Their Roles:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ClarificationAgent
   - Handles ambiguous queries
   - Asks clarifying questions
   - Manages multi-round clarification (max 3 rounds)
   - Use when: Query is vague, missing details, or unclear

2. QueryPlannerAgent
   - Validates queries against schema
   - Creates structured execution plans
   - Checks data availability
   - Use when: Query is clear and needs validation

3. QueryExecutorAgent
   - Generates BigQuery SQL
   - Executes queries
   - Returns results and metadata
   - Use when: Valid execution plan exists

4. ResponseFormatterAgent
   - Formats results into natural language
   - Creates user-friendly explanations
   - Use when: Query execution successful

Routing Decision Framework:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Analyze Current State
   - Read session.state for context
   - Check clarification_history
   - Review any previous errors

Step 2: Determine Next Agent
   - NEW QUERY + AMBIGUOUS → ClarificationAgent
   - NEW QUERY + CLEAR → QueryPlannerAgent
   - CLARIFICATION COMPLETE → QueryPlannerAgent
   - PLANNING COMPLETE → QueryExecutorAgent
   - EXECUTION COMPLETE → ResponseFormatterAgent
   - ANY ERROR → Analyze and re-route or inform user

Step 3: Transfer Control
   - Use: transfer_to_agent(agent_name='AgentName')
   - ADK handles the routing automatically

Current Session State:
{state}

Clarification Round: {clarification_round}/3
""",
        
        sub_agents=[
            clarification_agent,
            planner_agent,
            executor_agent,
            formatter_agent
        ],
        
        tools=[],  # Pure orchestrator, no direct tools
        
        # Allow transfer to any sub-agent
        disallow_transfer_to_parent=True,  # No parent to transfer to
        disallow_transfer_to_peers=False,  # Can transfer between sub-agents
    )
    
    return coordinator


class ADKSupervisorAgent:
    """
    ADK-based Supervisor Agent using LLM-driven orchestration.
    
    Replaces deterministic routing with intelligent LLM decision-making.
    """
    
    def __init__(self, app_name: str = "text2sql"):
        """
        Initialize ADK Supervisor Agent.
        
        Args:
            app_name: Application name for session management
        """
        from google.adk.sessions import InMemorySessionService
        from pathlib import Path
        import logging
        
        self.logger = logging.getLogger(__name__)
        self.app_name = app_name
        
        # Load schema context
        self.schema_context = self._load_schema_context()
        
        # Create coordinator agent
        self.coordinator = create_coordinator_agent(self.schema_context)
        
        # Initialize session service
        self.session_service = InMemorySessionService()
        
        # Create runner
        self.runner = Runner(
            agent=self.coordinator,
            app_name=self.app_name,
            session_service=self.session_service
        )
        
        self.logger.info("ADK Supervisor Agent initialized")
    
    def _load_schema_context(self) -> str:
        """Load schema context from config file."""
        from pathlib import Path
        
        context_file = Path(__file__).parent.parent.parent.parent / "config" / "systemcontext.md"
        
        if not context_file.exists():
            raise FileNotFoundError(f"Schema context not found: {context_file}")
        
        with open(context_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def handle_query(self, user_id: str, session_id: str, query: str) -> Dict[str, Any]:
        """
        Handle user query with LLM-driven orchestration.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query: User's natural language query
            
        Returns:
            Dict with response and metadata
        """
        from google.genai import types
        
        # Get or create session
        session = self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if session is None:
            session = self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
        
        # Initialize state with schema context
        if "schema_context" not in session.state:
            session.state["schema_context"] = self.schema_context
            session.state["clarification_round"] = 0
            session.state["clarification_history"] = []
        
        # Set current query
        session.state["user_query"] = query
        
        # Create user message
        user_message = types.Content(
            role='user',
            parts=[types.Part(text=query)]
        )
        
        # Run through coordinator (LLM decides routing)
        events = self.runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        )
        
        # Collect events and extract final response
        final_response = None
        event_log = []
        
        for event in events:
            event_log.append({
                "author": event.author if hasattr(event, 'author') else None,
                "type": type(event).__name__,
                "timestamp": event.timestamp if hasattr(event, 'timestamp') else None
            })
            
            if event.is_final_response() and event.content:
                final_response = event.content.parts[0].text
        
        # Extract results from session state
        result = {
            "success": session.state.get("execution_result", {}).get("success", False),
            "query": query,
            "response": final_response or session.state.get("formatted_response", {}).get("formatted_response", ""),
            "sql": session.state.get("execution_result", {}).get("sql"),
            "results": session.state.get("execution_result", {}).get("results", []),
            "metadata": {
                "execution_plan": session.state.get("execution_plan"),
                "execution_metadata": session.state.get("execution_result", {}).get("metadata", {}),
                "clarification_round": session.state.get("clarification_round", 0),
                "event_log": event_log
            }
        }
        
        return result
    
    def get_session_history(self, user_id: str, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        session = self.session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if session and hasattr(session, 'history'):
            return session.history
        return []
    
    def clear_session(self, user_id: str, session_id: str):
        """Clear session state."""
        self.session_service.delete_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id
        )
```

---

## 5. Advantages of Full LLM-Driven Approach

### 5.1 Intelligence & Adaptability
✅ **Dynamic Routing**: LLM decides routing based on context, not hardcoded rules  
✅ **Contextual Awareness**: Coordinator understands conversation flow and history  
✅ **Error Recovery**: LLM can intelligently retry or re-route on failures  
✅ **Natural Clarification**: No hardcoded 3-round limit - LLM knows when query is clear enough

### 5.2 Scalability & Extensibility
✅ **Easy Agent Addition**: New specialists just need clear descriptions  
✅ **Self-Documenting**: Agent descriptions serve as documentation  
✅ **No Code Changes**: Add capabilities via new agents, not code modifications  
✅ **Flexible Workflows**: LLM can create dynamic workflows based on needs

### 5.3 Google Cloud Alignment
✅ **ADK Best Practices**: Uses official Google patterns  
✅ **Vertex AI Integration**: Deploy to Agent Engine for production  
✅ **Built-in Observability**: ADK provides tracing, logging, evaluation  
✅ **Enterprise Ready**: Session management, state persistence, error handling

### 5.4 Development Experience
✅ **Declarative**: Describe what agents do, not how routing works  
✅ **Testable**: Each agent can be tested independently  
✅ **Maintainable**: Changes localized to specific agents  
✅ **Debuggable**: ADK events provide full execution trace

---

## 6. Migration Path

### Phase 1: Parallel Implementation (Week 1-2)
- [ ] Install ADK: `pip install google-adk`
- [ ] Create `src/agents/adk/` directory structure
- [ ] Implement Pydantic schemas
- [ ] Build individual specialist agents
- [ ] Test each agent independently

### Phase 2: Integration (Week 3)
- [ ] Implement CoordinatorAgent
- [ ] Create ADKSupervisorAgent wrapper
- [ ] Add session management
- [ ] Test end-to-end flow
- [ ] Compare with existing supervisor

### Phase 3: Production Readiness (Week 4)
- [ ] Add comprehensive error handling
- [ ] Implement logging and tracing
- [ ] Create evaluation test suite
- [ ] Performance optimization
- [ ] Documentation

### Phase 4: Deployment (Week 5)
- [ ] Deploy to Vertex AI Agent Engine
- [ ] Set up monitoring and alerts
- [ ] Gradual rollout (10% → 50% → 100%)
- [ ] Retire old supervisor

---

## 7. Cost Considerations

### LLM Call Analysis

**Current Deterministic Approach:**
- Query → Planner (1 call)
- Planner → Executor (1 call)
- Executor → Response (1 call)
- **Total: 3 LLM calls per query**

**ADK LLM-Driven Approach:**
- Query → Coordinator routing decision (1 call)
- Coordinator → ClarificationAgent (1 call if needed)
- Coordinator → QueryPlannerAgent (1 call)
- Coordinator → QueryExecutorAgent (1 call)
- Coordinator → ResponseFormatterAgent (1 call)
- **Total: 4-6 LLM calls per query** (depending on clarification)

**Cost Impact:**
- +33-100% LLM calls
- Offset by: Better accuracy, reduced user frustration, fewer retries
- Mitigation: Use cheaper model for Coordinator (flash-lite), cache routing decisions

---

## 8. Testing Strategy

### 8.1 Unit Tests (Per Agent)
```python
def test_clarification_agent_clear_query():
    """Test that clear queries are marked as clear."""
    agent = create_clarification_agent(schema_context)
    result = agent.run(
        session_state={"user_query": "Show me total claims grouped by status"}
    )
    assert result["clarification_result"]["status"] == "clear"

def test_clarification_agent_ambiguous_query():
    """Test that ambiguous queries generate questions."""
    agent = create_clarification_agent(schema_context)
    result = agent.run(
        session_state={"user_query": "Show me top customers"}
    )
    assert result["clarification_result"]["status"] == "needs_clarification"
    assert "question" in result["clarification_result"]
```

### 8.2 Integration Tests (Multi-Agent Flow)
```python
def test_full_flow_clear_query():
    """Test complete flow with clear query."""
    supervisor = ADKSupervisorAgent()
    result = supervisor.handle_query(
        user_id="test_user",
        session_id="test_session",
        query="How many customers do we have?"
    )
    assert result["success"] == True
    assert "sql" in result
    assert len(result["results"]) > 0
```

### 8.3 ADK Evaluation Framework
```python
from google.adk.evaluate import Evaluator, Criteria

evaluator = Evaluator(
    agent=coordinator_agent,
    test_cases=[
        {
            "input": "Show me claims",
            "expected_clarification": True
        },
        {
            "input": "Total claim amount by status",
            "expected_clarification": False,
            "expected_sql_contains": "SUM"
        }
    ],
    criteria=[
        Criteria.accuracy(),
        Criteria.hallucination(),
        Criteria.response_quality()
    ]
)

results = evaluator.evaluate()
```

---

## 9. Monitoring & Observability

### 9.1 ADK Built-in Tracing
```python
from google.adk.observability import CloudTrace

coordinator = create_coordinator_agent(
    schema_context,
    callbacks=[CloudTrace()]  # Automatic GCP Cloud Trace integration
)
```

### 9.2 Custom Metrics
```python
from google.adk.callbacks import CallbackContext

class MetricsCallback:
    def after_agent_call(self, ctx: CallbackContext):
        # Track agent transitions
        metrics.increment(f"agent.{ctx.agent.name}.calls")
        metrics.histogram(f"agent.{ctx.agent.name}.duration", ctx.duration)
        
        # Track routing decisions
        if ctx.agent.name == "Coordinator":
            next_agent = extract_transfer_from_response(ctx.response)
            metrics.increment(f"routing.{next_agent}")
```

### 9.3 Cost Tracking
```python
def track_llm_costs(event):
    if hasattr(event, 'usage'):
        input_tokens = event.usage.prompt_tokens
        output_tokens = event.usage.completion_tokens
        
        # Gemini 2.5 Flash pricing (example)
        cost = (input_tokens * 0.000075 + output_tokens * 0.0003) / 1000
        
        metrics.increment("llm.cost", cost)
        metrics.increment(f"llm.{event.author}.cost", cost)
```

---

## 10. Success Criteria

### 10.1 Functional Requirements
- [ ] All queries handled through LLM-driven routing
- [ ] Clarification works for ambiguous queries
- [ ] SQL generation accuracy ≥ 95%
- [ ] Response quality score ≥ 4.0/5.0
- [ ] Error handling covers all edge cases

### 10.2 Performance Requirements
- [ ] Latency ≤ 5s for simple queries
- [ ] Latency ≤ 10s for complex queries with clarification
- [ ] 99.9% uptime in production
- [ ] Cost per query ≤ $0.01

### 10.3 Quality Requirements
- [ ] Routing accuracy ≥ 98%
- [ ] Clarification relevance score ≥ 90%
- [ ] No hallucinations in responses
- [ ] All test cases passing

---

## 11. Next Steps

1. **Review & Approve Design** ✓
2. **Install Dependencies**: `pip install google-adk`
3. **Create Project Structure**: Set up `src/agents/adk/`
4. **Implement Schemas**: Define all Pydantic models
5. **Build Agents**: Create each specialist agent
6. **Test Individual Agents**: Unit tests for each
7. **Integrate Coordinator**: Wire everything together
8. **End-to-End Testing**: Full flow validation
9. **Deploy & Monitor**: Vertex AI Agent Engine

---

## 12. References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Multi-Agent Systems in ADK](https://google.github.io/adk-docs/agents/multi-agents/)
- [LLM Agent Transfer](https://google.github.io/adk-docs/agents/llm-agents/)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [Agent Starter Pack](https://github.com/GoogleCloudPlatform/agent-starter-pack)

---

**Document Status:** Draft for Review  
**Next Review:** After stakeholder feedback  
**Implementation Start:** Upon approval
