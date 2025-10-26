"""
Streamlit Text2SQL Interface - Iteration 1: Basic Chat

A web interface for the AgenticBot Text2SQL system using Streamlit.
Provides a chat-based interface for querying BigQuery using natural language.
"""

import os

# Suppress gRPC and ALTS warnings BEFORE any Google Cloud imports
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
import warnings
from pathlib import Path
from datetime import datetime

# Suppress specific warnings for cleaner console output
warnings.filterwarnings("ignore", category=UserWarning, module="vertexai.generative_models._generative_models")
warnings.filterwarnings("ignore", message=".*deprecated.*", category=UserWarning)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import logging
from src.agents.supervisor import SupervisorAgent
from src.utils.query_logger import initialize_logging, get_query_logger

# Configure logging to only show WARNING and above in console (no file logging)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
from src.ui.config import (
    APP_TITLE,
    APP_ICON,
    PAGE_TITLE,
    USER_AVATAR,
    BOT_AVATAR,
    WELCOME_MESSAGE,
    INPUT_PLACEHOLDER,
    SEND_BUTTON_TEXT,
    USER_MESSAGE_BG,
    BOT_MESSAGE_BG,
    ERROR_MESSAGE_BG,
    CLARIFICATION_BG,
    ERROR_GENERIC,
    ERROR_TIP,
    EXAMPLE_QUERIES,
    NAV_QUERIES,
)


# Page Configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=APP_ICON,
    layout="centered",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "supervisor" not in st.session_state:
        with st.spinner("Initializing AgenticBot..."):
            try:
                # Initialize logging system for this app run (archives old logs, creates new file)
                st.session_state.logger = initialize_logging("logs")
                st.session_state.supervisor = SupervisorAgent()
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"Failed to initialize: {e}")
                st.session_state.initialized = False
    
    # Initialize clarification tracking
    if "waiting_for_clarification" not in st.session_state:
        st.session_state.waiting_for_clarification = False
    
    if "clarification_key" not in st.session_state:
        st.session_state.clarification_key = None
    
    if "clarification_round" not in st.session_state:
        st.session_state.clarification_round = 0
    
    # Initialize query library tracking
    if "selected_query" not in st.session_state:
        st.session_state.selected_query = None
    
    if "execute_query" not in st.session_state:
        st.session_state.execute_query = False


def clean_pricing_response(content: str) -> str:
    """
    Clean and format pricing agent responses for better readability.
    Fixes the garbled tool calls formatting issue.
    
    Args:
        content: Raw pricing response content
        
    Returns:
        Cleaned and formatted content with readable tool call information
    """
    if not content or "Tool calls made:" not in content:
        return content
    
    try:
        # Split the response into main answer and tool section
        parts = content.split("Tool calls made:", 1)
        main_response = parts[0].strip()
        tool_section = parts[1].strip() if len(parts) > 1 else ""
        
        if not tool_section:
            return main_response
        
        # Remove any "How I got this information" section
        if "---" in tool_section:
            tool_section = tool_section.split("---")[0].strip()
        
        # Parse and format tool calls with better structure
        formatted_tools = []
        
        # Split by bullet points first
        bullet_parts = []
        if "•" in tool_section:
            bullet_parts = [part.strip() for part in tool_section.split("•") if part.strip()]
        
        # Process each tool call
        for i, part in enumerate(bullet_parts, 1):
            if not part or len(part) < 10:
                continue
            
            # Clean up the text - fix common formatting issues
            clean_part = ' '.join(part.split())  # Normalize whitespace
            clean_part = clean_part.replace("→", "➜")  # Better arrow symbol
            
            # Fix garbled text patterns
            clean_part = clean_part.replace("USDper", " USD per ")
            clean_part = clean_part.replace("Mcounts", "M counts")
            clean_part = clean_part.replace("inputtokensat", " input tokens at ")
            clean_part = clean_part.replace("calculatedcostfor", "calculated cost for ")
            clean_part = clean_part.replace("Calculatecosttool:", "Calculate cost tool: ")
            clean_part = clean_part.replace("invocations", " invocations")
            clean_part = clean_part.replace("invocationsat", " invocations at ")
            
            # Add icons based on content
            if "search" in clean_part.lower():
                icon = "🔍"
                label = "**Service Search**"
            elif "pricing" in clean_part.lower() and ("detail" in clean_part.lower() or "sku" in clean_part.lower()):
                icon = "💰"
                label = "**Pricing Details**"
            elif "retrieved" in clean_part.lower() or "options" in clean_part.lower():
                icon = "📋"
                label = "**SKU Retrieval**"
            elif "calculat" in clean_part.lower() or "cost" in clean_part.lower():
                icon = "🧮"
                label = "**Cost Calculation**"
            else:
                icon = "🔧"
                label = "**Tool Call**"
            
            # Format the tool call with clear structure
            formatted_tools.append(f"{icon} {label}: {clean_part}")
        
        # Reconstruct the response with better formatting
        if formatted_tools:
            tools_text = "\n\n".join(formatted_tools)  # Double line breaks for better spacing
            return f"{main_response}\n\n---\n\n**🔧 API Tool Execution Details:**\n\n{tools_text}"
        else:
            return main_response
            
    except Exception as e:
        # If parsing fails, return original content
        return content


