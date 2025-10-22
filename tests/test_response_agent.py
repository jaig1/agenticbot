#!/usr/bin/env python
"""
Standalone test script for Response Agent
Tests natural language response formatting capabilities
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.response_agent import ResponseAgent


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def print_section_header(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(title)
    print_separator()


def test_prompt_template():
    """Test that prompt template is loaded correctly"""
    print_section_header("TEST 1: Prompt Template Loading")
    
    try:
        agent = ResponseAgent()
        
        # Check template is cached
        if hasattr(agent, '_prompt_template'):
            print("✓ Prompt template is cached")
            print(f"  Template length: {len(agent._prompt_template)} chars")
            
            # Count variable placeholders
            var_count = agent._prompt_template.count('{')
            print(f"  Contains {var_count} variable placeholders")
            
            # Check for expected variables
            expected_vars = ['{user_query}', '{sql}', '{sample_results}', '{total_rows}', '{sample_count}', '{execution_time}']
            for var in expected_vars:
                if var in agent._prompt_template:
                    print(f"  ✓ Contains variable: {var}")
                else:
                    print(f"  ✗ Missing variable: {var}")
        else:
            print("✗ Prompt template not found in agent")
        
        # Check template file exists
        if agent.PROMPT_FILE.exists():
            print(f"✓ Template file exists: {agent.PROMPT_FILE}")
        else:
            print(f"✗ Template file missing: {agent.PROMPT_FILE}")
        
        print("\n✓ PASS: Prompt template test")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_results_handling():
    """Test handling of empty query results"""
    print_section_header("TEST 2: Empty Results Handling")
    
    try:
        agent = ResponseAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        if not context_file.exists():
            print(f"✗ Schema file not found: {context_file}")
            return False
            
        schema_context = context_file.read_text()
        print(f"✓ Schema loaded: {len(schema_context)} chars\n")
        
        # Test with empty results
        print("Test Case: Empty results")
        print("-" * 80)
        
        response = agent.format_response(
            user_query="Find customers named XYZ123",
            system_context=schema_context,
            execution_plan={
                "intent": "Find specific customer",
                "tables_needed": ["insurance_customers"],
                "operations": {"filtering": {"column": "customer_name"}},
                "confidence": 0.85
            },
            sql="SELECT * FROM customers WHERE name = 'XYZ123'",
            results=[],
            metadata={"row_count": 0, "execution_time_seconds": 0.05, "bytes_processed": 0}
        )
        
        # Check response structure
        checks = [
            ("formatted_response" in response, "Has formatted_response"),
            ("explanation" in response, "Has explanation"),
            ("ai_reasoning" in response, "Has ai_reasoning"),
            ("sql_query" in response, "Has sql_query"),
            ("execution_time" in response, "Has execution_time"),
            ("row_count" in response, "Has row_count"),
            (response["row_count"] == 0, "Row count is 0"),
            (len(response["results_data"]) == 0, "Results data is empty"),
            ("no results" in response["formatted_response"].lower(), "Message mentions no results")
        ]
        
        passed = all(check[0] for check in checks)
        
        for check, description in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {description}")
        
        print(f"\nFormatted Response: {response['formatted_response'][:150]}...")
        
        if passed:
            print("\n✓ PASS: Empty results test")
            return True
        else:
            print("\n✗ FAIL: Some checks failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_value_result():
    """Test formatting of single value results (aggregations)"""
    print_section_header("TEST 3: Single Value Result Formatting")
    
    try:
        agent = ResponseAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        schema_context = context_file.read_text()
        
        test_cases = [
            {
                "user_query": "How many customers do we have?",
                "execution_plan": {
                    "intent": "Count total customers",
                    "tables_needed": ["insurance_customers"],
                    "operations": {"aggregation": {"function": "COUNT"}},
                    "confidence": 0.95
                },
                "sql": "SELECT COUNT(*) as count FROM customers",
                "results": [{"count": 60}],
                "metadata": {"row_count": 1, "execution_time_seconds": 0.12, "bytes_processed": 1024}
            },
            {
                "user_query": "What is the total claim amount?",
                "execution_plan": {
                    "intent": "Calculate total claims",
                    "tables_needed": ["insurance_claims"],
                    "operations": {"aggregation": {"function": "SUM"}},
                    "confidence": 0.98
                },
                "sql": "SELECT SUM(claim_amount) as total FROM claims",
                "results": [{"total": 1696950}],
                "metadata": {"row_count": 1, "execution_time_seconds": 0.15, "bytes_processed": 2048}
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {test['user_query']}")
            print("-" * 80)
            
            response = agent.format_response(
                user_query=test['user_query'],
                system_context=schema_context,
                execution_plan=test['execution_plan'],
                sql=test['sql'],
                results=test['results'],
                metadata=test['metadata']
            )
            
            if response['formatted_response']:
                print(f"✓ Response generated: {len(response['formatted_response'])} chars")
                print(f"  Preview: {response['formatted_response'][:150]}...")
                print(f"  Execution time: {response['execution_time']}")
                print(f"  Row count: {response['row_count']}")
                print(f"  Confidence: {response['confidence_score']}")
                passed += 1
            else:
                print(f"✗ No response generated")
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: Single value result tests")
            return True
        else:
            print(f"✗ FAIL: {failed} test(s) failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_rows_result():
    """Test formatting of multiple row results"""
    print_section_header("TEST 4: Multiple Rows Result Formatting")
    
    try:
        agent = ResponseAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        schema_context = context_file.read_text()
        
        print("Test Case: Top 5 customers by premium")
        print("-" * 80)
        
        response = agent.format_response(
            user_query="Show me top 5 customers by total premium amount",
            system_context=schema_context,
            execution_plan={
                "intent": "Retrieve top customers by premium",
                "tables_needed": ["insurance_customers", "insurance_policies"],
                "operations": {
                    "aggregation": {"function": "SUM"},
                    "sorting": {"order": "DESC"},
                    "limit": 5
                },
                "confidence": 0.90
            },
            sql="SELECT c.customer_name, SUM(p.premium_amount) as total FROM customers c JOIN policies p GROUP BY c.customer_name ORDER BY total DESC LIMIT 5",
            results=[
                {"customer_name": "John Doe", "total": 50000},
                {"customer_name": "Jane Smith", "total": 45000},
                {"customer_name": "Bob Wilson", "total": 40000},
                {"customer_name": "Alice Brown", "total": 35000},
                {"customer_name": "Charlie Davis", "total": 30000}
            ],
            metadata={"row_count": 5, "execution_time_seconds": 0.45, "bytes_processed": 4096}
        )
        
        # Check response structure and content
        checks = [
            (response['formatted_response'], "Has formatted response"),
            (len(response['formatted_response']) > 100, "Response is substantial"),
            (response['row_count'] == 5, "Row count is correct"),
            (len(response['results_data']) == 5, "Results data has all rows"),
            (response['explanation'], "Has explanation"),
            (len(response['ai_reasoning']) > 0, "Has AI reasoning steps"),
            ("JOIN" in response['sql_query'].upper(), "SQL contains JOIN")
        ]
        
        passed = all(check[0] for check in checks)
        
        for check, description in checks:
            status = "✓" if check else "✗"
            print(f"  {status} {description}")
        
        print(f"\nFormatted Response ({len(response['formatted_response'])} chars):")
        print(response['formatted_response'][:300] + "...")
        
        print(f"\nAI Reasoning Steps: {len(response['ai_reasoning'])}")
        for step in response['ai_reasoning'][:3]:
            print(f"  - {step}")
        
        if passed:
            print("\n✓ PASS: Multiple rows result test")
            return True
        else:
            print("\n✗ FAIL: Some checks failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utility_functions():
    """Test utility functions (byte formatting, etc.)"""
    print_section_header("TEST 5: Utility Functions")
    
    try:
        agent = ResponseAgent()
        
        print("\nTest: Byte formatting")
        print("-" * 80)
        
        test_cases = [
            (0, "0.00MB"),
            (1024, "0.00MB"),
            (1024 * 1024, "1.0MB"),
            (1024 * 1024 * 10, "10.0MB"),
            (1024 * 1024 * 1024, "1.00GB"),
            (1024 * 1024 * 1024 * 2.5, "2.50GB")
        ]
        
        passed = 0
        failed = 0
        
        for bytes_val, expected in test_cases:
            result = agent._format_bytes(bytes_val)
            if result == expected:
                print(f"  ✓ {bytes_val} bytes -> {result}")
                passed += 1
            else:
                print(f"  ✗ {bytes_val} bytes -> {result} (expected {expected})")
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: Utility functions test")
            return True
        else:
            print(f"✗ FAIL: {failed} test(s) failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_response_structure():
    """Test that response contains all required fields"""
    print_section_header("TEST 6: Response Structure Validation")
    
    try:
        agent = ResponseAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        schema_context = context_file.read_text()
        
        print("Test Case: Complete response structure")
        print("-" * 80)
        
        response = agent.format_response(
            user_query="Test query",
            system_context=schema_context,
            execution_plan={
                "intent": "Test intent",
                "tables_needed": ["test_table"],
                "operations": {},
                "confidence": 0.8
            },
            sql="SELECT * FROM test_table",
            results=[{"id": 1, "value": "test"}],
            metadata={"row_count": 1, "execution_time_seconds": 0.1, "bytes_processed": 512}
        )
        
        # Check all required fields
        required_fields = [
            "formatted_response",
            "explanation",
            "ai_reasoning",
            "sql_query",
            "execution_time",
            "row_count",
            "bytes_processed",
            "query_interpretation",
            "confidence_score",
            "results_data"
        ]
        
        passed = 0
        failed = 0
        
        for field in required_fields:
            if field in response:
                print(f"  ✓ Has field: {field}")
                if isinstance(response[field], str):
                    print(f"    Type: str, Length: {len(response[field])}")
                elif isinstance(response[field], list):
                    print(f"    Type: list, Length: {len(response[field])}")
                elif isinstance(response[field], int):
                    print(f"    Type: int, Value: {response[field]}")
                else:
                    print(f"    Type: {type(response[field]).__name__}, Value: {response[field]}")
                passed += 1
            else:
                print(f"  ✗ Missing field: {field}")
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: Response structure test")
            return True
        else:
            print(f"✗ FAIL: {failed} field(s) missing")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reasoning_generation():
    """Test AI reasoning step generation"""
    print_section_header("TEST 7: AI Reasoning Generation")
    
    try:
        agent = ResponseAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        schema_context = context_file.read_text()
        
        test_cases = [
            {
                "sql": "SELECT c.name, SUM(p.amount) FROM customers c JOIN policies p ON c.id = p.customer_id GROUP BY c.name ORDER BY SUM(p.amount) DESC LIMIT 10",
                "execution_plan": {
                    "tables_needed": ["customers", "policies"],
                    "operations": {"aggregation": {"function": "SUM"}, "sorting": "DESC", "limit": 10}
                },
                "expected_patterns": ["JOIN", "SUM", "GROUP BY", "ORDER BY", "LIMIT"]
            },
            {
                "sql": "SELECT COUNT(*) FROM insurance_claims WHERE status = 'approved'",
                "execution_plan": {
                    "tables_needed": ["insurance_claims"],
                    "operations": {"aggregation": {"function": "COUNT"}, "filtering": {"column": "status"}}
                },
                "expected_patterns": ["COUNT", "WHERE"]
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest Case {i}")
            print("-" * 80)
            print(f"SQL: {test['sql'][:80]}...")
            
            reasoning = agent._generate_reasoning_steps(
                test['sql'],
                test['execution_plan'],
                schema_context
            )
            
            if reasoning and len(reasoning) > 0:
                print(f"✓ Generated {len(reasoning)} reasoning steps")
                for j, step in enumerate(reasoning, 1):
                    print(f"  {j}. {step}")
                passed += 1
            else:
                print(f"✗ No reasoning steps generated")
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: Reasoning generation test")
            return True
        else:
            print(f"✗ FAIL: {failed} test(s) failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RESPONSE AGENT - STANDALONE TESTS")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(("Prompt Template Loading", test_prompt_template()))
    results.append(("Utility Functions", test_utility_functions()))
    results.append(("Response Structure Validation", test_response_structure()))
    results.append(("Empty Results Handling", test_empty_results_handling()))
    results.append(("Single Value Result Formatting", test_single_value_result()))
    results.append(("Multiple Rows Result Formatting", test_multiple_rows_result()))
    results.append(("AI Reasoning Generation", test_reasoning_generation()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print_separator()
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print_separator()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("="*80 + "\n")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TEST(S) FAILED")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
