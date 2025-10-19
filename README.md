# AgenticBot - BigQuery Text2SQL Agent

A multi-agent Text2SQL system that converts natural language queries into SQL, executes them against BigQuery, and returns formatted results with natural language explanations. Built with Vertex AI Gemini and Application Default Credentials (ADC).

## Architecture

**3-Agent Architecture (Phase 2.2):**
- **Query Planner Agent**: Validates queries, creates execution plans, generates clarification questions
- **Query Execution Agent**: Generates SQL from execution plans and executes queries
- **Response Agent**: Formats raw results into natural language explanations
- **Supervisor Agent**: Orchestrates the pipeline, manages schema context, tracks conversation history

```
User Query 
  ↓
Supervisor Agent
  ↓
Query Planner (validates + creates plan)
  ↓
Query Execution Agent (generates SQL + executes)
  ↓
Response Agent (formats in natural language)
  ↓
User-friendly Response with Explanations
```

## Features

- **3-Agent Architecture**: Specialized agents for planning, execution, and response formatting
- **Query Validation**: LLM-based validation with smart clarification questions
- **Natural Language Responses**: User-friendly explanations with methodology and context
- **Automated Schema Discovery**: Introspect BigQuery datasets and generate comprehensive documentation
- **Query Generation**: Generate test SQL queries automatically from discovered schema
- **Text2SQL Conversion**: Convert natural language to SQL using Vertex AI Gemini
- **Query Execution**: Execute SQL queries against BigQuery with ADC authentication
- **Conversation Tracking**: Full history of queries, responses, and metadata
- **End-to-End Pipeline**: Complete workflow from natural language to formatted results

## Prerequisites

- Python 3.13+
- Google Cloud Project with BigQuery enabled
- Vertex AI API enabled
- UV package manager installed
- Application Default Credentials configured

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd agenticbot

# Install dependencies
uv sync
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Required variables:
# - GCP_PROJECT_ID
# - BQ_DATASET_ID
# - VERTEX_AI_LOCATION
# - GEMINI_MODEL_NAME
```

### 3. Authenticate

```bash
# Configure Application Default Credentials
gcloud auth application-default login

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com

# Enable BigQuery API (if not already enabled)
gcloud services enable bigquery.googleapis.com
```

### 4. Discover Schema

```bash
# Introspect BigQuery dataset and generate schema documentation
uv run python scripts/discover_schema.py

# This creates: config/schema.json
```

### 5. Generate Test Queries

```bash
# Generate example SQL queries from schema
uv run python scripts/generate_queries.py

# This creates: config/query_examples.json
```

### 6. Generate System Context

```bash
# Create LLM-ready context for Text2SQL
uv run python scripts/generate_context.py

# This creates: config/systemcontext.md
```

### 7. Run Supervisor Agent

```bash
# Run internal tests
uv run python src/agents/supervisor.py

# Run interactive demo
uv run python src/agents/supervisor_demo.py
```

## Project Structure

```
agenticbot/
├── config/
│   ├── schema.json           # BigQuery schema metadata
│   ├── query_examples.json   # Generated test queries
│   └── systemcontext.md      # LLM-ready schema context
├── scripts/
│   ├── discover_schema.py    # Schema discovery automation
│   ├── generate_queries.py   # Query generation automation
│   └── generate_context.py   # Context generation automation
├── src/
│   ├── agents/
│   │   ├── supervisor.py          # Orchestrator agent
│   │   ├── supervisor_demo.py     # Supervisor demonstration
│   │   ├── query_planner.py       # Query validation agent
│   │   ├── query_execution.py     # SQL generation & execution agent
│   │   └── response_agent.py      # Response formatting agent
│   ├── database/
│   │   ├── connector.py      # BigQuery connector with ADC
│   │   └── connector_demo.py # Connector demonstration
│   └── utils/
├── tests/
├── .env                      # Environment configuration (not in git)
├── .env.example              # Example environment file
├── pyproject.toml            # UV project configuration
└── README.md                 # This file
```

## Components

### 1. Schema Discovery (`scripts/discover_schema.py`)

**Purpose**: Automatically introspect BigQuery dataset and generate comprehensive schema documentation.

**Features**:
- Discovers all tables in dataset
- Extracts column metadata (name, type, mode, description)
- Infers primary keys and foreign keys
- Identifies relationships between tables
- Captures sample data
- Detects partitioning and clustering
- Generates business glossary

**Usage**:
```bash
uv run python scripts/discover_schema.py
```

**Output**: `config/schema.json`

### 2. Query Generation (`scripts/generate_queries.py`)

**Purpose**: Generate diverse test SQL queries based on discovered schema.

**Features**:
- Generates count, select, aggregation, and join queries
- Includes difficulty levels (easy, medium, hard)
- Tags queries by type
- Optimizes for partitioned tables
- Creates realistic test cases

**Usage**:
```bash
uv run python scripts/generate_queries.py
```

**Output**: `config/query_examples.json`

### 3. Context Generation (`scripts/generate_context.py`)

**Purpose**: Create LLM-ready system context for Text2SQL generation.

**Features**:
- Combines schema and query examples
- Formats as markdown for LLM consumption
- Includes BigQuery-specific guidelines
- Provides business context
- Token-optimized for Gemini models

**Usage**:
```bash
uv run python scripts/generate_context.py
```

**Output**: `config/systemcontext.md`

### 4. Database Connector (`src/database/connector.py`)

**Purpose**: Execute SQL queries against BigQuery using ADC.

**Features**:
- Application Default Credentials authentication
- Query execution with timeout protection
- SQL syntax validation (dry run)
- Comprehensive error handling
- Query metadata (execution time, bytes processed, etc.)
- Handles BigQuery data types (Decimal, dates)

**Usage**:
```python
from src.database.connector import DatabaseConnector

