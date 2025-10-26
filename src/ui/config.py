"""
UI Configuration - Streamlit App Settings

Contains configuration for the Streamlit Text2SQL interface including
example queries, app settings, and UI constants.
"""

# App Configuration
APP_TITLE = "AgenticBot"
APP_ICON = "✨"
PAGE_TITLE = "AgenticBot - Data Insight Assistant"

# Chat Configuration
MAX_CHAT_WIDTH = 800  # pixels
USER_AVATAR = "👤"
BOT_AVATAR = "✨"

# Example Queries
EXAMPLE_QUERIES = [
    "How many vehicles do we have in the master table?",
    "Show me vehicles updated in the last 30 days",
    "What's the average model year of our vehicles?",
    "Which plants have the most vehicle production?",
    "Find 2025 vehicles from plants 31 and 44",
]

# Comprehensive NAV Queries - From comprehensive testing (40 questions)
NAV_QUERIES = {
    "Vehicle Inventory & Status": [
        "Generate a list of vehicles (vin) that are still in the plant inventory with their associated status information",
        "Show me all vehicles with missing collection points",
        "Show me vehicles by plant location and status",
    ],
    
    "Quality Control & Defects": [
        "Get all quality concerns / defects filed on the vehicle (vin) as well as the repairs done on it",
        "What quality concerns are unresolved for vehicles?",
    ],
    
    "Campaign Management": [
        "Get the campaigns that the vehicle has been put on and the associated details",
        "Show me campaign management reporting for tracked vehicles",
    ],
    
    "Connected Vehicle Data": [
        "Get connected vehicle (cv) details for individual vins",
        "Show me connected vehicle service scheduling data",
        "Get OTA update status for vehicles",
        "Display connected vehicle telematics information",
    ],
    
    "Diagnostics & Maintenance": [
        "Get diagnostic trouble codes for vehicles",
        "Show me maintenance service requirements for the fleet",
        "List diagnostic scan results for vehicles in inventory",
        "Show me vehicle health monitoring data",
    ],
    
    "Simple Queries": [
        "Count total vehicles",
        "List unique vehicle models",
        "Show all assembly plants",
        "Count vehicles by status",
    ],
    
    "Complex Queries": [
        "Show vehicles with multiple quality concerns",
        "List vehicles with OTA updates and missing collection points",
        "Find vehicles with freight data but no shipping date",
        "Show vehicles with connected features and campaign assignments",
    ],
    
    "Analytical Queries": [
        "Calculate average time from production to shipping by plant",
        "Show monthly vehicle production trends",
        "Analyze defect rates by model and plant",
    ],
    
    "Basic Filtering": [
        "List all vehicle models",
    ],
    
    "Medium Complexity": [
        "Show vehicle count by plant and model",
        "List vehicles with their plant information and status",
        "Count vehicles by production year and shipping status",
    ],
    
    "Advanced Analytics": [
        "Analyze production efficiency by plant with defect correlation",
        "Show comprehensive vehicle lifecycle from production to delivery",
        "Generate quality metrics report with campaign impact analysis",
    ],
    
    "GCP Pricing": [
        "How much does 3 million Gemini input tokens cost?",
        "What is the cost for 1000 Cloud Functions invocations?",
        "What is the cost for processing 10 million Gemini input tokens?",
        "How much do 10000 Cloud Functions invocations cost?",
        "How much does 5 million Gemini input tokens cost?",
    ],
}

# UI Text
WELCOME_MESSAGE = """
👋 **Welcome to AgenticBot!**

I can help you explore your automotive manufacturing data using natural language. 
Ask me anything about vehicles, plants, campaigns, or production insights.
"""

INPUT_PLACEHOLDER = "Ask your question here..."
SEND_BUTTON_TEXT = "Send"
EXAMPLE_DROPDOWN_LABEL = "💡 Try an example question"

# Error Messages
ERROR_GENERIC = "⚠️ Something went wrong while processing your query."
ERROR_TIP = "💡 Try rephrasing your question or using simpler terms."

# Available Tables Info (for error messages)
AVAILABLE_TABLES = [
    "Unit Master (vehicle records)",
    "Campaign Detail (quality campaigns)",
    "Plant Unit Location (vehicle locations)",
    "Connected Vehicle Detail (telematics data)",
    "Assembly Plant Code (plant information)",
]

# Styling
USER_MESSAGE_BG = "#E3F2FD"  # Light blue
BOT_MESSAGE_BG = "#F5F5F5"   # Light gray
ERROR_MESSAGE_BG = "#FFE5E5"  # Light red
CLARIFICATION_BG = "#FFF9E5"  # Light yellow
