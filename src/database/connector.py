"""
BigQuery Database Connector Module

Handles all BigQuery database operations using Application Default Credentials (ADC).
This module provides a simple interface for executing SQL queries against BigQuery
with comprehensive error handling and metadata collection.

Authentication:
    Uses Google Cloud Application Default Credentials (ADC). No need to manage
    credential files in code - ADC automatically discovers credentials from:
    - Local: gcloud auth application-default login
    - Production: Service account attached to compute resources

Setup:
    For local development, run:
        gcloud auth application-default login
    
    For production, ensure service account is attached or GOOGLE_APPLICATION_CREDENTIALS
    environment variable points to service account key file.
"""

import os
import logging
import time
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple

from google.cloud import bigquery
from google.cloud import exceptions as google_exceptions
from google.api_core import exceptions as api_exceptions
from google.auth import exceptions as auth_exceptions
from dotenv import load_dotenv

# Setup module-level logger
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    Manage BigQuery connections and execute SQL queries with proper error handling.
    
    This class uses Application Default Credentials (ADC) for authentication,
    eliminating the need to manage credential files in code. All configuration
    is read from environment variables.
    
    Example:
        >>> connector = DatabaseConnector()
        >>> if connector.test_connection():
        ...     sql = "SELECT CURRENT_DATE() as today"
        ...     results, metadata = connector.execute_query(sql)
        ...     if metadata["success"]:
        ...         print(f"Rows: {len(results)}")
    """
    
    def __init__(self):
        """
        Initialize the DatabaseConnector.
        
        Configuration is loaded from environment variables:
        - GCP_PROJECT_ID: Google Cloud project ID (required)
        - BQ_DATASET_ID: BigQuery dataset name (required)
        
        Authentication uses Application Default Credentials (ADC) automatically.
        
        Raises:
            ValueError: If required environment variables are not set
        """
        # Load environment variables
        load_dotenv()
        
        # Get required configuration
        self.project_id = os.getenv('GCP_PROJECT_ID')
        if not self.project_id:
            raise ValueError(
                "GCP_PROJECT_ID not found in environment variables. Set it in .env file."
            )
        
        self.dataset_id = os.getenv('BQ_DATASET_ID')
        if not self.dataset_id:
            raise ValueError(
                "BQ_DATASET_ID not found in environment variables. Set it in .env file."
            )
        
        # Client will be created lazily
        self.client: Optional[bigquery.Client] = None
        
        logger.info(
            f"DatabaseConnector initialized for project: {self.project_id}, "
            f"dataset: {self.dataset_id}"
        )
        logger.info("Using Application Default Credentials for authentication")
    
    def get_client(self) -> bigquery.Client:
        """
        Get or create BigQuery client using Application Default Credentials.
        
        The client is created lazily on first use and reused for subsequent calls.
        ADC automatically discovers credentials without requiring explicit configuration.
        
        Returns:
            BigQuery client instance
            
        Raises:
            DefaultCredentialsError: If ADC is not configured
            Exception: If client creation fails for other reasons
        """
        if self.client is not None:
            return self.client
        
        try:
            # Create client - ADC is used automatically
            self.client = bigquery.Client(project=self.project_id)
            logger.info("BigQuery client created using Application Default Credentials")
            return self.client
            
        except auth_exceptions.DefaultCredentialsError as e:
            logger.error("Failed to create BigQuery client. Ensure Application Default Credentials are configured.")
            logger.error("Run: gcloud auth application-default login")
            raise
        except Exception as e:
            logger.error(f"Failed to create BigQuery client: {e}")
            raise
    
    def execute_query(
        self,
        sql: str,
        timeout: int = 30
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute SQL query and return results with metadata.
        
        Args:
            sql: The SQL query string to execute
            timeout: Maximum execution time in seconds (default 30)
            
        Returns:
            Tuple of (results_list, metadata_dict) where:
            - results_list: List of dictionaries, one per row
            - metadata_dict: Dictionary with execution details including:
                - success (bool): Whether query succeeded
                - row_count (int): Number of rows returned
                - execution_time_seconds (float): Query execution time
                - bytes_processed (int): Bytes processed by BigQuery
                - bytes_billed (int): Bytes billed by BigQuery
                - error (str or None): Error message if failed
                - query_id (str): BigQuery job ID
                
        Example:
            >>> connector = DatabaseConnector()
            >>> sql = "SELECT * FROM `project.dataset.table` LIMIT 10"
            >>> results, metadata = connector.execute_query(sql, timeout=30)
            >>> if metadata["success"]:
            ...     for row in results:
            ...         print(row)  # Each row is a dictionary
        """
        start_time = time.time()
        
        try:
            # Get BigQuery client
            client = self.get_client()
            
            # Create job configuration
            job_config = bigquery.QueryJobConfig()
            
            # Execute query
            sql_preview = sql[:100] + "..." if len(sql) > 100 else sql
            logger.info(f"Executing SQL query: {sql_preview}")
            
            query_job = client.query(sql, job_config=job_config)
            
            # Wait for results with timeout
            try:
                result_iterator = query_job.result(timeout=timeout)
            except (TimeoutError, concurrent.futures.TimeoutError) as e:
                execution_time = time.time() - start_time
                metadata = {
                    "success": False,
                    "row_count": 0,
                    "execution_time_seconds": round(execution_time, 3),
                    "bytes_processed": 0,
                    "bytes_billed": 0,
                    "error": "Query timeout exceeded",
                    "query_id": query_job.job_id if query_job else None
                }
                logger.error(f"Query timeout exceeded after {timeout}s")
                return ([], metadata)
            
            # Convert results to list of dictionaries
            results = []
            for row in result_iterator:
                row_dict = {}
                for key, value in row.items():
                    # Handle non-JSON-serializable types
                    if value is None:
                        row_dict[key] = None
                    elif hasattr(value, 'isoformat'):  # datetime/date objects
                        row_dict[key] = value.isoformat()
                    elif isinstance(value, (bytes, bytearray)):
                        row_dict[key] = value.decode('utf-8', errors='ignore')
                    elif hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                        # Convert Decimal to float
                        row_dict[key] = float(value)
                    else:
                        row_dict[key] = value
                results.append(row_dict)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Get BigQuery job statistics
            total_bytes_processed = query_job.total_bytes_processed or 0
            total_bytes_billed = query_job.total_bytes_billed or 0
            
            # Build metadata
            metadata = {
                "success": True,
                "row_count": len(results),
                "execution_time_seconds": round(execution_time, 3),
                "bytes_processed": total_bytes_processed,
                "bytes_billed": total_bytes_billed,
                "error": None,
                "query_id": query_job.job_id
            }
            
            logger.info(
                f"Query executed successfully: {len(results)} rows in {execution_time:.3f}s"
            )
            
            return (results, metadata)
            
        except google_exceptions.BadRequest as e:
            # SQL syntax error or invalid query
            execution_time = time.time() - start_time
            metadata = {
                "success": False,
                "row_count": 0,
                "execution_time_seconds": round(execution_time, 3),
                "bytes_processed": 0,
                "bytes_billed": 0,
                "error": str(e),
                "query_id": None
            }
            logger.error(f"Query failed with BadRequest: {e}")
            return ([], metadata)
            
        except api_exceptions.Forbidden as e:
            # Permission denied
            execution_time = time.time() - start_time
            metadata = {
                "success": False,
                "row_count": 0,
                "execution_time_seconds": round(execution_time, 3),
                "bytes_processed": 0,
                "bytes_billed": 0,
                "error": "Permission denied. Check BigQuery access permissions for your credentials.",
                "query_id": None
            }
            logger.error(f"Permission denied: {e}")
            return ([], metadata)
            
        except auth_exceptions.DefaultCredentialsError as e:
            # ADC not configured
            execution_time = time.time() - start_time
            metadata = {
                "success": False,
                "row_count": 0,
                "execution_time_seconds": round(execution_time, 3),
                "bytes_processed": 0,
                "bytes_billed": 0,
                "error": "Application Default Credentials not found. Run: gcloud auth application-default login",
                "query_id": None
            }
            logger.error("Application Default Credentials not found")
            logger.error("Run: gcloud auth application-default login")
            logger.error(f"Error details: {e}")
            return ([], metadata)
            
        except Exception as e:
            # Catch-all for unexpected errors
            execution_time = time.time() - start_time
            metadata = {
                "success": False,
                "row_count": 0,
                "execution_time_seconds": round(execution_time, 3),
                "bytes_processed": 0,
                "bytes_billed": 0,
                "error": str(e),
                "query_id": None
            }
            logger.error(f"Unexpected error executing query: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ([], metadata)
    
    def validate_sql_syntax(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL syntax without executing the query (dry run).
        
        This performs a BigQuery dry run to check if the SQL is syntactically
        correct and references valid tables/columns without actually executing it.
        
        Args:
            sql: The SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message) where:
            - is_valid: True if SQL is valid, False otherwise
            - error_message: Error description if invalid, None if valid
            
        Example:
            >>> connector = DatabaseConnector()
            >>> is_valid, error = connector.validate_sql_syntax("SELECT * FROM table")
            >>> if not is_valid:
            ...     print(f"Invalid SQL: {error}")
        """
        try:
            client = self.get_client()
            
            # Create job configuration with dry_run enabled
            job_config = bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False
            )
            
            logger.debug(f"Validating SQL syntax: {sql[:100]}...")
            
            # Execute dry run
            client.query(sql, job_config=job_config)
            
            logger.debug("SQL syntax validation successful")
            return (True, None)
            
        except google_exceptions.BadRequest as e:
            # Extract error message
            error_message = str(e)
            logger.debug(f"SQL syntax validation failed: {error_message}")
            return (False, error_message)
            
        except Exception as e:
            logger.debug(f"SQL syntax validation error: {e}")
            return (False, str(e))
    
    def test_connection(self) -> bool:
        """
        Test if BigQuery connection works with Application Default Credentials.
        
        Executes a simple query to verify that ADC is properly configured
        and the client can connect to BigQuery.
        
        Returns:
            True if connection successful, False otherwise
            
        Example:
            >>> connector = DatabaseConnector()
            >>> if connector.test_connection():
            ...     print("✓ Connected to BigQuery using ADC")
            ... else:
            ...     print("✗ Connection failed - check ADC setup")
        """
        try:
            client = self.get_client()
            
            # Execute simple test query
            query = "SELECT 1 AS test"
            query_job = client.query(query)
            result = query_job.result()
            
            logger.info("BigQuery connection test successful with Application Default Credentials")
            return True
            
        except auth_exceptions.DefaultCredentialsError as e:
            logger.error("Application Default Credentials not found. Run: gcloud auth application-default login")
            logger.error(f"Error: {e}")
            return False
            
        except Exception as e:
            logger.error(f"BigQuery connection test failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get metadata about a specific table.
        
        Args:
            table_name: Name of table (without project/dataset prefix)
            
        Returns:
            Dictionary with table metadata including:
            - table_name: Name of the table
            - num_rows: Number of rows in table
            - num_bytes: Size in bytes
            - created: Creation timestamp (ISO format)
            - modified: Last modified timestamp (ISO format)
            - schema_fields: Number of columns
            
        Example:
            >>> connector = DatabaseConnector()
            >>> info = connector.get_table_info("my_table")
            >>> print(f"Rows: {info['num_rows']}, Size: {info['num_bytes']} bytes")
        """
        try:
            client = self.get_client()
            
            # Build fully qualified table ID
            table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
            
            # Get table
            table = client.get_table(table_id)
            
            info = {
                "table_name": table_name,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "created": table.created.isoformat() if table.created else None,
                "modified": table.modified.isoformat() if table.modified else None,
                "schema_fields": len(table.schema)
            }
            
            return info
            
        except google_exceptions.NotFound:
            logger.error(f"Table not found: {table_name}")
            return {"error": "Table not found"}
            
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {"error": str(e)}
    
    def _format_bytes(self, bytes_count: int) -> str:
        """
        Format bytes into human-readable string.
        
        Args:
            bytes_count: Number of bytes
            
        Returns:
            Formatted string like "1.5 MB"
        """
        if bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 ** 2:
            return f"{bytes_count / 1024:.2f} KB"
        elif bytes_count < 1024 ** 3:
            return f"{bytes_count / (1024 ** 2):.2f} MB"
        else:
            return f"{bytes_count / (1024 ** 3):.2f} GB"
    
    @property
    def fully_qualified_dataset(self) -> str:
        """
        Get fully qualified dataset name.
        
        Returns:
            String in format "project_id.dataset_id"
        """
        return f"{self.project_id}.{self.dataset_id}"
    
    @property
    def is_connected(self) -> bool:
        """
        Check if BigQuery client has been initialized.
        
        Returns:
            True if client exists, False otherwise
        """
        return self.client is not None