connector = DatabaseConnector()
results, metadata = connector.execute_query("SELECT * FROM table LIMIT 10")

if metadata["success"]:
    print(f"Rows: {metadata['row_count']}")
    print(f"Time: {metadata['execution_time_seconds']}s")
```

**Demo**:
```bash
uv run python src/database/connector_demo.py
```

### 5. Supervisor Agent (`src/agents/supervisor.py`)

**Purpose**: Orchestrate the 3-agent Text2SQL pipeline and manage the overall system.

**Responsibilities**:
- Load and cache schema context from `config/systemcontext.md`
- Initialize and manage all agents (Query Planner, Query Execution, Response Agent)
- Route user queries through the pipeline
- Track conversation history
- Provide session statistics

**Features**:
- Central orchestration point for 3-agent architecture
- Schema context management
- Conversation history tracking
- Success rate statistics
- Clean separation of concerns

**Usage**:
```python
from src.agents.supervisor import SupervisorAgent

# Initialize once
supervisor = SupervisorAgent()

# Process queries
result = supervisor.handle_query("How many insurance customers do we have?")

if result["success"]:
    print(f"SQL: {result['sql']}")
    print(f"Response: {result['response']}")  # Natural language explanation
    print(f"Summary: {result['summary']}")
    print(f"Rows: {result['metadata']['row_count']}")

# Get statistics
stats = supervisor.get_stats()
print(f"Success rate: {stats['success_rate']:.1%}")

# Get history
history = supervisor.get_conversation_history()
```

**Test**:
```bash
# Run internal tests
uv run python src/agents/supervisor.py

# Run interactive demo
uv run python src/agents/supervisor_demo.py
```

---

### 6. Query Planner Agent (`src/agents/query_planner.py`)

**Purpose**: Validate queries and create execution plans using LLM.

**Responsibilities**:
- Analyze user queries to determine if they can be answered
- Create detailed execution plans for answerable queries
- Generate smart clarification questions for unanswerable queries
- Identify required tables and operations

**Features**:
- LLM-based query validation
- Execution plan generation (intent, tables, operations)
- Smart clarification question generation
- JSON-structured output

**Returns**:
- For answerable queries: `{"status": "answerable", "plan": {...}}`
- For unanswerable queries: `{"status": "needs_clarification", "clarification_question": "..."}`

---

### 7. Query Execution Agent (`src/agents/query_execution.py`)

**Purpose**: Generate SQL from execution plans and execute queries.

**Responsibilities**:
- Generate SQL from execution plan using Vertex AI Gemini
- Execute SQL queries via Database Connector
- Return raw results and metadata
- Handle errors gracefully

**Features**:
- Execution plan-guided SQL generation
- Vertex AI Gemini integration
- Automatic SQL cleaning (removes markdown, comments)
- Raw result formatting

**Returns**:
```python
{
    "success": True,
    "sql": "SELECT COUNT(*) ...",
    "results": [...],
    "metadata": {"row_count": 1, "execution_time_seconds": 0.5, ...}
}
```

---

### 8. Response Agent (`src/agents/response_agent.py`)

**Purpose**: Format raw query results into natural language explanations.

**Responsibilities**:
- Transform raw SQL results into user-friendly explanations
- Explain methodology and reasoning
- Provide context and insights
- Make technical results accessible to business users

**Features**:
- LLM-powered natural language generation
- Professional business-friendly tone
- Methodology explanation
- Result summaries
- Fallback simple formatting

**Returns**:
```python
{
    "formatted_response": "Based on your question...",
    "summary": "5 results found",
    "methodology": "Analysis joined tables, calculated aggregations."
}
```

---

## Request Flow

```
1. User submits natural language query
       ↓
2. Supervisor Agent receives query
       ↓
3. Query Planner validates query and creates execution plan
       ↓
4. Query Execution Agent generates SQL (using plan) and executes
       ↓
5. Response Agent formats results into natural language
       ↓
6. Supervisor logs result and updates history
       ↓
