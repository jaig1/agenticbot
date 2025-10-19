"""
Worker Agent Demo - Interactive Text2SQL Demonstration

This demo script showcases the WorkerAgent's end-to-end Text2SQL capabilities
using insurance-specific queries against the BigQuery dataset.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agents.worker import WorkerAgent


def main():
    print("\n" + "="*80)
    print("Worker Agent Demo - Interactive Text2SQL")
    print("="*80 + "\n")
    
    # Initialize agent
    print("Initializing Worker Agent...")
    try:
        agent = WorkerAgent()
        print("✓ Agent ready\n")
    except Exception as e:
        print(f"✗ Failed to initialize agent: {e}")
        return
    
    # Insurance-specific example queries
    queries = [
        "How many insurance customers are in the database?",
        "What is the average claim amount for approved claims?",
        "Show me the first 5 insurance policies ordered by start date",
        "How many insurance agents work in the New York region?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i} of {len(queries)}")
        print(f"{'='*80}")
        print(f"\nUser: {query}")
        print("-" * 80)
        
        result = agent.process_query(query)
        
        if result["success"]:
            print(f"\n✓ SUCCESS\n")
            print(f"Generated SQL:")
            print(f"{result['sql']}\n")
            print(f"Response:")
            print(f"{result['response']}\n")
            print(f"Metadata:")
            print(f"  - Execution Time: {result['metadata']['execution_time_seconds']:.3f}s")
            print(f"  - Rows Returned: {result['metadata']['row_count']}")
            print(f"  - Bytes Processed: {result['metadata']['bytes_processed']:,} bytes")
        else:
            print(f"\n✗ FAILED\n")
            print(f"Error: {result['response']}")
            if result['sql']:
                print(f"\nAttempted SQL:")
                print(f"{result['sql']}")
    
    print("\n" + "="*80)
    print("Demo Complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
