"""
Supervisor Agent Demo - 3-Agent Architecture (Phase 2.2)

This demo showcases the 3-agent architecture with natural language response formatting:
    User Query → Supervisor → Query Planner → Query Execution Agent → Response Agent

Query Planner: Validates queries and creates execution plans
Query Execution Agent: Generates SQL and executes queries
Response Agent: Formats results into natural language explanations
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agents.supervisor import SupervisorAgent


def main():
    print("\n" + "="*80)
    print("Supervisor Agent Demo - 3-Agent Architecture")
    print("="*80 + "\n")
    
    print("Architecture:")
    print("  User Query → Supervisor")
    print("    ↓")
    print("  Query Planner (validates + creates plan)")
    print("    ↓")
    print("  Query Execution Agent (generates SQL + executes)")
    print("    ↓")
    print("  Response Agent (explains results in natural language)")
    print("    ↓")
    print("  User-friendly Response")
    print()
    print("="*80 + "\n")
    
    # Initialize Supervisor
    print("Initializing Supervisor Agent...")
    try:
        supervisor = SupervisorAgent()
        print("✓ Supervisor ready\n")
    except Exception as e:
        print(f"✗ Failed to initialize Supervisor: {e}")
        return
    
    # Example queries
    queries = [
        "How many insurance customers do we have?",
        "What is the total claim amount?",
        "Show me employee performance data",  # Should need clarification
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print('='*80)
        
        result = supervisor.handle_query(query)
        
        if result["success"]:
            print(f"\n✓ Success")
            print(f"\n--- Generated SQL ---")
            print(result['sql'])
            print(f"\n--- Formatted Response ---")
            print(result['response'])
            print(f"\n--- Metadata ---")
            print(f"Summary: {result['summary']}")
            print(f"Methodology: {result['methodology']}")
            print(f"Execution time: {result['metadata']['execution_time_seconds']}s")
            print(f"Rows: {result['metadata']['row_count']}")
        else:
            print(f"\n✗ Failed or Needs Clarification")
            print(f"\nResponse:")
            print(result['response'])
    
    # Show session stats
    print(f"\n{'='*80}")
    print("Session Statistics")
    print('='*80)
    stats = supervisor.get_stats()
    print(f"Total queries: {stats['total_requests']}")
    print(f"Successful: {stats['successful_requests']}")
    print(f"Failed: {stats['failed_requests']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    
    # Show conversation history summary
    print(f"\n{'='*80}")
    print("Conversation History Summary")
    print('='*80)
    history = supervisor.get_conversation_history()
    for entry in history:
        status = "✓" if entry["success"] else "✗"
        print(f"{status} Request {entry['request_number']}: {entry['user_query'][:60]}...")
    
    print(f"\n{'='*80}")
    print("Demo Complete")
    print('='*80 + "\n")


if __name__ == "__main__":
    main()
