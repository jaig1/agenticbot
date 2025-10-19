"""
Streamlit Text2SQL Interface - Iteration 1: Basic Chat

A web interface for the AgenticBot Text2SQL system using Streamlit.
Provides a chat-based interface for querying BigQuery using natural language.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from src.agents.supervisor import SupervisorAgent
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
)


# Page Configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=APP_ICON,
    layout="centered",
    initial_sidebar_state="collapsed"
)


def initialize_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "supervisor" not in st.session_state:
        with st.spinner("Initializing AgenticBot..."):
            try:
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
            
            # Custom styling for message box
            st.markdown(
                f"""
                {badge_html}
                <div style="
                    background-color: {bg_color};
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                ">
                    {content}
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
                    st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show details expandable section for successful assistant messages
            if role == "assistant" and metadata and metadata.get("success"):
                with st.expander("▼ Show Details"):
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
            
            # Extract response
            if result["success"]:
                response_text = result["response"]
                display_data = result["display_data"]  # Complete display package from Response Agent
                
                metadata = {
                    "success": True,
                    "explanation": display_data.get("explanation"),
                    "ai_reasoning": display_data.get("ai_reasoning", []),
                    "sql": display_data["sql_query"],
                    "execution_time": display_data["execution_time"],
                    "row_count": display_data["row_count"],
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
                # Handle clarification or error
                response_text = result["response"]
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
            
        except Exception as e:
            error_message = f"{ERROR_GENERIC}\n\n**Error:** {str(e)}\n\n{ERROR_TIP}"
            
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


def main():
    """Main application entry point."""
    
    # Initialize session state
    initialize_session_state()
    
    # App title
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Check if initialization was successful
    if not st.session_state.get("initialized", False):
        st.error("Failed to initialize the application. Please check your configuration.")
        return
    
    # Initialize tracking variables for example dropdown
    if "process_example" not in st.session_state:
        st.session_state.process_example = False
    if "example_to_process" not in st.session_state:
        st.session_state.example_to_process = None
    if "example_dropdown_key" not in st.session_state:
        st.session_state.example_dropdown_key = 0  # Counter to force widget recreation
    
    # Process the example query if flagged (do this BEFORE creating the widget)
    if st.session_state.process_example and st.session_state.example_to_process:
        process_query(st.session_state.example_to_process)
        st.session_state.process_example = False
        st.session_state.example_to_process = None
        # Increment key to force widget recreation with default value
        st.session_state.example_dropdown_key += 1
        st.rerun()
    
    # Display welcome message and example dropdown if no messages yet
    if len(st.session_state.messages) == 0:
        st.markdown(WELCOME_MESSAGE)
        
        # Example queries dropdown - static position below welcome message
        example_options = ["Select an example query..."] + EXAMPLE_QUERIES
        
        selected = st.selectbox(
            label="Choose an example to run instantly:",
            options=example_options,
            index=0,  # Always default to first option
            key=f"example_selector_{st.session_state.example_dropdown_key}",  # Unique key forces reset
            label_visibility="collapsed"
        )
        
        # Detect when user selects a new example
        if selected != "Select an example query...":
            # Mark for processing on next rerun
            st.session_state.example_to_process = selected
            st.session_state.process_example = True
            st.rerun()
    
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
                use_container_width=True,
                type="primary"
            )
        
        if submit_button and user_input.strip():
            process_query(user_input.strip())
            st.rerun()


if __name__ == "__main__":
    main()