7. User receives formatted response with explanations
```

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Google Cloud Configuration
GCP_PROJECT_ID=your-gcp-project-id
BQ_DATASET_ID=your_bigquery_dataset_name
BQ_LOCATION=US

# Service Account (for reference)
GOOGLE_CLOUD_SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com

# Vertex AI Configuration
VERTEX_AI_LOCATION=us-central1
GEMINI_MODEL_NAME=gemini-2.5-flash-lite

# Optional Settings
BQ_TABLE_PREFIX=insurance_
BQ_ENABLE_PARTITIONING=true
BQ_ENABLE_CLUSTERING=true
LOG_LEVEL=INFO
```

### Authentication

**Application Default Credentials (ADC)**:

For local development:
```bash
gcloud auth application-default login
```

For production (service accounts):
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

Or use service account impersonation:
```bash
gcloud auth application-default login --impersonate-service-account=SA_EMAIL
```

### API Enablement

```bash
# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## Workflow

## Workflow

### Complete Pipeline

```bash
# 1. Discover BigQuery schema
uv run python scripts/discover_schema.py

# 2. Generate test queries
uv run python scripts/generate_queries.py

# 3. Generate LLM context
uv run python scripts/generate_context.py

# 4. Test database connector
uv run python src/database/connector_demo.py

# 5. Test Supervisor Agent (orchestrator)
uv run python src/agents/supervisor.py

# 6. Run Supervisor demo (recommended - full 3-agent pipeline)
uv run python src/agents/supervisor_demo.py
```

### Typical Usage (Recommended: Supervisor Agent)

```python
from src.agents.supervisor import SupervisorAgent

# Initialize Supervisor (loads schema, initializes all agents)
supervisor = SupervisorAgent()

# Process multiple queries
queries = [
    "How many customers do we have?",
    "What is the average claim amount?",
    "Show me pending claims",
]

for query in queries:
    result = supervisor.handle_query(query)
    
    if result["success"]:
        print(f"Query: {query}")
        print(f"SQL: {result['sql']}")
        print(f"Response: {result['response']}")  # Natural language explanation
        print(f"Summary: {result['summary']}")
        print(f"Methodology: {result['methodology']}")

# Get session statistics
stats = supervisor.get_stats()
print(f"Success rate: {stats['success_rate']:.1%}")

# Get conversation history
history = supervisor.get_conversation_history()
```

### Multi-Agent Architecture Usage

```python
from src.agents.supervisor import SupervisorAgent

# Initialize Supervisor once (loads schema, initializes all 3 agents)
supervisor = SupervisorAgent()

# Process multiple queries
queries = [
    "How many customers do we have?",
    "What is the average claim amount?",
    "Show me pending claims",
]

for query in queries:
    result = supervisor.handle_query(query)
    
    if result["success"]:
        print(f"Query: {query}")
        print(f"SQL: {result['sql']}")
        print(f"Response: {result['response']}")
        print(f"Time: {result['metadata']['execution_time_seconds']}s")
    else:
        print(f"Error: {result['response']}")

# Get session statistics
stats = supervisor.get_stats()
print(f"\nSuccess Rate: {stats['success_rate']:.1%}")
print(f"Total Queries: {stats['total_requests']}")

# Get conversation history
history = supervisor.get_conversation_history()
for entry in history:
    print(f"[{entry['request_number']}] {entry['user_query']}: {entry['success']}")
        print()
```

## Development Status

**Phase 1.1 - Monolithic POC:**
- [x] UV project initialization
- [x] Schema discovery automation
- [x] Query generation automation
- [x] System context generation
- [x] Database connector with ADC

**Phase 1.2 - Multi-Agent Architecture:**
- [x] Supervisor agent (orchestrator)
- [x] Conversation history tracking
- [x] Session statistics
- [x] Multi-agent request flow

**Phase 2.1 - Query Planning:**
- [x] Query Planning Agent (LLM-based validation)
- [x] Execution plan generation
- [x] Smart clarification questions
- [x] Answerability detection

**Phase 2.2 - Specialized Agents:**
- [x] Query Execution Agent (SQL generation + execution)
- [x] Response Agent (natural language formatting)
- [x] 3-agent architecture complete
- [x] User-friendly response explanations

**Phase 3 - Future Enhancements:**
- [ ] Error recovery and retry logic
- [ ] Multi-turn conversations
- [ ] Query optimization agent
- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] Comprehensive API documentation
- [ ] Deployment guide

## Troubleshooting

### Authentication Issues

```bash
# Check ADC status
gcloud auth application-default print-access-token

# Revoke and re-authenticate
gcloud auth application-default revoke
gcloud auth application-default login
```

### Schema Discovery Fails

```bash
# Verify BigQuery access
bq ls --project_id=YOUR_PROJECT_ID

# Check dataset permissions
bq show --project_id=YOUR_PROJECT_ID YOUR_DATASET_ID
```

### Vertex AI Errors

```bash
# Verify API enabled
gcloud services list --enabled | grep aiplatform

# Enable if missing
gcloud services enable aiplatform.googleapis.com

# Check quota
gcloud alpha services quota list --service=aiplatform.googleapis.com
```

### SQL Generation Issues

- Check `config/systemcontext.md` exists
- Verify Gemini model name is correct
- Review Vertex AI logs in Cloud Console
- Try simpler queries first

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]
