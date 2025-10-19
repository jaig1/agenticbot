"""
Supervisor Agent Demo - 3-Agent Architecture (Phase 2.2)

This demo showcases the 3-agent architecture with natural language response formatting:
    User Query → Supervisor → Query Planner → Query Execution Agent → Response Agent

Query Planner: Validates queries and creates execution plans
Query Execution Agent: Generates SQL and executes queries
Response Agent: Formats results into natural language explanations

Includes clarification loop testing to demonstrate multi-round conversations.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agents.supervisor import SupervisorAgent


def print_separator(title="", char="="):
    """Print a visual separator."""
    if title:
        print(f"\n{char*80}")
        print(f"  {title}")
        print(f"{char*80}")
    else:
        print(f"\n{char*80}\n")


def test_clarification_loop(supervisor):
    """Test the clarification loop functionality."""
    print_separator("CLARIFICATION LOOP TEST", "=")
    
    print("\nThis test demonstrates the multi-round clarification feature.")
    print("The system will ask for clarification and merge responses intelligently.\n")
    
    # Test 1: Basic clarification
    print_separator("Test 1: Basic Single-Round Clarification", "-")
    print("\n👤 User: Show me data")
    
    result = supervisor.handle_query("Show me data")
    
    print(f"\n🤖 Bot: {result['response'][:300]}...")
    print(f"📊 Status: {'✓ Success' if result['success'] else '⚠️  Needs Clarification'}")
    
    if result['metadata'].get('needs_clarification'):
        clarification_key = result['metadata']['clarification_key']
        round_num = result['metadata']['clarification_round']
        max_rounds = result['metadata']['max_rounds']
        print(f"📍 Clarification Round: {round_num}/{max_rounds}")
        
        # Provide clarification
        print(f"\n{'-'*80}")
        print("\n👤 User responds: by status")
        
        result2 = supervisor.handle_clarification_response(clarification_key, "by status")
        
        print(f"\n🤖 Bot: {result2['response'][:200]}...")
        print(f"📊 Status: {'✓ Success' if result2['success'] else '❌ Failed'}")
        
        if result2['success']:
            print(f"\n✅ SQL Generated:")
            print(result2['sql'][:400] + ("..." if len(result2['sql']) > 400 else ""))
            print(f"\n📈 Results: {result2['metadata']['row_count']} rows returned")
        else:
            print(f"\n⚠️  Needs more clarification")
    
    # Test 2: Direct answer (no clarification)
    print_separator("Test 2: Direct Answer (No Clarification)", "-")
    print("\n👤 User: Show me total claims by status")
    
    result = supervisor.handle_query("Show me total claims by status")
    
    print(f"\n🤖 Bot: {result['response'][:200]}...")
    print(f"📊 Status: {'✓ Success' if result['success'] else '❌ Failed'}")
    
    if result['success']:
        print(f"\n✅ Direct answer - No clarification needed")
        print(f"📈 Results: {result['metadata']['row_count']} rows returned")
    
    print_separator()


def demo_basic_queries(supervisor):
    """Run basic query demonstrations."""
    print_separator("BASIC QUERY DEMONSTRATIONS", "=")
    
    # Example queries
    queries = [
        "How many insurance customers do we have?",
        "What is the total claim amount?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'-'*80}")
        print(f"Query {i}: {query}")
        print('-'*80)
        
        result = supervisor.handle_query(query)
        
        if result["success"]:
            print(f"\n✓ Success")
            print(f"\n--- Generated SQL ---")
            print(result['sql'])
            print(f"\n--- Formatted Response ---")
            print(result['response'][:300] + ("..." if len(result['response']) > 300 else ""))
            print(f"\n--- Metadata ---")
            display_data = result.get('display_data', {})
            print(f"Execution time: {display_data.get('execution_time', 'N/A')}")
            print(f"Rows: {display_data.get('row_count', 0)}")
        else:
            print(f"\n✗ Failed or Needs Clarification")
            print(f"\nResponse:")
            print(result['response'][:300])
    
    print_separator()


def main():
    print_separator("Supervisor Agent Demo - 3-Agent Architecture with Clarification Loop", "=")
    
    print("\nArchitecture:")
    print("  User Query → Supervisor")
    print("    ↓")
    print("  Query Planner (validates + creates plan)")
    print("    ↓")
    print("  Query Execution Agent (generates SQL + executes)")
    print("    ↓")
    print("  Response Agent (explains results in natural language)")
    print("    ↓")
    print("  User-friendly Response")
    
    print("\nNew Feature: Multi-Round Clarification Loop")
    print("  - System asks for clarification when query is ambiguous")
    print("  - User provides clarification")
    print("  - System merges context and re-analyzes")
    print("  - Max 3 rounds of clarification")
    
    print_separator()
    
    # Initialize Supervisor
    print("\nInitializing Supervisor Agent...")
    try:
        supervisor = SupervisorAgent()
        print("✓ Supervisor ready\n")
    except Exception as e:
        print(f"✗ Failed to initialize Supervisor: {e}")
        return
    
    # Run clarification loop tests
    test_clarification_loop(supervisor)
    
    # Run basic query demos
    demo_basic_queries(supervisor)
    
    # Show session stats
    print_separator("Session Statistics", "=")
    stats = supervisor.get_stats()
    print(f"\nTotal queries: {stats['total_requests']}")
    print(f"Successful: {stats['successful_requests']}")
    print(f"Failed: {stats['failed_requests']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    
    # Show conversation history summary
    print_separator("Conversation History Summary", "=")
    history = supervisor.get_conversation_history()
    for entry in history:
        status = "✓" if entry["success"] else "✗"
        print(f"{status} Request {entry['request_number']}: {entry['user_query'][:60]}...")
    
    print_separator("Demo Complete", "=")
    print()


if __name__ == "__main__":
    main()
