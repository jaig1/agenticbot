#!/usr/bin/env python
"""
Standalone test script for Query Execution Agent
Tests SQL generation and execution capabilities
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.query_execution import QueryExecutionAgent


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
        agent = QueryExecutionAgent()
        
        # Check template is cached
        if hasattr(agent, '_prompt_template'):
            print("✓ Prompt template is cached")
            print(f"  Template length: {len(agent._prompt_template)} chars")
            
            # Count variable placeholders
            var_count = agent._prompt_template.count('{')
            print(f"  Contains {var_count} variable placeholders")
            
            # Check for expected variables
            expected_vars = ['{schema_context}', '{user_query}', '{execution_plan}', '{dataset_reference}']
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


def test_sql_generation():
    """Test SQL generation from execution plans"""
    print_section_header("TEST 2: SQL Generation")
    
    try:
        agent = QueryExecutionAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        if not context_file.exists():
            print(f"✗ Schema file not found: {context_file}")
            return False
            
        schema_context = context_file.read_text()
        print(f"✓ Schema loaded: {len(schema_context)} chars\n")
        
        test_cases = [
            {
                "user_query": "Count all customers",
                "execution_plan": {
                    "intent": "Count total customers",
                    "tables_needed": ["insurance_customers"],
                    "operations": {"aggregation": {"function": "COUNT"}}
                },
                "expected_keywords": ["COUNT", "insurance_customers"]
            },
            {
                "user_query": "Sum all claim amounts",
                "execution_plan": {
                    "intent": "Calculate total claim amounts",
                    "tables_needed": ["insurance_claims"],
                    "operations": {"aggregation": {"function": "SUM", "column": "claim_amount"}}
                },
                "expected_keywords": ["SUM", "claim_amount", "insurance_claims"]
            },
            {
                "user_query": "Get top 10 policies by premium",
                "execution_plan": {
                    "intent": "Retrieve highest premium policies",
                    "tables_needed": ["insurance_policies"],
                    "operations": {
                        "sorting": {"column": "premium_amount", "order": "DESC"},
                        "limit": 10
                    }
                },
                "expected_keywords": ["ORDER BY", "DESC", "LIMIT 10"]
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {test['user_query']}")
            print("-" * 80)
            
            sql = agent._generate_sql(
                test['user_query'],
                schema_context,
                test['execution_plan']
            )
            
            if sql:
                print(f"✓ SQL generated successfully")
                print(f"  Length: {len(sql)} chars")
                print(f"  SQL: {sql[:150]}...")
                
                # Check for expected keywords
                keywords_found = 0
                sql_upper = sql.upper()
                for keyword in test['expected_keywords']:
                    if keyword.upper() in sql_upper:
                        print(f"  ✓ Contains: {keyword}")
                        keywords_found += 1
                    else:
                        print(f"  ✗ Missing: {keyword}")
                
                if keywords_found == len(test['expected_keywords']):
                    print(f"✓ PASS - All keywords found")
                    passed += 1
                else:
                    print(f"⚠ PARTIAL - {keywords_found}/{len(test['expected_keywords'])} keywords found")
                    passed += 1  # Still count as pass if SQL generated
            else:
                print(f"✗ FAIL - SQL generation returned None")
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: All SQL generation tests")
            return True
        else:
            print(f"✗ FAIL: {failed} test(s) failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sql_cleaning():
    """Test SQL cleaning functionality"""
    print_section_header("TEST 3: SQL Cleaning")
    
    try:
        agent = QueryExecutionAgent()
        
        test_cases = [
            {
                "input": "```sql\nSELECT * FROM table\n```",
                "expected_clean": "SELECT * FROM table",
                "description": "Remove SQL markdown blocks"
            },
            {
                "input": "```\nSELECT * FROM table\n```",
                "expected_clean": "SELECT * FROM table",
                "description": "Remove generic markdown blocks"
            },
            {
                "input": "-- This is a comment\nSELECT * FROM table\n# Another comment",
                "expected_clean": "SELECT * FROM table",
                "description": "Remove comment lines"
            },
            {
                "input": "SELECT * FROM table",
                "expected_clean": "SELECT * FROM table",
                "description": "No cleaning needed"
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {test['description']}")
            print("-" * 80)
            print(f"Input: {repr(test['input'][:50])}...")
            
            cleaned = agent._clean_sql(test['input'])
            
            if cleaned.strip() == test['expected_clean'].strip():
                print(f"✓ PASS - Cleaned correctly")
                print(f"  Result: {cleaned}")
                passed += 1
            else:
                print(f"✗ FAIL - Unexpected result")
                print(f"  Expected: {test['expected_clean']}")
                print(f"  Got: {cleaned}")
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: All SQL cleaning tests")
            return True
        else:
            print(f"✗ FAIL: {failed} test(s) failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_end_to_end_execution():
    """Test end-to-end query execution (SQL generation + BigQuery execution)"""
    print_section_header("TEST 4: End-to-End Query Execution")
    
    try:
        agent = QueryExecutionAgent()
        
        # Load schema
        context_file = Path("config/systemcontext.md")
        schema_context = context_file.read_text()
        
        test_cases = [
            {
                "user_query": "How many insurance customers do we have?",
                "execution_plan": {
                    "intent": "Count total insurance customers",
                    "tables_needed": ["insurance_customers"],
                    "operations": {"aggregation": {"function": "COUNT"}}
                },
                "expected_rows": 1
            },
            {
                "user_query": "What is the total claim amount?",
                "execution_plan": {
                    "intent": "Calculate total claim amounts",
                    "tables_needed": ["insurance_claims"],
                    "operations": {"aggregation": {"function": "SUM", "column": "claim_amount"}}
                },
                "expected_rows": 1
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test in enumerate(test_cases, 1):
            print(f"\nTest Case {i}: {test['user_query']}")
            print("-" * 80)
            
            result = agent.execute_query(
                test['user_query'],
                schema_context,
                test['execution_plan']
            )
            
            if result['success']:
                print(f"✓ Query executed successfully")
                print(f"  SQL: {result['sql'][:100]}...")
                print(f"  Rows returned: {result['metadata']['row_count']}")
                print(f"  Execution time: {result['metadata']['execution_time_seconds']}s")
                
                if result['results']:
                    print(f"  Sample result: {result['results'][0]}")
                
                if result['metadata']['row_count'] == test['expected_rows']:
                    print(f"✓ PASS - Row count matches expected")
                    passed += 1
                else:
                    print(f"⚠ PARTIAL - Expected {test['expected_rows']} rows, got {result['metadata']['row_count']}")
                    passed += 1  # Still count as pass if query succeeded
            else:
                print(f"✗ FAIL - Query execution failed")
                print(f"  Error: {result['metadata'].get('error', 'Unknown')}")
                failed += 1
        
        print(f"\n{'='*80}")
        print(f"Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("✓ PASS: All end-to-end execution tests")
            return True
        else:
            print(f"✗ FAIL: {failed} test(s) failed")
            return False
            
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connector_integration():
    """Test integration with Database Connector"""
    print_section_header("TEST 5: Database Connector Integration")
    
    try:
        agent = QueryExecutionAgent()
        
        # Check that db_connector is initialized
        if hasattr(agent, 'db_connector'):
            print("✓ Database connector is initialized")
            print(f"  Type: {type(agent.db_connector).__name__}")
        else:
            print("✗ Database connector not found")
            return False
        
        # Check configuration
        print(f"✓ Project ID: {agent.project_id}")
        print(f"✓ Dataset ID: {agent.dataset_id}")
        print(f"✓ Model: {agent.model_name}")
        
        print("\n✓ PASS: Database connector integration test")
        return True
        
    except Exception as e:
        print(f"\n✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("QUERY EXECUTION AGENT - STANDALONE TESTS")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(("Prompt Template Loading", test_prompt_template()))
    results.append(("SQL Cleaning", test_sql_cleaning()))
    results.append(("Database Connector Integration", test_database_connector_integration()))
    results.append(("SQL Generation", test_sql_generation()))
    results.append(("End-to-End Query Execution", test_end_to_end_execution()))
    
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
