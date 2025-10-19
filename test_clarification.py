"""
Test Clarification Loop - Manual Testing Script

This script tests the clarification loop functionality without the UI.
It simulates a conversation with multiple rounds of clarification.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.agents.supervisor import SupervisorAgent


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print('='*80)
    else:
        print(f"\n{'-'*80}\n")


def test_basic_clarification():
    """Test Case 1: Basic single-round clarification."""
    print_separator("TEST 1: Basic Single-Round Clarification")
    
    supervisor = SupervisorAgent()
    
    # Step 1: Ask ambiguous question
    print("\n👤 User: Show me claims")
    result1 = supervisor.handle_query("Show me claims")
    
    print(f"\n🤖 Bot: {result1['response']}")
    print(f"\n📊 Status: {'✓ Success' if result1['success'] else '⚠️  Needs Clarification'}")
    
    if result1['metadata'].get('needs_clarification'):
        clarification_key = result1['metadata']['clarification_key']
        clarification_round = result1['metadata']['clarification_round']
        print(f"📍 Clarification Round: {clarification_round}/{result1['metadata']['max_rounds']}")
        print(f"🔑 Clarification Key: {clarification_key}")
        
        # Step 2: Provide clarification
        print_separator()
        print("\n👤 User: by status")
        result2 = supervisor.handle_clarification_response(clarification_key, "by status")
        
        print(f"\n🤖 Bot: {result2['response'][:200]}...")
        print(f"\n📊 Status: {'✓ Success' if result2['success'] else '⚠️  Still needs clarification'}")
        
        if result2['success']:
            print(f"\n✅ SQL Generated:")
            print(result2['sql'])
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
    print_separator("TEST 2: Multi-Round Clarification")
    
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
    print_separator()
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
        print_separator()
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
    print_separator("TEST 3: Max Rounds Limit (3 rounds)")
    
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
        print_separator()
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
    print_separator("TEST 4: Direct Answer (No Clarification)")
    
    supervisor = SupervisorAgent()
    
    print("\n👤 User: Show me total claims grouped by status")
    result = supervisor.handle_query("Show me total claims grouped by status")
    
    print(f"\n🤖 Bot: {result['response'][:200]}...")
    print(f"\n📊 Status: {'✓ Success' if result['success'] else '❌ Failed'}")
    
    if result['success']:
        print(f"\n✅ Direct answer provided without clarification")
        print(f"\n📝 SQL Generated:")
        print(result['sql'])
        print(f"\n📈 Results: {result['metadata']['row_count']} rows")
        return True
    elif result['metadata'].get('needs_clarification'):
        print(f"\n❌ Should not need clarification for specific query")
        return False
    else:
        print(f"\n❌ Query failed")
        return False


def main():
    """Run all test cases."""
    print("\n" + "="*80)
    print("  CLARIFICATION LOOP - TEST SUITE")
    print("="*80)
    
    tests = [
        ("Basic Single-Round Clarification", test_basic_clarification),
        ("Multi-Round Clarification", test_multi_round_clarification),
        ("Max Rounds Limit Enforcement", test_max_rounds_limit),
        ("Direct Answer (No Clarification)", test_direct_answer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n\n{'#'*80}")
            print(f"# Running: {test_name}")
            print(f"{'#'*80}")
            
            success = test_func()
            results.append((test_name, success))
            
            print_separator()
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
