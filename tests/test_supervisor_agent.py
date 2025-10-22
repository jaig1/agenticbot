#!/usr/bin/env python
"""
Supervisor Agent Test Suite - Comprehensive Testing & Demonstration

This script tests the complete 3-agent architecture with clarification loop:
    User Query → Supervisor → Query Planner → Query Execution Agent → Response Agent

Tests include:
- Multi-round clarification loop functionality
- Direct answer handling (no clarification needed)
- Max rounds limit enforcement
- Basic query demonstrations
- Session statistics and conversation history

Architecture:
- Query Planner: Validates queries and creates execution plans
- Query Execution Agent: Generates SQL and executes queries
- Response Agent: Formats results into natural language explanations
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.supervisor import SupervisorAgent


def print_separator(title="", char="="):
    """Print a visual separator."""
    if title:
        print(f"\n{char*80}")
        print(f"  {title}")
        print(f"{char*80}")
    else:
        print(f"\n{char*80}\n")


def test_basic_clarification():
    """Test Case 1: Basic single-round clarification."""
    print_separator("TEST 1: Basic Single-Round Clarification", "=")
    
    supervisor = SupervisorAgent()
    
    # Step 1: Ask ambiguous question
    print("\n👤 User: Show me top customers")
    result1 = supervisor.handle_query("Show me top customers")
    
    print(f"\n🤖 Bot: {result1['response']}")
    print(f"\n📊 Status: {'✓ Success' if result1['success'] else '⚠️  Needs Clarification'}")
    
    if result1['metadata'].get('needs_clarification'):
        clarification_key = result1['metadata']['clarification_key']
        clarification_round = result1['metadata']['clarification_round']
        print(f"📍 Clarification Round: {clarification_round}/{result1['metadata']['max_rounds']}")
        print(f"🔑 Clarification Key: {clarification_key}")
        
        # Step 2: Provide clarification
        print_separator("", "-")
        print("\n👤 User: by premium amount")
        result2 = supervisor.handle_clarification_response(clarification_key, "by premium amount")
        
        print(f"\n🤖 Bot: {result2['response'][:200]}...")
        print(f"\n📊 Status: {'✓ Success' if result2['success'] else '⚠️  Still needs clarification'}")
        
        if result2['success']:
            print(f"\n✅ SQL Generated:")
            print(result2['sql'][:400] + ("..." if len(result2['sql']) > 400 else ""))
            print(f"\n📈 Results: {result2['metadata']['row_count']} rows")
            return True
        else:
            print(f"\n❌ Failed to generate SQL after clarification")
            return False
    else:
        print(f"\n❌ Expected clarification but got direct answer")
        return False


def test_multi_round_clarification():
    """Test Case 2: Multi-round clarification."""
    print_separator("TEST 2: Multi-Round Clarification", "=")
    
    supervisor = SupervisorAgent()
    
    # Round 1
    print("\n👤 User: Show me top customers")
    result = supervisor.handle_query("Show me top customers")
    print(f"\n🤖 Bot: {result['response']}")
    
    if not result['metadata'].get('needs_clarification'):
        print("\n❌ Expected clarification but got direct answer")
        return False
    
    clarification_key = result['metadata']['clarification_key']
    round_num = result['metadata']['clarification_round']
    print(f"📍 Round {round_num}: Needs clarification")
    
    # Round 2
    print_separator("", "-")
    print("\n👤 User: by revenue")
    result = supervisor.handle_clarification_response(clarification_key, "by revenue")
    print(f"\n🤖 Bot: {result['response'][:200]}...")
    print(f"\n📊 Status: {'✓ Success' if result['success'] else '⚠️  Needs more clarification'}")
    
    if result['success']:
        print(f"\n✅ SQL Generated after {round_num} round(s)")
        print(result['sql'][:300] + "...")
        return True
    elif result['metadata'].get('needs_clarification'):
        # May need another round
        round_num = result['metadata']['clarification_round']
        print(f"📍 Round {round_num}: Still needs clarification")
        
        # Round 3 (if needed)
        print_separator("", "-")
        print("\n👤 User: for last year")
        result = supervisor.handle_clarification_response(clarification_key, "for last year")
        print(f"\n🤖 Bot: {result['response'][:200]}...")
        print(f"\n📊 Status: {'✓ Success' if result['success'] else '❌ Failed'}")
        
        if result['success']:
            print(f"\n✅ SQL Generated after multiple rounds")
            print(result['sql'][:300] + "...")
            return True
        
    return False


def test_max_rounds_limit():
    """Test Case 3: Max rounds limit enforcement."""
    print_separator("TEST 3: Max Rounds Limit (3 rounds)", "=")
    
    supervisor = SupervisorAgent()
    
    clarification_key = None
    
    # Keep giving vague responses
    vague_responses = [
        "Show me data",
        "just data",
        "information",
        "stats"
    ]
    
    for i, response in enumerate(vague_responses, 1):
        print_separator("", "-")
        print(f"\n👤 User (Round {i}): {response}")
        
        if i == 1:
            result = supervisor.handle_query(response)
        else:
            result = supervisor.handle_clarification_response(clarification_key, response)
        
        print(f"\n🤖 Bot: {result['response'][:200]}...")
        
        if result['metadata'].get('needs_clarification'):
            clarification_key = result['metadata']['clarification_key']
            round_num = result['metadata']['clarification_round']
            max_rounds = result['metadata']['max_rounds']
            print(f"📍 Clarification Round: {round_num}/{max_rounds}")
        elif result['metadata'].get('max_rounds_reached'):
            print(f"\n✅ Max rounds limit enforced correctly!")
            print(f"🛑 System stopped after {supervisor.max_clarification_rounds} rounds")
            return True
        elif result['success']:
            print(f"\n⚠️  Unexpectedly got success")
            return False
    
    print(f"\n❌ Should have hit max rounds limit")
    return False


def test_direct_answer():
    """Test Case 4: Direct answer (no clarification needed)."""
    print_separator("TEST 4: Direct Answer (No Clarification)", "=")
    
    supervisor = SupervisorAgent()
    
    print("\n👤 User: Show me total claims grouped by status")
    result = supervisor.handle_query("Show me total claims grouped by status")
    
    print(f"\n🤖 Bot: {result['response'][:200]}...")
    print(f"\n📊 Status: {'✓ Success' if result['success'] else '❌ Failed'}")
    
    if result['success']:
        print(f"\n✅ Direct answer provided without clarification")
        print(f"\n📝 SQL Generated:")
        print(result['sql'][:400] + ("..." if len(result['sql']) > 400 else ""))
        print(f"\n📈 Results: {result['metadata']['row_count']} rows")
        return True
    elif result['metadata'].get('needs_clarification'):
        print(f"\n❌ Should not need clarification for specific query")
        return False
    else:
        print(f"\n❌ Query failed")
        return False


def test_basic_query_demonstrations():
    """Test Case 5: Basic query demonstrations with full output."""
    print_separator("TEST 5: Basic Query Demonstrations", "=")
    
    supervisor = SupervisorAgent()
    
    # Example queries
    queries = [
        "How many insurance customers do we have?",
        "What is the total claim amount?",
    ]
    
    passed = 0
    failed = 0
    
    for i, query in enumerate(queries, 1):
        print_separator("", "-")
        print(f"\nQuery {i}: {query}")
        print('-'*80)
        
        result = supervisor.handle_query(query)
        
        if result["success"]:
            print(f"\n✓ Success")
            print(f"\n--- Generated SQL ---")
            print(result['sql'])
            print(f"\n--- Formatted Response ---")
            print(result['response'][:300] + ("..." if len(result['response']) > 300 else ""))
            print(f"\n--- Metadata ---")
            print(f"Execution time: {result['metadata'].get('execution_time_seconds', 'N/A')}s")
            print(f"Rows: {result['metadata'].get('row_count', 0)}")
            print(f"Bytes processed: {result['metadata'].get('bytes_processed', 0):,} bytes")
            passed += 1
        else:
            print(f"\n✗ Failed or Needs Clarification")
            print(f"\nResponse:")
            print(result['response'][:300])
            failed += 1
    
    print_separator("", "-")
    print(f"Query Demonstrations: {passed} passed, {failed} failed")
    
    return failed == 0


def test_session_stats():
    """Test Case 6: Session statistics and conversation history."""
    print_separator("TEST 6: Session Statistics & History", "=")
    
    supervisor = SupervisorAgent()
    
    # Run a few queries to build history
    queries = [
        "How many customers?",
        "Total claim amount",
        "Show policies"
    ]
    
    print("\nRunning sample queries to build history...\n")
    
    for query in queries:
        print(f"  Running: {query}")
        result = supervisor.handle_query(query)
        status = "✓" if result['success'] else "✗"
        print(f"  {status} {'Success' if result['success'] else 'Failed/Clarification needed'}")
    
    # Get session statistics
    print_separator("Session Statistics", "-")
    stats = supervisor.get_stats()
    print(f"\nTotal queries: {stats['total_requests']}")
    print(f"Successful: {stats['successful_requests']}")
    print(f"Failed: {stats['failed_requests']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    
    # Get conversation history
    print_separator("Conversation History Summary", "-")
    history = supervisor.get_conversation_history()
    
    if not history:
        print("\n⚠️  No conversation history found")
        return False
    
    for entry in history:
        status = "✓" if entry["success"] else "✗"
        print(f"{status} Request {entry['request_number']}: {entry['user_query'][:60]}...")
    
    print(f"\n✅ Session stats test passed ({len(history)} queries in history)")
    return True


def main():
    """Run all test cases."""
    print_separator("SUPERVISOR AGENT - COMPREHENSIVE TEST SUITE", "=")
    
    print("\nArchitecture:")
    print("  User Query → Supervisor Agent")
    print("    ↓")
    print("  Query Planner Agent (validates + creates execution plan)")
    print("    ↓")
    print("  Query Execution Agent (generates SQL + executes)")
    print("    ↓")
    print("  Response Agent (formats results in natural language)")
    print("    ↓")
    print("  User-friendly Response")
    
    print("\nFeatures Tested:")
    print("  - Multi-round clarification loop (max 3 rounds)")
    print("  - Direct answer handling (no clarification)")
    print("  - Max rounds enforcement")
    print("  - Query demonstrations with full output")
    print("  - Session statistics and conversation history")
    
    print_separator("", "=")
    
    tests = [
        ("Basic Single-Round Clarification", test_basic_clarification),
        ("Multi-Round Clarification", test_multi_round_clarification),
        ("Max Rounds Limit Enforcement", test_max_rounds_limit),
        ("Direct Answer (No Clarification)", test_direct_answer),
        ("Basic Query Demonstrations", test_basic_query_demonstrations),
        ("Session Statistics & History", test_session_stats),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n\n{'#'*80}")
            print(f"# Running: {test_name}")
            print(f"{'#'*80}")
            
            success = test_func()
            results.append((test_name, success))
            
            print_separator("", "-")
            print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
            
        except Exception as e:
            print(f"\n💥 Exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n\n" + "="*80)
    print("  TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print(f"\n{'='*80}")
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