def display_message(role: str, content: str, metadata: dict = None):
    """
    Display a chat message with appropriate styling.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content to display
        metadata: Optional metadata (for assistant messages)
    """
    if role == "user":
        avatar = USER_AVATAR
        bg_color = USER_MESSAGE_BG
    else:
        avatar = BOT_AVATAR
        bg_color = BOT_MESSAGE_BG
        
        # Check if it's an error or clarification
        if metadata and metadata.get("needs_clarification"):
            bg_color = CLARIFICATION_BG
        elif metadata and not metadata.get("success", True):
            bg_color = ERROR_MESSAGE_BG
    
    # Create message container with styling
    with st.container():
        col1, col2 = st.columns([0.1, 0.9])
        
        with col1:
            st.markdown(f"### {avatar}")
        
        with col2:
            # Add clarification badge if in clarification mode
            badge_html = ""
            if role == "assistant" and metadata and metadata.get("needs_clarification"):
                round_num = metadata.get("clarification_round", 1)
                max_rounds = metadata.get("max_rounds", 3)
                badge_html = f"""
                <div style="
                    display: inline-block;
                    background-color: #ff9800;
                    color: white;
                    padding: 3px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-bottom: 8px;
                ">
                    💬 Clarification Round {round_num}/{max_rounds}
                </div>
                <br>
                """
            
            # Clean pricing responses for better readability
            display_content = content
            if role == "assistant" and metadata and metadata.get("is_cost_query"):
                display_content = clean_pricing_response(content)
            
            # For pricing responses, use markdown rendering for better formatting
            if role == "assistant" and metadata and metadata.get("is_cost_query"):
                # Display badge if needed
                if badge_html:
                    st.markdown(badge_html, unsafe_allow_html=True)
                
                # Use markdown for pricing responses to handle formatting better
                with st.container():
                    st.markdown(
                        f"""<div style="
                            background-color: {bg_color};
                            padding: 15px;
                            border-radius: 10px;
                            margin-bottom: 10px;
                        "></div>""",
                        unsafe_allow_html=True
                    )
                    # Display the cleaned content as markdown for proper formatting
                    st.markdown(display_content)
            else:
                # Regular HTML rendering for non-pricing responses
                st.markdown(
                    f"""
                    {badge_html}
                    <div style="
                        background-color: {bg_color};
                        padding: 15px;
                        border-radius: 10px;
                        margin-bottom: 10px;
                    ">
                        {display_content}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Show results table for successful queries with data
            if role == "assistant" and metadata and metadata.get("success"):
                results_data = metadata.get("results_data", [])
                if results_data:
                    st.markdown("### 📊 Query Results")
                    import pandas as pd
                    df = pd.DataFrame(results_data)
                    st.dataframe(df, width='stretch', hide_index=True)
            
            # Show details expandable section for successful assistant messages
            if role == "assistant" and metadata and metadata.get("success"):
                with st.expander("▼ Show Details"):
                    # Handle cost queries vs SQL queries differently
                    if metadata.get("is_cost_query"):
                        # Cost Query details
                        st.markdown("**Query Type**")
                        st.write(f"GCP Pricing Analysis: {metadata.get('query_type', 'pricing_estimate')}")
                        
                        st.markdown("**Agent Used**")
                        st.write(f"🤖 {metadata.get('agent', 'gcp_pricing_agent')}")
                        
                        # Show pricing response metadata
                        cost_data = metadata.get("cost_data")
                        if cost_data:
                            st.markdown("**� Pricing Response Details**")
                            st.json(cost_data)
                    else:
                        # SQL Query details
                        # SQL Query - at the top, wrapped to avoid horizontal scrolling
                        st.markdown("**Generated SQL**")
                        sql = metadata.get("sql", "N/A")
                        st.code(sql, language="sql", wrap_lines=True)
                        
                        # Explanation - Detailed query logic
                        if metadata.get("explanation"):
                            st.markdown("**Explanation**")
                            explanation = metadata.get("explanation", "N/A")
                            st.write(explanation)
                        
                        # AI Reasoning - Step-by-step breakdown
                        if metadata.get("ai_reasoning"):
                            with st.expander("View AI Reasoning", expanded=False):
                                reasoning_steps = metadata.get("ai_reasoning", [])
                                for i, step in enumerate(reasoning_steps, 1):
                                    st.markdown(f"{i}. {step}")
                        
                        # Execution metrics without heading - smaller font size
                        st.markdown("""
                            <style>
                            [data-testid="stMetricValue"] {
                                font-size: 14px;
                            }
                            [data-testid="stMetricLabel"] {
                                font-size: 12px;
                            }
                            </style>
                        """, unsafe_allow_html=True)
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            exec_time = metadata.get("execution_time", "N/A")
                            st.metric("Execution Time", exec_time)
                        with col_b:
                            row_count = metadata.get("row_count", 0)
                            st.metric("Rows Returned", row_count)
                        with col_c:
                            bytes_proc = metadata.get("bytes_processed", "N/A")
                            st.metric("Data Processed", bytes_proc)
        
        st.markdown("<br>", unsafe_allow_html=True)


def process_query(user_query: str):
    """
    Process user query through Supervisor Agent.
    
    Args:
        user_query: Natural language query from user
    """
    # Use the session logger (initialized once per app run)
    logger = st.session_state.logger
    request_id = logger.start_request(user_query)
    
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": user_query
    })
    
    # Show user message
    display_message("user", user_query)
    
    # Process query with supervisor
    with st.spinner("Thinking..."):
        try:
            # Check if we're in clarification mode
            if st.session_state.waiting_for_clarification and st.session_state.clarification_key:
                # This is a response to a clarification question
                result = st.session_state.supervisor.handle_clarification_response(
                    st.session_state.clarification_key,
                    user_query
                )
            else:
                # Normal query processing
                result = st.session_state.supervisor.handle_query(user_query)
            
            # Note: Removed verbose orchestration and debug logging for cleaner output
            
            # Extract response
            response_text = result["response"]
            display_data = result.get("display_data", {})  # Complete display package from Response Agent
            
            # Check if this is a cost query or SQL query
            is_cost_query = "pricing_data" in display_data
            
            # Log the actual SQL that was generated (regardless of success/failure)
            sql_query = display_data.get("sql_query", "")
            if sql_query:
                logger.log_sql_generated(
                    request_id,
                    sql_query,
                    ["pcm_unit_master"],  # Default tables - could be parsed from SQL
                    1000,  # Default generation time
                    "MEDIUM"
                )
            
            if result["success"]:
                
                if is_cost_query:
                    # Log pricing query
                    logger.log_pricing_query(
                        request_id, 
                        user_query, 
                        display_data.get("agent", "GCP Pricing Agent"),
                        0.0,  # Will be extracted from pricing_data if available
                        0     # Processing time will be calculated from orchestration metrics
                    )
                    
                    # Cost query metadata
                    metadata = {
                        "success": True,
                        "is_cost_query": True,
                        "query_type": display_data.get("query_type"),
                        "agent": display_data.get("agent"),
                        "pricing_data": display_data.get("pricing_data"),
                        "sql": None,  # Cost queries don't have SQL
                        "results_data": []  # Cost data is handled differently
                    }
                else:
                    # SQL Query Success - Log execution results
                    results_data = display_data.get("results_data", [])
                    row_count = display_data.get("row_count", len(results_data) if results_data else 0)
                    execution_time = display_data.get("execution_time", "N/A")
                    
                    # Note: Removed verbose SQL execution logging for cleaner output
                    
                    # Log results captured with actual sample data
                    if results_data:
                        columns = list(results_data[0].keys()) if results_data else []
                        logger.log_results_captured(
                            request_id,
                            results_data[:3],  # First 3 rows for logging
                            columns,
                            ["STRING"] * len(columns),  # Default data types
                            len(str(results_data)) / 1024  # Rough size in KB
                        )
                    
                    # SQL query metadata
                    metadata = {
                        "success": True,
                        "is_cost_query": False,
                        "explanation": display_data.get("explanation"),
                        "ai_reasoning": display_data.get("ai_reasoning", []),
                        "sql": display_data.get("sql_query", "N/A"),
                        "execution_time": display_data.get("execution_time"),
                        "row_count": display_data.get("row_count"),
                        "bytes_processed": display_data.get("bytes_processed"),
                        "query_interpretation": display_data.get("query_interpretation"),
                        "confidence_score": display_data.get("confidence_score"),
                        "results_data": display_data.get("results_data", [])
                    }
                
                # Clear clarification state on success
                st.session_state.waiting_for_clarification = False
                st.session_state.clarification_key = None
                st.session_state.clarification_round = 0
                
            else:
                # Handle clarification or error - log the failure
                error_msg = result.get("error_message", response_text if response_text else "Unknown error")
                
                if sql_query and not result["success"]:
                    # This is likely a SQL execution error
                    logger.log_sql_error(
                        request_id,
                        sql_query,
                        error_msg,
                        "SQL_EXECUTION_ERROR"
                    )
                
                # Note: Error logging removed - errors are captured in main log through log_sql_error method
                
                metadata = {
                    "success": False,
                    "needs_clarification": result["metadata"].get("needs_clarification", False)
                }
                
                # Update clarification state
                if result["metadata"].get("needs_clarification"):
                    st.session_state.waiting_for_clarification = True
                    st.session_state.clarification_key = result["metadata"].get("clarification_key")
                    st.session_state.clarification_round = result["metadata"].get("clarification_round", 1)
                    metadata["clarification_round"] = st.session_state.clarification_round
                    metadata["max_rounds"] = result["metadata"].get("max_rounds", 3)
                else:
                    # Error or max rounds reached - clear clarification state
                    st.session_state.waiting_for_clarification = False
                    st.session_state.clarification_key = None
                    st.session_state.clarification_round = 0
            
            # Add assistant message to chat
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "metadata": metadata
            })
            
            # Display assistant message
            display_message("assistant", response_text, metadata)
            
            # Log the final response from the bot (always capture this)
            logger._write_to_file(logger.main_log_file, f"""
{logger._format_timestamp()} [INFO] [RESPONSE] [RESPONSE_AGENT] - Bot response generated
    ↳ Request ID: {request_id}
    ↳ Success: {result["success"]}
    ↳ Response Length: {len(response_text)} characters
    ↳ Query Type: {"Pricing Query" if is_cost_query else "SQL Query"}
    ↳ Bot Response Content:
    
    "{response_text[:800]}{'...' if len(response_text) > 800 else ''}"
    
    ↳ Additional Context:
        • SQL Query: {"Yes" if sql_query else "No"}  
        • Results Returned: {display_data.get("row_count", "N/A")} rows
        • Execution Time: {display_data.get("execution_time", "N/A")}
""")
            
            # Log request completion with actual metrics
            orchestration_metrics = result.get("orchestration_metrics", {})
            iterations = orchestration_metrics.get("iterations", 0)
            
            # Extract timing information from display_data if available
            execution_time_str = display_data.get("execution_time", "0ms")
            sql_execution_time = int(execution_time_str.replace("ms", "")) if "ms" in str(execution_time_str) else 0
            
            logger.log_request_complete(
                request_id,
                15000 + sql_execution_time,  # Estimated total time including SQL execution
                {
                    "orchestration": 6000,
                    "planning": 4000,
                    "sql_generation": 2000,
                    "sql_execution": sql_execution_time,
                    "response_formatting": 3000
                },
                0.001,  # Estimated cost
                "SUCCESS" if result["success"] else "FAILED"
            )
            
        except Exception as e:
            error_message = f"{ERROR_GENERIC}\n\n**Error:** {str(e)}\n\n{ERROR_TIP}"
            
            # Note: Exception logging removed - using main log only
            
            # Clear clarification state on error
            st.session_state.waiting_for_clarification = False
            st.session_state.clarification_key = None
            st.session_state.clarification_round = 0
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_message,
                "metadata": {"success": False}
            })
            
            display_message("assistant", error_message, {"success": False})


def render_query_library():
    """Render the Query Library sidebar with all available queries."""
    with st.sidebar:
        st.title("🔍 Query Library")
        st.markdown("Click any query to execute it instantly")
        st.markdown("---")
        
        # Combine Simple queries with NAV_QUERIES
        all_queries = {
            "Simple": EXAMPLE_QUERIES,
            **NAV_QUERIES
        }
        
        # Render each category as expandable section
        for category, queries in all_queries.items():
            with st.expander(f"📁 {category}", expanded=False):
                for query in queries:
                    # Create unique key for each button
                    button_key = f"query_{hash(query)}_{category}"
                    
                    if st.button(
                        query,
                        key=button_key,
                        width='stretch',
                        help=f"Execute: {query[:50]}..."
                    ):
                        # Set query for execution
                        st.session_state.selected_query = query
                        st.session_state.execute_query = True
                        st.rerun()


def main():
    """Main application entry point."""
    
    # Initialize session state
    initialize_session_state()
    
    # Render Query Library sidebar
    render_query_library()
    
    # App title
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Check if initialization was successful
    if not st.session_state.get("initialized", False):
        st.error("Failed to initialize the application. Please check your configuration.")
        return
    
    # Process query from Query Library if selected
    if st.session_state.execute_query and st.session_state.selected_query:
        process_query(st.session_state.selected_query)
        st.session_state.execute_query = False
        st.session_state.selected_query = None
        st.rerun()
    
    # Display welcome message if no messages yet
    if len(st.session_state.messages) == 0:
        st.markdown(WELCOME_MESSAGE)
        st.info("👈 Use the **Query Library** in the sidebar to explore sample queries, or type your own question below.")
    
    # Display chat history
    for message in st.session_state.messages:
        display_message(
            message["role"],
            message["content"],
            message.get("metadata")
        )
    
    # Chat input at bottom
    st.markdown("---")
    
    # Create input form with compact button below, right-aligned
    with st.form(key="query_form", clear_on_submit=True):
        user_input = st.text_area(
            label="query_input",
            placeholder=INPUT_PLACEHOLDER,
            height=100,
            label_visibility="collapsed"
        )
        
        # Send button - small and right-aligned
        col1, col2 = st.columns([0.9, 0.1])
        with col2:
            submit_button = st.form_submit_button(
                label="➤",
                width='stretch',
                type="primary"
            )
        
        if submit_button and user_input.strip():
            process_query(user_input.strip())
            st.rerun()


if __name__ == "__main__":
    main()
