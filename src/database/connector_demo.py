#!/usr/bin/env python3
"""
Database Connector Demo

Demonstrates how to use the DatabaseConnector with Application Default Credentials.
Shows connection testing, query execution, error handling, and metadata retrieval.
"""

import sys
import os
import logging

# Add parent directory to path to access src module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.connector import DatabaseConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def demonstrate_connection_test():
    """Test BigQuery connection using ADC."""
    print("=" * 80)
    print("Testing BigQuery Connection with ADC")
    print("=" * 80)
    print("Attempting to connect using Application Default Credentials...")
    print()
    
    try:
        connector = DatabaseConnector()
        
        if connector.test_connection():
            print("✓ Connection successful")
            print("✓ Application Default Credentials are properly configured")
            print(f"✓ Project: {connector.project_id}")
            print(f"✓ Dataset: {connector.dataset_id}")
        else:
            print("✗ Connection failed")
            print("\nTo fix this, run:")
            print("  gcloud auth application-default login")
            print("\nOr ensure service account is properly configured")
        
        return connector
        
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nEnsure your .env file has:")
        print("  GCP_PROJECT_ID=your-project-id")
        print("  BQ_DATASET_ID=your-dataset-name")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def demonstrate_simple_query(connector):
    """Execute a simple query."""
    print("\n" + "=" * 80)
    print("Executing Simple Query")
    print("=" * 80)
    
    sql = "SELECT CURRENT_DATE() as today, 'Hello BigQuery' as message, @@project_id as project"
    print(f"SQL: {sql}")
    print()
    
    results, metadata = connector.execute_query(sql)
    
    if metadata["success"]:
        print("✓ Query executed successfully")
        print(f"  Rows returned: {metadata['row_count']}")
        print(f"  Execution time: {metadata['execution_time_seconds']}s")
        print(f"  Bytes processed: {connector._format_bytes(metadata['bytes_processed'])}")
        print(f"  Bytes billed: {connector._format_bytes(metadata['bytes_billed'])}")
        print(f"  Query ID: {metadata['query_id']}")
        print()
        print("Results:")
        for row in results:
            print(f"  {row}")
    else:
        print("✗ Query failed")
        print(f"  Error: {metadata['error']}")


def demonstrate_syntax_validation(connector):
    """Validate SQL syntax with and without errors."""
    print("\n" + "=" * 80)
    print("SQL Syntax Validation")
    print("=" * 80)
    
    # Test valid SQL
    print("Testing with valid SQL...")
    sql = "SELECT 1 AS test"
    is_valid, error = connector.validate_sql_syntax(sql)
    print(f"  SQL: {sql}")
    print(f"  Valid: {is_valid}")
    print()
    
    # Test invalid SQL
    print("Testing with invalid SQL (typo: FORM instead of FROM)...")
    sql = "SELECT * FORM invalid_table"
    is_valid, error = connector.validate_sql_syntax(sql)
    print(f"  SQL: {sql}")
    print(f"  Valid: {is_valid}")
    if error:
        # Show first line of error only
        error_preview = error.split('\n')[0]
        print(f"  Error: {error_preview}")


def demonstrate_query_with_data(connector):
    """Query actual data from BigQuery."""
    print("\n" + "=" * 80)
    print("Querying Actual Data")
    print("=" * 80)
    
    # Query INFORMATION_SCHEMA to get tables
    sql = f"""
        SELECT table_name, table_type
        FROM `{connector.project_id}.{connector.dataset_id}.INFORMATION_SCHEMA.TABLES`
        LIMIT 5
    """
    
    print(f"Querying tables in dataset '{connector.dataset_id}'...")
    print()
    
    results, metadata = connector.execute_query(sql)
    
    if metadata["success"]:
        print(f"✓ Found {metadata['row_count']} tables:")
        print()
        for row in results:
            print(f"  - {row['table_name']} ({row['table_type']})")
        print()
        print("Metadata:")
        print(f"  Execution time: {metadata['execution_time_seconds']}s")
        print(f"  Bytes processed: {connector._format_bytes(metadata['bytes_processed'])}")
    else:
        print("✗ Query failed")
        print(f"  Error: {metadata['error']}")


def demonstrate_error_handling(connector):
    """Demonstrate error handling for various error types."""
    print("\n" + "=" * 80)
    print("Error Handling Demo")
    print("=" * 80)
    
    # Test 1: Non-existent table
    print("Test 1: Non-existent table...")
    sql = f"SELECT * FROM `{connector.fully_qualified_dataset}.nonexistent_table_12345`"
    results, metadata = connector.execute_query(sql)
    
    if not metadata["success"]:
        print("✓ Error handled gracefully")
        error_preview = metadata['error'][:100] + "..." if len(metadata['error']) > 100 else metadata['error']
        print(f"  Error: {error_preview}")
    print()
    
    # Test 2: Syntax error
    print("Test 2: Syntax error...")
    sql = "SELCT * FROM table"  # typo
    results, metadata = connector.execute_query(sql)
    
    if not metadata["success"]:
        print("✓ Error caught")
        error_preview = metadata['error'][:100] + "..." if len(metadata['error']) > 100 else metadata['error']
        print(f"  Error: {error_preview}")


def demonstrate_table_info(connector):
    """Get metadata for tables in the dataset."""
    print("\n" + "=" * 80)
    print("Table Metadata")
    print("=" * 80)
    
    print("Getting metadata for tables in dataset...")
    print()
    
    # First, get list of tables
    sql = f"""
        SELECT table_name
        FROM `{connector.project_id}.{connector.dataset_id}.INFORMATION_SCHEMA.TABLES`
        LIMIT 3
    """
    
    results, metadata = connector.execute_query(sql)
    
    if metadata["success"] and results:
        for row in results:
            table_name = row['table_name']
            print(f"Table: {table_name}")
            
            info = connector.get_table_info(table_name)
            
            if "error" not in info:
                print(f"  Rows: {info['num_rows']:,}")
                print(f"  Size: {connector._format_bytes(info['num_bytes'])}")
                print(f"  Columns: {info['schema_fields']}")
                print(f"  Created: {info['created']}")
                print(f"  Modified: {info['modified']}")
            else:
                print(f"  Error: {info['error']}")
            print()
    else:
        print("No tables found or query failed")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("Database Connector Demo - Using Application Default Credentials")
    print("=" * 80 + "\n")
    
    print("AUTHENTICATION:")
    print("This demo uses Google Cloud Application Default Credentials (ADC)")
    print("Ensure you have run: gcloud auth application-default login")
    print("=" * 80 + "\n")
    
    try:
        # Test connection
        connector = demonstrate_connection_test()
        
        if connector is None:
            print("\n" + "=" * 80)
            print("Cannot proceed - connector initialization failed")
            print("=" * 80 + "\n")
            sys.exit(1)
        
        print()
        
        if connector.test_connection():
            # Run demonstrations
            demonstrate_simple_query(connector)
            
            demonstrate_syntax_validation(connector)
            
            demonstrate_query_with_data(connector)
            
            demonstrate_table_info(connector)
            
            demonstrate_error_handling(connector)
            
        else:
            print("\n" + "=" * 80)
            print("Cannot proceed - BigQuery connection failed")
            print("Please configure Application Default Credentials:")
            print("  gcloud auth application-default login")
            print("=" * 80 + "\n")
        
        print("\n" + "=" * 80)
        print("Demo Complete")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
