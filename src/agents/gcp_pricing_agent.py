"""
GCP Pricing Agent using Vertex AI Function Calling
Single agent that answers questions about GCP service pricing.
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    FunctionDeclaration,
    Tool,
    Content,
    Part,
)

from .tools.gcp_pricing_tools import GCPPricingTools


@dataclass
class PricingResponse:
    """Data class for pricing query response - matches supervisor expectations"""
    success: bool
    data: Dict[str, Any]
    formatted_response: str
    metadata: Dict[str, Any]
    error_message: Optional[str] = None


class GCPPricingAgent:
    """
    GCP Pricing Agent with function calling capabilities
    Uses Vertex AI Gemini with tools to answer pricing questions
    """
    
    # Path to external prompt template
    PROMPT_FILE = Path(__file__).parent.parent.parent / "prompt" / "gcp_pricing_agent_prompt.txt"
    
    def __init__(self, project_id: str = None, location: str = None, model_name: str = None):
        """
        Initialize GCP Pricing Agent
        
        Args:
            project_id: GCP project ID (from env if not provided)
            location: Vertex AI location (from env if not provided)
            model_name: Gemini model name (from env if not provided)
        """
        load_dotenv()
        
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.location = location or os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        self.model_name = model_name or os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash-lite')
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        
        # Initialize pricing tools
        self.tools_instance = GCPPricingTools()
        
        # Define function declarations for Gemini
        self.function_declarations = self._create_function_declarations()
        
        # Create tool from function declarations
        self.pricing_tool = Tool(function_declarations=self.function_declarations)
        
        # Validate and cache prompt template
        self._validate_prompt_file()
        self._prompt_template = self._load_prompt_template()
        
        # Initialize model with tools
        self.model = GenerativeModel(
            self.model_name,
            tools=[self.pricing_tool],
            system_instruction=self._prompt_template
        )
        
        # Initialize chat
        self.chat = None
    
    def _create_function_declarations(self) -> List[FunctionDeclaration]:
        """Create function declarations for Gemini tool calling"""
        
        search_service_func = FunctionDeclaration(
            name="search_gcp_service",
            description="Search for a GCP service by name and return the service ID. Use this when the user mentions a service like 'Compute Engine', 'Gemini', 'BigQuery', etc.",
            parameters={
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "The name of the GCP service to search for (e.g., 'Compute Engine', 'Gemini API', 'Cloud Storage')"
                    }
                },
                "required": ["service_name"]
            }
        )
        
        get_skus_func = FunctionDeclaration(
            name="get_service_skus",
            description="Get all SKUs (Stock Keeping Units) for a GCP service. SKUs represent specific billable items like 'n1-standard-1 VM' or 'input tokens'. Use this after finding the service ID to get pricing details.",
            parameters={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "The service ID obtained from search_gcp_service"
                    },
                    "filter_text": {
                        "type": "string",
                        "description": "Optional filter text to narrow down SKUs (e.g., 'gemini-2.5-flash-lite', 'n1-standard', 'input token')"
                    }
                },
                "required": ["service_id"]
            }
        )
        
        get_pricing_func = FunctionDeclaration(
            name="get_sku_pricing",
            description="Get detailed pricing information for a specific SKU including price, currency, and unit. Use this to get the actual dollar amount for a SKU.",
            parameters={
                "type": "object",
                "properties": {
                    "sku_id": {
                        "type": "string",
                        "description": "The SKU ID obtained from get_service_skus"
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code (e.g., 'USD', 'EUR'). Default is USD.",
                        "default": "USD"
                    }
                },
                "required": ["sku_id"]
            }
        )
        
        calculate_cost_func = FunctionDeclaration(
            name="calculate_cost",
            description="MANDATORY: Calculate total cost based on usage quantities and SKU pricing. You MUST call this for ANY quantity-based pricing question (like '2 million tokens', '1000 images', '10 hours'). NEVER do manual calculations. Pass individual parameters instead of complex objects.",
            parameters={
                "type": "object",
                "properties": {
                    "sku_id": {
                        "type": "string",
                        "description": "The SKU ID to calculate cost for"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "The usage quantity (e.g., 1000000 for 1M tokens)"
                    },
                    "price_per_unit": {
                        "type": "number",
                        "description": "The price per unit from get_sku_pricing (e.g., 0.5 for $0.50)"
                    },
                    "unit_quantity": {
                        "type": "number",
                        "description": "The unit quantity from get_sku_pricing (e.g., 1000000 for 'per 1M')"
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code (e.g., 'USD')",
                        "default": "USD"
                    }
                },
                "required": ["sku_id", "quantity", "price_per_unit", "unit_quantity"]
            }
        )
        
        return [search_service_func, get_skus_func, get_pricing_func, calculate_cost_func]
    
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
        Load the system instruction prompt template from file.
        Called once at initialization and cached in memory.
        
        Returns:
            Prompt template string
        """
        try:
            return self.PROMPT_FILE.read_text()
        except Exception as e:
            raise RuntimeError(f"Failed to load prompt template: {e}")
    
    def _get_system_instruction(self) -> str:
        """Get system instruction for the agent (legacy method - now loads from external file)"""
        return self._prompt_template
    
    def _execute_function(self, function_call) -> Dict[str, Any]:
        """
        Execute a function call from Gemini
        
        Args:
            function_call: Function call object from Gemini
            
        Returns:
            Function execution result
        """
        function_name = function_call.name
        args = dict(function_call.args)
        
        print(f"🔧 Calling function: {function_name}")
        print(f"   Args: {args}")
        
        try:
            if function_name == "search_gcp_service":
                result = self.tools_instance.search_gcp_service(**args)
            elif function_name == "get_service_skus":
                result = self.tools_instance.get_service_skus(**args)
            elif function_name == "get_sku_pricing":
                result = self.tools_instance.get_sku_pricing(**args)
            elif function_name == "calculate_cost":
                result = self.tools_instance.calculate_cost(**args)
            else:
                result = {"error": f"Unknown function: {function_name}"}
            
            print(f"✅ Result: {json.dumps(result, indent=2)[:200]}...\n")
            return result
            
        except Exception as e:
            error_result = {"error": str(e)}
            print(f"❌ Error: {error_result}\n")
            return error_result
    
    def start_chat(self):
        """Start a new chat session"""
        self.chat = self.model.start_chat(response_validation=False)
        return self
    
    def handle_pricing_query(self, user_query: str) -> PricingResponse:
        """
        Supervisor-compatible interface for pricing queries
        
        Args:
            user_query: Natural language pricing question
            
        Returns:
            PricingResponse with formatted response ready for user
        """
        try:
            if not self.chat:
                self.start_chat()
                
            # Get pricing response with tool transparency
            response_text = self.send_message(user_query, verbose=False, include_summary=True)
            
            return PricingResponse(
                success=True,
                data={"pricing_response": response_text},
                formatted_response=response_text,
                metadata={
                    "query_type": "pricing_estimate",
                    "agent": "gcp_pricing_agent",
                    "tools_used": True
                },
                error_message=None
            )
            
        except Exception as e:
            return PricingResponse(
                success=False,
                data={},
                formatted_response=f"I apologize, but I encountered an error processing your pricing query: {str(e)}",
                metadata={
                    "query_type": "pricing_estimate", 
                    "agent": "gcp_pricing_agent",
                    "error": str(e)
                },
                error_message=str(e)
            )
    
    def send_message(self, message: str, verbose: bool = True, include_summary: bool = False) -> str:
        """
        Send a message to the agent and get response
        
        Args:
            message: User message
            verbose: Whether to print function calls
            include_summary: Whether to include a summary of function calls in response
            
        Returns:
            Agent's response text
        """
        if not self.chat:
            self.start_chat()
        
        if verbose:
            print(f"\n👤 User: {message}\n")
        
        # Track function calls for summary
        function_calls_summary = []
        
        # Send initial message
        response = self.chat.send_message(message)
        
        # Handle function calling loop
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            # Check if model wants to call a function
            if not response.candidates:
                break
            
            parts = response.candidates[0].content.parts
            if not parts or not any(part.function_call for part in parts):
                # No more function calls, we have final response
                break
            
            # Execute all function calls in this turn
            function_responses = []
            for part in parts:
                if part.function_call:
                    function_call = part.function_call
                    result = self._execute_function(function_call)
                    
                    # Track function call for summary
                    function_calls_summary.append({
                        'function': function_call.name,
                        'args': dict(function_call.args),
                        'result': result
                    })
                    
                    function_responses.append(
                        Part.from_function_response(
                            name=function_call.name,
                            response={"result": result}
                        )
                    )
            
            # Send all function responses back to model
            response = self.chat.send_message(function_responses)
            
            iteration += 1
        
        # Get final text response
        final_response = response.text if response.candidates else "I apologize, but I couldn't generate a response."
        
        # Add summary if requested
        if include_summary and function_calls_summary:
            summary = self._create_function_calls_summary(function_calls_summary)
            final_response += f"\n\n---\n**How I got this information:**\n{summary}"
        
        if verbose:
            print(f"🤖 Agent: {final_response}\n")
        
        return final_response
    
    def _create_function_calls_summary(self, function_calls: List[Dict]) -> str:
        """Create a summary of function calls made during the response"""
        summary_parts = []
        
        for i, call in enumerate(function_calls, 1):
            func_name = call['function']
            args = call['args']
            result = call['result']
            
            if func_name == 'search_gcp_service':
                service_name = args.get('service_name', 'unknown')
                if result.get('found'):
                    source = result.get('source', 'api')
                    source_desc = "service_mappings.json cache" if source == "cache" else "GCP API"
                    summary_parts.append(f"{i}. **Searched for service**: '{service_name}' → Found service ID `{result['service_id']}` ({result['display_name']}) from {source_desc}")
                else:
                    summary_parts.append(f"{i}. **Searched for service**: '{service_name}' → Not found")
            
            elif func_name == 'get_service_skus':
                service_id = args.get('service_id', 'unknown')
                filter_text = args.get('filter_text', 'none')
                if isinstance(result, list) and result:
                    sku_count = len([sku for sku in result if 'error' not in sku])
                    summary_parts.append(f"{i}. **Retrieved SKUs**: For service `{service_id}` with filter '{filter_text}' → Found {sku_count} pricing items")
                else:
                    summary_parts.append(f"{i}. **Retrieved SKUs**: For service `{service_id}` → No SKUs found")
            
            elif func_name == 'get_sku_pricing':
                sku_id = args.get('sku_id', 'unknown')
                if 'error' not in result:
                    price = result.get('price', 0)
                    currency = result.get('currency', 'USD')
                    unit = result.get('unit', 'unknown unit')
                    # Try to find the SKU description from previous get_service_skus calls
                    sku_description = "pricing details"
                    summary_parts.append(f"{i}. **Got pricing**: ${price} {currency} {unit} for {sku_description}")
                else:
                    summary_parts.append(f"{i}. **Got pricing**: SKU `{sku_id}` → Error: {result['error']}")
            
            elif func_name == 'calculate_cost':
                if 'error' not in result:
                    total_cost = result.get('total_cost', 0)
                    currency = result.get('currency', 'USD')
                    breakdown_count = len(result.get('breakdown', []))
                    summary_parts.append(f"{i}. **Calculated cost**: Total ${total_cost} {currency} based on {breakdown_count} pricing components")
                else:
                    summary_parts.append(f"{i}. **Calculated cost**: Error: {result['error']}")
        
        return '\n'.join(summary_parts)
    
    def run_interactive(self):
        """Run interactive chat loop"""
        print("\n" + "="*60)
        print("GCP Pricing Agent - Interactive Mode")
        print("="*60)
        print("Ask me anything about GCP service pricing!")
        print("Type 'exit' or 'quit' to end the conversation.\n")
        
        self.start_chat()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\n👋 Goodbye! Thanks for using GCP Pricing Agent.\n")
                    break
                
                self.send_message(user_input, verbose=True)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point for running the agent"""
    agent = GCPPricingAgent()
    agent.run_interactive()


if __name__ == "__main__":
    main()
