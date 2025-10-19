#!/usr/bin/env python3
"""
BigQuery Schema Discovery Script

Automatically connects to BigQuery, discovers all tables and columns,
infers relationships, and generates schema.json file.
"""

import json
import os
import sys
import logging
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError
from dotenv import load_dotenv

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SchemaDiscoverer:
    """Discovers BigQuery schema and generates comprehensive schema documentation."""
    
    def __init__(self):
        """Initialize the schema discoverer with environment configuration."""
        # Load environment variables
        load_dotenv()
        
        # Get required environment variables
        self.project_id = os.getenv('GCP_PROJECT_ID')
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        self.dataset_id = os.getenv('BQ_DATASET_ID')
        if not self.dataset_id:
            raise ValueError("BQ_DATASET_ID environment variable is required")
        
        # Validate ADC is configured
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {credentials_path}"
            )
        
        # Create BigQuery client using ADC
        try:
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"Successfully authenticated to project: {self.project_id}")
        except DefaultCredentialsError as e:
            logger.error("Application Default Credentials (ADC) not found or invalid")
            logger.error("Please run: gcloud auth application-default login")
            raise ValueError(
                "ADC authentication required. Run 'gcloud auth application-default login' first."
            ) from e
        
        # Initialize storage
        self.discovered_tables: Dict[str, Dict] = {}
        self.foreign_keys: Dict[str, List[Dict]] = {}
        self.table_metadata: Dict[str, Dict] = {}
        
        logger.info(f"Initialized schema discovery for dataset: {self.dataset_id}")
    
    def discover_tables(self) -> List[str]:
        """
        Query INFORMATION_SCHEMA to get all tables in the dataset.
        
        Returns:
            List of table names
        """
        try:
            query = f"""
                SELECT table_name
                FROM `{self.project_id}.{self.dataset_id}.INFORMATION_SCHEMA.TABLES`
                WHERE table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            
            logger.info(f"Discovering tables in {self.dataset_id}...")
            query_job = self.client.query(query)
            results = query_job.result()
            
            tables = [row.table_name for row in results]
            logger.info(f"Discovered {len(tables)} tables: {', '.join(tables)}")
            
            return tables
            
        except Exception as e:
            logger.error(f"Failed to discover tables: {e}")
            raise
    
    def discover_table_metadata(self, table_name: str) -> Dict[str, Any]:
        """
        Discover table-level metadata including partitioning and clustering.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table metadata
        """
        try:
            query = f"""
                SELECT
                    table_name,
                    ddl
                FROM `{self.project_id}.{self.dataset_id}.INFORMATION_SCHEMA.TABLES`
                WHERE table_name = @table_name
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("table_name", "STRING", table_name)
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            metadata = {
                "partitioning": None,
                "clustering": []
            }
            
            if results:
                ddl = results[0].ddl
                
                # Parse DDL for partitioning info
                if "PARTITION BY" in ddl:
                    # Extract partitioning field
                    partition_start = ddl.find("PARTITION BY")
                    partition_section = ddl[partition_start:partition_start + 200]
                    
                    if "DATE(" in partition_section:
                        field_start = partition_section.find("DATE(") + 5
                        field_end = partition_section.find(")", field_start)
                        field = partition_section[field_start:field_end].strip()
                        metadata["partitioning"] = {
                            "type": "DAY",
                            "field": field
                        }
                
                # Parse DDL for clustering info
                if "CLUSTER BY" in ddl:
                    cluster_start = ddl.find("CLUSTER BY") + 10
                    # Find the end of clustering section (next keyword or OPTIONS)
                    cluster_end = ddl.find("OPTIONS", cluster_start)
                    if cluster_end == -1:
                        cluster_end = ddl.find(";", cluster_start)
                    if cluster_end == -1:
                        cluster_end = len(ddl)
                    
                    cluster_section = ddl[cluster_start:cluster_end].strip()
                    # Remove trailing characters and split by comma
                    cluster_fields = [f.strip() for f in cluster_section.split(",")]
                    metadata["clustering"] = cluster_fields
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Could not retrieve metadata for {table_name}: {e}")
            return {"partitioning": None, "clustering": []}
    
    def discover_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Query INFORMATION_SCHEMA to get all columns for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column dictionaries
        """
        try:
            query = f"""
                SELECT
                    column_name,
                    data_type,
                    is_nullable
                FROM `{self.project_id}.{self.dataset_id}.INFORMATION_SCHEMA.COLUMNS`
                WHERE table_name = @table_name
                ORDER BY ordinal_position
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("table_name", "STRING", table_name)
                ]
            )
            
            logger.info(f"Discovering columns for table: {table_name}")
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            columns = []
            for row in results:
                column = {
                    "name": row.column_name,
                    "type": row.data_type,
                    "nullable": row.is_nullable == "YES",
                    "primary_key": False,
                    "description": ""
                }
                columns.append(column)
            
            logger.info(f"Discovered {len(columns)} columns for {table_name}")
            return columns
            
        except Exception as e:
            logger.error(f"Failed to discover columns for {table_name}: {e}")
            raise
    
    def infer_primary_keys(self, table_name: str, columns: List[Dict]) -> List[Dict]:
        """
        Infer primary keys based on naming patterns and data types.
        
        Args:
            table_name: Name of the table
            columns: List of column dictionaries
            
        Returns:
            Updated columns list with primary_key flags set
        """
        pk_patterns = [
            lambda col: col["name"] == "id",
            lambda col: col["name"].endswith("_id") and col["name"] == f"{table_name}_id",
            lambda col: col["name"].endswith("_key"),
        ]
        
        identified_pks = []
        
        for column in columns:
            # Check if column type is suitable for primary key
            if column["type"] in ["INT64", "STRING", "NUMERIC"]:
                for pattern in pk_patterns:
                    if pattern(column):
                        column["primary_key"] = True
                        identified_pks.append(column["name"])
                        break
        
        if identified_pks:
            logger.info(f"Identified potential primary keys for {table_name}: {', '.join(identified_pks)}")
        
        return columns
    
    def infer_foreign_keys(self) -> Dict[str, List[Dict]]:
        """
        Infer foreign key relationships by analyzing column names and matching with other tables.
        
        Returns:
            Dictionary mapping table names to list of foreign key relationships
        """
        logger.info("Inferring foreign key relationships...")
        
        foreign_keys = defaultdict(list)
        table_names = list(self.discovered_tables.keys())
        
        # Get table prefix from environment
        table_prefix = os.getenv('BQ_TABLE_PREFIX', '')
        
        for table_name, table_info in self.discovered_tables.items():
            primary_keys = [col["name"] for col in table_info["columns"] if col["primary_key"]]
            
            for column in table_info["columns"]:
                col_name = column["name"]
                
                # Skip if this is a primary key
                if col_name in primary_keys:
                    continue
                
                # Check if column name ends with _id (potential foreign key)
                if col_name.endswith("_id"):
                    # Extract the referenced table name
                    base_name = col_name[:-3]  # Remove '_id'
                    
                    # Try to find matching table
                    potential_tables = [
                        f"{table_prefix}{base_name}",  # e.g., policy_id -> insurance_policies
                        f"{table_prefix}{base_name}s",  # Try plural
                        f"{table_prefix}{base_name}es",  # Try plural with 'es'
                        base_name,  # Try without prefix
                        f"{base_name}s",  # Try without prefix, plural
                    ]
                    
                    for potential_table in potential_tables:
                        if potential_table in table_names and potential_table != table_name:
                            # Found a matching table!
                            # Determine the referenced column (usually 'id' or table_name + '_id')
                            ref_table_pks = [
                                col["name"] 
                                for col in self.discovered_tables[potential_table]["columns"] 
                                if col["primary_key"]
                            ]
                            
                            ref_column = ref_table_pks[0] if ref_table_pks else "id"
                            
                            fk_relationship = {
                                "column": col_name,
                                "references_table": potential_table,
                                "references_column": ref_column
                            }
                            
                            foreign_keys[table_name].append(fk_relationship)
                            logger.info(
                                f"Found FK: {table_name}.{col_name} -> {potential_table}.{ref_column}"
                            )
                            break
        
        logger.info(f"Discovered {sum(len(fks) for fks in foreign_keys.values())} foreign key relationships")
        return dict(foreign_keys)
    
    def discover_sample_data(self, table_name: str, limit: int = 10) -> List[Dict]:
        """
        Query sample rows from a table to understand data patterns.
        
        Args:
            table_name: Name of the table
            limit: Maximum number of rows to retrieve
            
        Returns:
            List of sample row dictionaries
        """
        try:
            query = f"""
                SELECT *
                FROM `{self.project_id}.{self.dataset_id}.{table_name}`
                LIMIT @limit
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("limit", "INT64", limit)
                ]
            )
            
            logger.info(f"Retrieving sample data from {table_name}...")
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            sample_data = []
            for row in results:
                # Convert Row to dictionary, handling various data types
                row_dict = {}
                for key, value in row.items():
                    # Convert non-serializable types to JSON-compatible formats
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
                sample_data.append(row_dict)
            
            logger.info(f"Retrieved {len(sample_data)} sample rows from {table_name}")
            return sample_data
            
        except Exception as e:
            logger.warning(f"Could not retrieve sample data from {table_name}: {e}")
            return []
    
    def infer_relationships(self) -> List[Dict]:
        """
        Infer relationships between tables including many-to-many relationships.
        
        Returns:
            List of relationship dictionaries
        """
        logger.info("Inferring table relationships...")
        
        relationships = []
        
        # Direct foreign key relationships (one-to-many, many-to-one)
        for source_table, fk_list in self.foreign_keys.items():
            for fk in fk_list:
                target_table = fk["references_table"]
                source_col = fk["column"]
                target_col = fk["references_column"]
                
                # Many-to-one relationship (from child to parent)
                relationships.append({
                    "type": "many-to-one",
                    "from": f"{source_table}.{source_col}",
                    "to": f"{target_table}.{target_col}",
                    "description": f"Each {source_table} references a {target_table}"
                })
                
                # One-to-many relationship (from parent to child) - inverse
                relationships.append({
                    "type": "one-to-many",
                    "from": f"{target_table}.{target_col}",
                    "to": f"{source_table}.{source_col}",
                    "description": f"Each {target_table} can have multiple {source_table} records"
                })
        
        # Detect many-to-many relationships (junction tables)
        # A junction table typically has 2+ foreign keys and few other columns
        for table_name, fk_list in self.foreign_keys.items():
            if len(fk_list) >= 2:
                # Check if this looks like a junction table
                total_columns = len(self.discovered_tables[table_name]["columns"])
                fk_count = len(fk_list)
                
                # If most columns are foreign keys, likely a junction table
                if fk_count >= 2 and (fk_count / total_columns) > 0.4:
                    # Create many-to-many relationship between the two main tables
                    table1 = fk_list[0]["references_table"]
                    table2 = fk_list[1]["references_table"]
                    
                    relationships.append({
                        "type": "many-to-many",
                        "from": table1,
                        "to": table2,
                        "through": table_name,
                        "description": f"{table1} and {table2} have a many-to-many relationship through {table_name}"
                    })
                    
                    logger.info(f"Detected many-to-many: {table1} <-> {table2} (via {table_name})")
        
        logger.info(f"Inferred {len(relationships)} relationships")
        return relationships
    
    def generate_business_glossary(self) -> Dict[str, Any]:
        """
        Generate a business glossary with common terms and synonyms.
        
        Returns:
            Dictionary with business terms and their synonyms
        """
        logger.info("Generating business glossary...")
        
        # Default business terms
        glossary = {
            "terms": {
                "customer": ["client", "buyer", "user", "account", "policyholder"],
                "order": ["purchase", "transaction", "sale"],
                "product": ["item", "sku", "merchandise", "policy"],
                "revenue": ["sales", "income", "amount", "total", "premium"],
                "date": ["time", "timestamp", "when", "period"],
                "claim": ["claims", "incident", "loss", "damage"],
                "agent": ["broker", "representative", "salesperson"],
                "policy": ["policies", "contract", "coverage", "plan"],
                "status": ["state", "condition", "stage"],
            },
            "phrases": {
                "recent": "last 30 days",
                "active": "has activity in last 90 days",
                "pending": "not yet processed or approved",
                "approved": "verified and accepted"
            }
        }
        
        # Analyze discovered tables and columns to suggest synonyms
        discovered_terms = {}
        
        for table_name in self.discovered_tables.keys():
            # Extract base term from table name (remove prefix)
            table_prefix = os.getenv('BQ_TABLE_PREFIX', '')
            base_term = table_name.replace(table_prefix, '') if table_prefix else table_name
            
            # Add table as a term
            if base_term not in discovered_terms:
                discovered_terms[base_term] = []
            
            # Analyze columns for additional terms
            for column in self.discovered_tables[table_name]["columns"]:
                col_name = column["name"]
                
                # Extract meaningful terms (skip common suffixes)
                if not any(col_name.endswith(suffix) for suffix in ["_id", "_date", "_at", "_by"]):
                    if col_name not in discovered_terms:
                        discovered_terms[col_name] = []
        
        # Merge discovered terms into glossary
        glossary["discovered_entities"] = discovered_terms
        
        logger.info(f"Generated glossary with {len(glossary['terms'])} standard terms and {len(discovered_terms)} discovered entities")
        
        return glossary
    
    def build_schema(self) -> Dict[str, Any]:
        """
        Build the complete schema by orchestrating all discovery methods.
        
        Returns:
            Complete schema dictionary
        """
        logger.info("=" * 60)
        logger.info("Starting comprehensive schema discovery...")
        logger.info("=" * 60)
        
        # Discover all tables
        table_names = self.discover_tables()
        
        if not table_names:
            raise ValueError(f"No tables found in dataset {self.dataset_id}")
        
        # Build detailed table information
        tables = []
        for table_name in table_names:
            # Get columns
            columns = self.discover_columns(table_name)
            
            # Infer primary keys
            columns = self.infer_primary_keys(table_name, columns)
            
            # Get table metadata (partitioning, clustering)
            metadata = self.discover_table_metadata(table_name)
            
            # Get sample data
            sample_data = self.discover_sample_data(table_name, limit=5)
            
            # Build table dictionary
            table_info = {
                "name": table_name,
                "description": "",  # To be filled manually
                "columns": columns,
                "sample_data": sample_data
            }
            
            # Add partitioning info if present
            if metadata["partitioning"]:
                table_info["partitioning"] = metadata["partitioning"]
            
            # Add clustering info if present
            if metadata["clustering"]:
                table_info["clustering"] = metadata["clustering"]
            
            tables.append(table_info)
            self.discovered_tables[table_name] = table_info
        
        # Infer foreign keys
        self.foreign_keys = self.infer_foreign_keys()
        
        # Infer relationships
        relationships = self.infer_relationships()
        
        # Generate business glossary
        business_glossary = self.generate_business_glossary()
        
        # Build final schema
        schema = {
            "database": self.dataset_id,
            "database_type": "bigquery",
            "project_id": self.project_id,
            "tables": tables,
            "relationships": relationships,
            "business_glossary": business_glossary
        }
        
        logger.info("=" * 60)
        logger.info("Schema discovery completed successfully!")
        logger.info("=" * 60)
        
        return schema
    
    def save_schema(self, schema: Dict[str, Any], output_path: str = "config/schema.json"):
        """
        Save the schema to a JSON file.
        
        Args:
            schema: Complete schema dictionary
            output_path: Path to output file
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"Created directory: {output_dir}")
            
            # Write schema to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, sort_keys=True, ensure_ascii=False)
            
            logger.info(f"✓ Schema saved successfully to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save schema to {output_path}: {e}")
            raise
    
    def run(self):
        """
        Main method that orchestrates the entire schema discovery process.
        """
        try:
            logger.info("Starting BigQuery schema discovery...")
            
            # Build complete schema
            schema = self.build_schema()
            
            # Validate schema has at least one table
            if not schema.get("tables"):
                raise ValueError("No tables discovered - schema is empty")
            
            # Save schema
            self.save_schema(schema)
            
            # Print summary
            print("\n" + "=" * 60)
            print("SCHEMA DISCOVERY SUMMARY")
            print("=" * 60)
            print(f"✓ Tables discovered: {len(schema['tables'])}")
            print(f"✓ Relationships found: {len(schema['relationships'])}")
            print(f"✓ Output file: config/schema.json")
            print("=" * 60)
            print("\nTable Details:")
            for table in schema['tables']:
                print(f"\n  • {table['name']}")
                print(f"    - Columns: {len(table['columns'])}")
                if table.get('partitioning'):
                    print(f"    - Partitioned by: {table['partitioning']['field']} ({table['partitioning']['type']})")
                if table.get('clustering'):
                    print(f"    - Clustered by: {', '.join(table['clustering'])}")
                print(f"    - Sample rows: {len(table.get('sample_data', []))}")
            
            print("\n" + "=" * 60)
            print("NEXT STEPS:")
            print("  1. Review config/schema.json")
            print("  2. Add meaningful descriptions for tables and columns")
            print("  3. Verify inferred relationships are correct")
            print("  4. Enhance business glossary with domain-specific terms")
            print("=" * 60 + "\n")
            
            logger.info("Schema discovery complete!")
            
        except Exception as e:
            logger.error(f"Schema discovery failed: {e}")
            raise


if __name__ == "__main__":
    try:
        discoverer = SchemaDiscoverer()
        discoverer.run()
        print("\n✓ SUCCESS: Schema has been discovered and saved to config/schema.json")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ ERROR: Schema discovery failed: {e}")
        logger.exception("Full error traceback:")
        sys.exit(1)
