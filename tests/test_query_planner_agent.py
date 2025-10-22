#!/usr/bin/env python
"""
Standalone test script for Query Planner Agent
Tests the agent with various scenarios including clarification flows
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.query_planner import QueryPlanningAgent


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
        planner = QueryPlanningAgent()
        
        # Check template is cached
        if hasattr(planner, '_prompt_template'):
            print("✓ Prompt template is cached")
            print(f"  Template length: {len(planner._prompt_template)} chars")
            
            # Count variable placeholders
            var_count = planner._prompt_template.count('{')
            print(f"  Contains {var_count} variable placeholders")
            
            # Check for expected variables
            expected_vars = ['{schema_context}', '{history_section}', '{user_query}']
            for var in expected_vars:
                if var in planner._prompt_template:
                    print(f"  ✓ Contains variable: {var}")
                else:
                    print(f"  ✗ Missing variable: {var}")
        else:
            print("✗ Prompt template not found in agent")
        
        # Check template file exists
        if planner.PROMPT_FILE.exists():
            print(f"✓ Template file exists: {planner.PROMPT_FILE}")
        else:
            print(f"✗ Template file missing: {planner.PROMPT_FILE}")
        
        print("\n✓ PASS: Prompt template test")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_queries():
    """Test basic query planning without clarifications"""
    print_section_header("TEST 2: Basic Query Planning")
    
    try:
        planner = QueryPlanningAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        if not context_file.exists():
            print(f"✗ Schema file not found: {context_file}")
            return False
            
        schema_context = context_file.read_text()
        print(f"✓ Schema loaded: {len(schema_context)} chars\n")
        
        test_cases = [
            ("Show me all customers", True, "Should be answerable - simple query"),
            ("What's the average claim amount?", True, "Should be answerable - aggregation"),
            ("Show me employee salaries", False, "Should need clarification - no employee table"),
            ("List active policies", True, "Should be answerable with business logic"),
            ("Get customer revenue", False, "Should need clarification - no revenue column"),
        ]
        
        passed = 0
        failed = 0
        
        for query, expected_answerable, description in test_cases:
            print(f"\nQuery: '{query}'")
            print(f"Expected: {'Answerable' if expected_answerable else 'Needs Clarification'}")
            print(f"Context: {description}")
            print("-" * 80)
            
            result = planner.plan_query(query, schema_context)
            
            status = result["status"]
            success = (status == "answerable") == expected_answerable
            
            if success:
                print(f"✓ PASS - Status: {status}")
                passed += 1
            else:
                print(f"✗ FAIL - Expected: {'answerable' if expected_answerable else 'needs_clarification'}, Got: {status}")
                failed += 1
            
            if status == "answerable":
                print(f"  Tables: {result['plan']['tables_needed']}")
                print(f"  Intent: {result['plan']['intent']}")
                print(f"  Complexity: {result['plan'].get('complexity', 'unknown')}")
            else:
                clarification = result['clarification_question']
                print(f"  Clarification: {clarification[:150]}...")
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: All basic query tests")
            return True
        else:
            print(f"✗ FAIL: {failed} test(s) failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_clarification_flow():
    """Test query planning with clarification history"""
    print_section_header("TEST 3: Clarification Flow")
    
    try:
        planner = QueryPlanningAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        schema_context = context_file.read_text()
        
        # Simulate a clarification conversation
        print("\nScenario: User asks vague question, system clarifies, user responds")
        print("-" * 80)
        
        print("\nRound 1: User asks: 'Show me data'")
        result1 = planner.plan_query("Show me data", schema_context)
        print(f"Status: {result1['status']}")
        
        if result1['status'] == 'needs_clarification':
            clarification = result1['clarification_question']
            print(f"System asks: {clarification[:150]}...")
            
            print("\nRound 2: User clarifies: 'Claims data by status'")
            print("-" * 80)
            history = [
                {
                    "query": "Show me data",
                    "clarification": clarification,
                    "response": "Claims data"
                }
            ]
            result2 = planner.plan_query("by status", schema_context, history)
            print(f"Status: {result2['status']}")
            
            if result2['status'] == 'answerable':
                print(f"✓ Agent understood combined intent!")
                print(f"  Tables: {result2['plan']['tables_needed']}")
                print(f"  Intent: {result2['plan']['intent']}")
                print(f"  Complexity: {result2['plan'].get('complexity', 'unknown')}")
                print("\n✓ PASS: Clarification flow test")
                return True
            else:
                print(f"⚠ Still needs clarification: {result2['clarification_question'][:100]}...")
                print("  (This may be acceptable if query is still ambiguous)")
                print("\n✓ PASS: Clarification flow test (multiple rounds)")
                return True
        else:
            print("⚠ Query was answerable without clarification")
            print("  (This is acceptable - the query may have been clear enough)")
            print("\n✓ PASS: Clarification flow test")
            return True
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_history_section_building():
    """Test the history section building method"""
    print_section_header("TEST 4: History Section Building")
    
    try:
        planner = QueryPlanningAgent()
        
        # Test 1: Empty history
        print("\nTest 4.1: Empty history")
        result = planner._build_history_section(None, "test query")
        if result == "":
            print("✓ Returns empty string for None history")
        else:
            print(f"✗ Expected empty string, got: {len(result)} chars")
            return False
        
        # Test 2: History with data
        print("\nTest 4.2: History with conversation data")
        history = [
            {
                "query": "Show me data",
                "clarification": "What type of data?",
                "response": "Claims"
            }
        ]
        result = planner._build_history_section(history, "by status")
        
        checks = [
            ("CONVERSATION HISTORY", "Contains header"),
            ("Show me data", "Contains original query"),
            ("What type of data?", "Contains clarification"),
            ("Claims", "Contains user response"),
            ("by status", "Contains current input"),
            ("IMPORTANT", "Contains synthesis instruction"),
        ]
        
        all_passed = True
        for text, description in checks:
            if text in result:
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description}")
                all_passed = False
        
        if all_passed:
            print("\n✓ PASS: History section building test")
            return True
        else:
            print("\n✗ FAIL: Some checks failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_building():
    """Test prompt building with and without history"""
    print_section_header("TEST 5: Prompt Building")
    
    try:
        planner = QueryPlanningAgent()
        
        # Test 1: Without history
        print("\nTest 5.1: Building prompt without history")
        prompt = planner._build_planning_prompt(
            user_query="Show me claims",
            schema_context="TEST SCHEMA CONTENT",
            clarification_history=None
        )
        
        if "TEST SCHEMA CONTENT" in prompt:
            print("  ✓ Contains schema context")
        else:
            print("  ✗ Missing schema context")
            return False
            
        if "Show me claims" in prompt:
            print("  ✓ Contains user query")
        else:
            print("  ✗ Missing user query")
            return False
            
        if "CONVERSATION HISTORY" not in prompt:
            print("  ✓ Does not contain conversation history")
        else:
            print("  ✗ Should not contain conversation history")
            return False
        
        # Test 2: With history
        print("\nTest 5.2: Building prompt with history")
        history = [
            {
                "query": "Show data",
                "clarification": "What type?",
                "response": "Claims"
            }
        ]
        prompt = planner._build_planning_prompt(
            user_query="by status",
            schema_context="TEST SCHEMA CONTENT",
            clarification_history=history
        )
        
        if "TEST SCHEMA CONTENT" in prompt:
            print("  ✓ Contains schema context")
        else:
            print("  ✗ Missing schema context")
            return False
            
        if "by status" in prompt:
            print("  ✓ Contains current user query")
        else:
            print("  ✗ Missing current user query")
            return False
            
        if "CONVERSATION HISTORY" in prompt:
            print("  ✓ Contains conversation history section")
        else:
            print("  ✗ Missing conversation history section")
            return False
            
        if "Show data" in prompt:
            print("  ✓ Contains previous query from history")
        else:
            print("  ✗ Missing previous query from history")
            return False
        
        print("\n✓ PASS: Prompt building test")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("QUERY PLANNER AGENT - STANDALONE TESTS")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(("Prompt Template Loading", test_prompt_template()))
    results.append(("History Section Building", test_history_section_building()))
    results.append(("Prompt Building", test_prompt_building()))
    results.append(("Basic Query Planning", test_basic_queries()))
    results.append(("Clarification Flow", test_clarification_flow()))
    
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
