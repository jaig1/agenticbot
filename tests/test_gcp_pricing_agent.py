"""
Test suite for GCP Pricing Agent
Tests the agent's ability to answer various pricing questions and perform function calls.
"""

import pytest
import os
import sys
import time
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.gcp_pricing_agent import GCPPricingAgent


class TestGCPPricingAgent:
    """Test cases for GCP Pricing Agent"""
    
    @pytest.fixture(scope="class")
    def agent(self):
        """Create a GCP Pricing Agent instance for testing"""
        try:
            agent = GCPPricingAgent()
            agent.start_chat()
            return agent
        except Exception as e:
            pytest.skip(f"Could not initialize GCP Pricing Agent: {e}")
    
    def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly"""
        assert agent is not None
        assert agent.project_id is not None
        assert agent.location is not None
        assert agent.model_name is not None
        assert agent.tools_instance is not None
        assert hasattr(agent.tools_instance, 'use_adc')
        print(f"✅ Agent initialized with project: {agent.project_id}")
    
    def test_tools_authentication(self, agent):
        """Test that tools are using proper authentication"""
        assert agent.tools_instance.use_adc == True, "Should be using Application Default Credentials"
        print("✅ Tools configured to use ADC")
    
    def test_service_search_functionality(self, agent):
        """Test the service search functionality directly"""
        # Test searching for a known service
        result = agent.tools_instance.search_gcp_service("Vertex AI")
        assert isinstance(result, dict)
        assert "found" in result
        print(f"✅ Service search result: {result}")
    
    @pytest.mark.parametrize("question,expected_cost", [
        (
            "How much does 3 million Gemini input tokens cost?",
            1.50
        ),
        (
            "What is the cost for 1000 Cloud Functions invocations?",
            0.00
        ),
        (
            "What is the cost for processing 10 million Gemini input tokens?",
            5.00
        ),
        (
            "How much do 10000 Cloud Functions invocations cost?",
            0.00
        ),
        (
            "How much does 5 million Gemini input tokens cost?",
            2.50
        )
    ])
    def test_pricing_questions(self, agent, question, expected_cost):
        """Test the 5 verified working pricing questions"""
        print(f"\n🤖 Testing question: {question}")
        print(f"   💰 Expected cost: ${expected_cost}")
        
        try:
            # Send message with summary enabled to get tool transparency
            response = agent.send_message(question, verbose=False, include_summary=True)
            
            # Basic response validation
            assert response is not None, "Response should not be None"
            assert isinstance(response, str), "Response should be a string"
            assert len(response) > 50, "Response should be substantial"
            
            print(f"   📝 Response length: {len(response)} characters")
            
            # Check for cost in response
            response_lower = response.lower()
            cost_mentioned = f"${expected_cost}" in response or f"${expected_cost:.2f}" in response
            
            if expected_cost == 0.00:
                # For free tier, check for "$0" or "free" 
                cost_mentioned = "$0" in response or "free" in response_lower
            
            print(f"   � Cost mentioned correctly: {cost_mentioned}")
            
            # Check for tool transparency indicators
            has_tool_calls = "tool calls made:" in response_lower or "how i got this information:" in response_lower
            print(f"   � Has tool transparency: {has_tool_calls}")
            
            # Check for key pricing workflow indicators
            has_search = "search" in response_lower and "service" in response_lower
            has_pricing = "pricing" in response_lower or "cost" in response_lower
            has_calculation = "calculat" in response_lower or "total" in response_lower
            
            print(f"   🔍 Has search workflow: {has_search}")
            print(f"   💲 Has pricing info: {has_pricing}")
            print(f"   🧮 Has calculation: {has_calculation}")
            print(f"   💬 Response preview: {response[:150]}...")
            
            # Core assertions
            assert cost_mentioned, f"Response should mention the expected cost ${expected_cost}"
            assert has_tool_calls, "Response should include tool call transparency"
            assert has_pricing, "Response should contain pricing information"
            
        except Exception as e:
            pytest.fail(f"Question failed: {question}. Error: {e}")
    
    def test_function_calling_workflow(self, agent):
        """Test that the agent properly uses function calling"""
        # This test checks if the agent makes function calls for a pricing query
        question = "How much does 5 million Gemini input tokens cost?"
        
        # Capture the original function to monitor calls
        original_execute = agent._execute_function
        function_calls_made = []
        
        def mock_execute(function_call):
            function_calls_made.append(function_call.name)
            return original_execute(function_call)
        
        agent._execute_function = mock_execute
        
        try:
            response = agent.send_message(question, verbose=False)
            
            # Verify function calls were made
            assert len(function_calls_made) > 0, "Agent should make function calls for pricing queries"
            print(f"✅ Function calls made: {function_calls_made}")
            
            # All 4 function calls we expect for complete workflow
            expected_functions = ['search_gcp_service', 'get_service_skus', 'get_sku_pricing', 'calculate_cost']
            found_functions = [f for f in expected_functions if f in function_calls_made]
            
            assert len(found_functions) >= 3, f"Should call at least 3 pricing functions from {expected_functions}"
            print(f"✅ Expected functions found: {found_functions}")
            
            # For the working questions, we should get all 4 functions
            if len(found_functions) == 4:
                print("🎉 Complete 4-tool workflow achieved!")
            
        finally:
            # Restore original function
            agent._execute_function = original_execute
    
    def test_error_handling(self, agent):
        """Test how the agent handles invalid requests"""
        # Test with a non-existent service
        response = agent.send_message("What is the pricing for NonExistentService?", verbose=False)
        
        assert response is not None
        assert isinstance(response, str)
        # Should handle gracefully, not crash
        print(f"✅ Error handling response: {response[:100]}...")
    
    def test_cost_calculation_request(self, agent):
        """Test requests that require cost calculation"""
        question = "If I use 100,000 API calls per month, what would be the estimated cost?"
        
        response = agent.send_message(question, verbose=False)
        
        assert response is not None
        assert isinstance(response, str)
        
        # Should mention that specific service info is needed
        response_lower = response.lower()
        assert any(word in response_lower for word in ['service', 'specific', 'which', 'what']), \
            "Should ask for more specific service information"
        
        print(f"✅ Cost calculation handling: {response[:100]}...")
    
    def test_response_quality(self, agent):
        """Test the quality and helpfulness of responses"""
        question = "I need to understand GCP pricing for a new project"
        
        response = agent.send_message(question, verbose=False)
        
        assert response is not None
        assert len(response) > 50, "Response should be detailed enough"
        
        # Should be helpful and ask for specifics
        response_lower = response.lower()
        helpful_indicators = ['help', 'specific', 'service', 'tell me', 'which', 'what']
        
        assert any(indicator in response_lower for indicator in helpful_indicators), \
            "Response should be helpful and ask for specifics"
        
        print(f"✅ Quality response: {response[:100]}...")


def run_manual_test():
    """Manual test function that can be run directly"""
    print("🧪 Running manual GCP Pricing Agent test...")
    
    try:
        agent = GCPPricingAgent()
        agent.start_chat()
        print("✅ Agent initialized successfully")
        
        # Test one of the verified working questions manually
        question = "How much does 3 million Gemini input tokens cost?"
        print(f"\n🤖 Testing: {question}")
        
        response = agent.send_message(question, verbose=True, include_summary=True)
        print(f"\n📝 Response received: {len(response)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Manual test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run manual test when script is executed directly
    success = run_manual_test()
    if success:
        print("\n✅ Manual test completed successfully!")
        print("\nTo run full test suite:")
        print("pytest tests/test_gcp_pricing_agent.py -v")
    else:
        print("\n❌ Manual test failed!")
        sys.exit(1)
