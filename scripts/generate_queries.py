#!/usr/bin/env python3
"""
BigQuery Query Generator Script

Reads schema.json and automatically generates test queries covering
different patterns and complexity levels.
"""

import json
import os
import sys
import logging
from typing import Dict, List, Any

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryGenerator:
    """Generates test SQL queries based on discovered BigQuery schema."""
    
    def __init__(self, schema_path: str = "config/schema.json"):
        """
        Initialize the query generator with schema file.
        
        Args:
            schema_path: Path to the schema JSON file
        """
        self.schema_path = schema_path
        
        # Validate schema file exists
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        # Load and parse schema
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            logger.info(f"Loaded schema from {schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
        
        # Extract key information
        self.project_id = self.schema.get('project_id', '')
        self.database = self.schema.get('database', '')
        self.tables = self.schema.get('tables', [])
        self.relationships = self.schema.get('relationships', [])
        self.business_glossary = self.schema.get('business_glossary', {})
        
        if not self.tables:
            raise ValueError("Schema contains no tables")
        
        logger.info(f"Schema loaded: {len(self.tables)} tables, {len(self.relationships)} relationships")
    
    def _get_full_table_name(self, table_name: str) -> str:
        """
        Generate fully qualified table name with backticks.
        
        Args:
            table_name: Simple table name
            
        Returns:
            Fully qualified table name
        """
        return f"`{self.project_id}.{self.database}.{table_name}`"
    
    def find_numeric_columns(self) -> List[Dict]:
        """
        Find all numeric columns across all tables.
        
        Returns:
            List of dictionaries with table_name, column_name, data_type
        """
        numeric_types = ['INT64', 'FLOAT64', 'NUMERIC', 'BIGNUMERIC', 'INTEGER', 'FLOAT']
        numeric_columns = []
        
        for table in self.tables:
            for column in table.get('columns', []):
                if column['type'] in numeric_types:
                    numeric_columns.append({
                        'table_name': table['name'],
                        'column_name': column['name'],
                        'data_type': column['type']
                    })
        
        logger.info(f"Found {len(numeric_columns)} numeric columns")
        return numeric_columns
    
    def find_date_columns(self) -> List[Dict]:
        """
        Find all date/time columns across all tables.
        
        Returns:
            List of dictionaries with table_name, column_name, data_type
        """
        date_types = ['DATE', 'DATETIME', 'TIMESTAMP', 'TIME']
        date_columns = []
        
        for table in self.tables:
            for column in table.get('columns', []):
                if column['type'] in date_types:
                    date_columns.append({
                        'table_name': table['name'],
                        'column_name': column['name'],
                        'data_type': column['type']
                    })
        
        logger.info(f"Found {len(date_columns)} date/time columns")
        return date_columns
    
    def find_categorical_columns(self) -> List[Dict]:
        """
        Find STRING columns that are likely categorical (good for GROUP BY).
        
        Returns:
            List of dictionaries with table_name, column_name
        """
        categorical_keywords = [
            'status', 'category', 'type', 'country', 'region', 'state',
            'city', 'gender', 'level', 'priority', 'grade', 'class'
        ]
        categorical_columns = []
        
        for table in self.tables:
            for column in table.get('columns', []):
                if column['type'] == 'STRING':
                    col_lower = column['name'].lower()
                    if any(keyword in col_lower for keyword in categorical_keywords):
                        categorical_columns.append({
                            'table_name': table['name'],
                            'column_name': column['name']
                        })
        
        logger.info(f"Found {len(categorical_columns)} categorical columns")
        return categorical_columns
    
    def generate_count_queries(self) -> List[Dict]:
        """
        Generate various count queries.
        
        Returns:
            List of query dictionaries
        """
        queries = []
        
        if not self.tables:
            return queries
        
        # Query 1: Count all records in first table
        first_table = self.tables[0]
        queries.append({
            'id': None,  # Will be assigned later
            'user_query': f"How many {first_table['name'].replace('insurance_', '')} records do we have?",
            'expected_sql': f"SELECT COUNT(*) as total_count FROM {self._get_full_table_name(first_table['name'])}",
            'expected_result_type': 'single_value',
            'description': f"Count all records in {first_table['name']} table",
            'difficulty': 'easy',
            'tags': ['count', 'basic']
        })
        
        # Query 2: Count distinct values in a categorical column
        categorical_cols = self.find_categorical_columns()
        if categorical_cols:
            col_info = categorical_cols[0]
            table_name = col_info['table_name']
            column_name = col_info['column_name']
            queries.append({
                'id': None,
                'user_query': f"How many unique {column_name.replace('_', ' ')} values are there?",
                'expected_sql': f"SELECT COUNT(DISTINCT {column_name}) as unique_count FROM {self._get_full_table_name(table_name)}",
                'expected_result_type': 'single_value',
                'description': f"Count distinct values in {column_name}",
                'difficulty': 'easy',
                'tags': ['count', 'distinct']
            })
        
        # Query 3: Count with date filter
        date_cols = self.find_date_columns()
        if date_cols:
            col_info = date_cols[0]
            table_name = col_info['table_name']
            column_name = col_info['column_name']
            queries.append({
                'id': None,
                'user_query': f"How many {table_name.replace('insurance_', '')} records from the last 30 days?",
                'expected_sql': f"SELECT COUNT(*) as recent_count FROM {self._get_full_table_name(table_name)} WHERE {column_name} >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)",
                'expected_result_type': 'single_value',
                'description': f"Count records from last 30 days using partition-optimized query",
                'difficulty': 'medium',
                'tags': ['count', 'date_filter', 'partition_optimized']
            })
        
        # Query 4: Count grouped by categorical column
        if categorical_cols:
            col_info = categorical_cols[0]
            table_name = col_info['table_name']
            column_name = col_info['column_name']
            queries.append({
                'id': None,
                'user_query': f"Show me the count of records by {column_name.replace('_', ' ')}",
                'expected_sql': f"SELECT {column_name}, COUNT(*) as count FROM {self._get_full_table_name(table_name)} GROUP BY {column_name} ORDER BY count DESC",
                'expected_result_type': 'table',
                'description': f"Count records grouped by {column_name}",
                'difficulty': 'medium',
                'tags': ['count', 'group_by', 'aggregation']
            })
        
        # Query 5: Count with multiple conditions
        if len(self.tables) > 1 and categorical_cols and date_cols:
            cat_col = categorical_cols[0]
            date_col = date_cols[0]
            # Use same table if both columns are from same table, otherwise use first table with conditions
            if cat_col['table_name'] == date_col['table_name']:
                table_name = cat_col['table_name']
                cat_column = cat_col['column_name']
                date_column = date_col['column_name']
                queries.append({
                    'id': None,
                    'user_query': f"Count recent {table_name.replace('insurance_', '')} records by {cat_column.replace('_', ' ')}",
                    'expected_sql': f"SELECT {cat_column}, COUNT(*) as count FROM {self._get_full_table_name(table_name)} WHERE {date_column} >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) GROUP BY {cat_column} ORDER BY count DESC",
                    'expected_result_type': 'table',
                    'description': f"Count with multiple conditions: date filter and grouping",
                    'difficulty': 'medium',
                    'tags': ['count', 'multiple_conditions', 'group_by', 'date_filter']
                })
        
        logger.info(f"Generated {len(queries)} count queries")
        return queries
    
    def generate_select_queries(self) -> List[Dict]:
        """
        Generate various SELECT queries.
        
        Returns:
            List of query dictionaries
        """
        queries = []
        
        if not self.tables:
            return queries
        
        first_table = self.tables[0]
        columns = first_table.get('columns', [])
        
        # Query 1: Select all from table (limited)
        queries.append({
            'id': None,
            'user_query': f"Show me some sample {first_table['name'].replace('insurance_', '')} records",
            'expected_sql': f"SELECT * FROM {self._get_full_table_name(first_table['name'])} LIMIT 10",
            'expected_result_type': 'table',
            'description': f"Select all columns with limit",
            'difficulty': 'easy',
            'tags': ['select', 'basic', 'limit']
        })
        
        # Query 2: Select specific columns
        if len(columns) >= 3:
            selected_cols = [col['name'] for col in columns[:3]]
            col_list = ', '.join(selected_cols)
            queries.append({
                'id': None,
                'user_query': f"Show me {', '.join([c.replace('_', ' ') for c in selected_cols])} from {first_table['name'].replace('insurance_', '')}",
                'expected_sql': f"SELECT {col_list} FROM {self._get_full_table_name(first_table['name'])} LIMIT 100",
                'expected_result_type': 'table',
                'description': f"Select specific columns",
                'difficulty': 'easy',
                'tags': ['select', 'specific_columns']
            })
        
        # Query 3: Select with WHERE filter
        categorical_cols = self.find_categorical_columns()
        if categorical_cols:
            col_info = categorical_cols[0]
            table_name = col_info['table_name']
            column_name = col_info['column_name']
            # Use a sample value from schema if available
            sample_value = 'active'  # Generic placeholder
            queries.append({
                'id': None,
                'user_query': f"Show me all {table_name.replace('insurance_', '')} where {column_name.replace('_', ' ')} is active",
                'expected_sql': f"SELECT * FROM {self._get_full_table_name(table_name)} WHERE {column_name} = '{sample_value}' LIMIT 100",
                'expected_result_type': 'table',
                'description': f"Select with WHERE condition",
                'difficulty': 'easy',
                'tags': ['select', 'where', 'filter']
            })
        
        # Query 4: Select with ORDER BY
        if columns:
            order_col = columns[0]['name']
            queries.append({
                'id': None,
                'user_query': f"Show me {first_table['name'].replace('insurance_', '')} sorted by {order_col.replace('_', ' ')}",
                'expected_sql': f"SELECT * FROM {self._get_full_table_name(first_table['name'])} ORDER BY {order_col} DESC LIMIT 50",
                'expected_result_type': 'table',
                'description': f"Select with ORDER BY",
                'difficulty': 'easy',
                'tags': ['select', 'order_by', 'sort']
            })
        
        # Query 5: Select with multiple conditions
        date_cols = self.find_date_columns()
        if date_cols and categorical_cols:
            date_col = date_cols[0]
            cat_col = categorical_cols[0]
            if date_col['table_name'] == cat_col['table_name']:
                table_name = date_col['table_name']
                queries.append({
                    'id': None,
                    'user_query': f"Show recent {table_name.replace('insurance_', '')} records that are active",
                    'expected_sql': f"SELECT * FROM {self._get_full_table_name(table_name)} WHERE {date_col['column_name']} >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) AND {cat_col['column_name']} = 'active' LIMIT 100",
                    'expected_result_type': 'table',
                    'description': f"Select with multiple WHERE conditions",
                    'difficulty': 'medium',
                    'tags': ['select', 'where', 'multiple_conditions', 'date_filter']
                })
        
        logger.info(f"Generated {len(queries)} select queries")
        return queries
    
    def generate_date_filter_queries(self) -> List[Dict]:
        """
        Generate queries with date filtering.
        
        Returns:
            List of query dictionaries
        """
        queries = []
        date_cols = self.find_date_columns()
        
        if not date_cols:
            logger.warning("No date columns found, skipping date filter queries")
            return queries
        
        col_info = date_cols[0]
        table_name = col_info['table_name']
        column_name = col_info['column_name']
        full_table = self._get_full_table_name(table_name)
        
        # Query 1: Records from last month
        queries.append({
            'id': None,
            'user_query': f"Show me {table_name.replace('insurance_', '')} from last month",
            'expected_sql': f"SELECT * FROM {full_table} WHERE {column_name} >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH) LIMIT 100",
            'expected_result_type': 'table',
            'description': f"Records from last month using DATE_SUB",
            'difficulty': 'medium',
            'tags': ['date_filter', 'relative_date', 'partition_optimized']
        })
        
        # Query 2: Records from this year
        queries.append({
            'id': None,
            'user_query': f"What {table_name.replace('insurance_', '')} do we have from this year?",
            'expected_sql': f"SELECT * FROM {full_table} WHERE EXTRACT(YEAR FROM {column_name}) = EXTRACT(YEAR FROM CURRENT_DATE()) LIMIT 100",
            'expected_result_type': 'table',
            'description': f"Records from current year using EXTRACT",
            'difficulty': 'medium',
            'tags': ['date_filter', 'extract', 'year']
        })
        
        # Query 3: Records between two dates
        queries.append({
            'id': None,
            'user_query': f"Show {table_name.replace('insurance_', '')} between January and March 2024",
            'expected_sql': f"SELECT * FROM {full_table} WHERE {column_name} BETWEEN '2024-01-01' AND '2024-03-31' LIMIT 100",
            'expected_result_type': 'table',
            'description': f"Records between specific date range",
            'difficulty': 'medium',
            'tags': ['date_filter', 'between', 'date_range']
        })
        
        # Query 4: Records from last N days
        queries.append({
            'id': None,
            'user_query': f"Show me {table_name.replace('insurance_', '')} from the last 7 days",
            'expected_sql': f"SELECT * FROM {full_table} WHERE {column_name} >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) ORDER BY {column_name} DESC LIMIT 100",
            'expected_result_type': 'table',
            'description': f"Recent records with partition optimization",
            'difficulty': 'medium',
            'tags': ['date_filter', 'recent', 'partition_optimized']
        })
        
        # Query 5: Records grouped by month
        queries.append({
            'id': None,
            'user_query': f"How many {table_name.replace('insurance_', '')} per month this year?",
            'expected_sql': f"SELECT DATE_TRUNC({column_name}, MONTH) as month, COUNT(*) as count FROM {full_table} WHERE EXTRACT(YEAR FROM {column_name}) = EXTRACT(YEAR FROM CURRENT_DATE()) GROUP BY month ORDER BY month",
            'expected_result_type': 'table',
            'description': f"Group by month for current year",
            'difficulty': 'hard',
            'tags': ['date_filter', 'group_by', 'date_trunc', 'aggregation']
        })
        
        logger.info(f"Generated {len(queries)} date filter queries")
        return queries
    
    def generate_aggregation_queries(self) -> List[Dict]:
        """
        Generate queries with aggregations.
        
        Returns:
            List of query dictionaries
        """
        queries = []
        numeric_cols = self.find_numeric_columns()
        
        if not numeric_cols:
            logger.warning("No numeric columns found, skipping aggregation queries")
            return queries
        
        col_info = numeric_cols[0]
        table_name = col_info['table_name']
        column_name = col_info['column_name']
        full_table = self._get_full_table_name(table_name)
        
        # Query 1: SUM of numeric column
        queries.append({
            'id': None,
            'user_query': f"What is the total {column_name.replace('_', ' ')}?",
            'expected_sql': f"SELECT SUM({column_name}) as total_{column_name} FROM {full_table}",
            'expected_result_type': 'single_value',
            'description': f"Sum of {column_name}",
            'difficulty': 'easy',
            'tags': ['aggregation', 'sum']
        })
        
        # Query 2: AVG of numeric column
        queries.append({
            'id': None,
            'user_query': f"What is the average {column_name.replace('_', ' ')}?",
            'expected_sql': f"SELECT AVG({column_name}) as avg_{column_name} FROM {full_table}",
            'expected_result_type': 'single_value',
            'description': f"Average of {column_name}",
            'difficulty': 'easy',
            'tags': ['aggregation', 'average']
        })
        
        # Query 3: MAX and MIN
        queries.append({
            'id': None,
            'user_query': f"What are the minimum and maximum {column_name.replace('_', ' ')} values?",
            'expected_sql': f"SELECT MIN({column_name}) as min_{column_name}, MAX({column_name}) as max_{column_name} FROM {full_table}",
            'expected_result_type': 'single_row',
            'description': f"Min and max values",
            'difficulty': 'easy',
            'tags': ['aggregation', 'min', 'max']
        })
        
        # Query 4: GROUP BY with COUNT
        categorical_cols = self.find_categorical_columns()
        if categorical_cols:
            cat_col = [c for c in categorical_cols if c['table_name'] == table_name]
            if cat_col:
                cat_column = cat_col[0]['column_name']
                queries.append({
                    'id': None,
                    'user_query': f"Count {table_name.replace('insurance_', '')} by {cat_column.replace('_', ' ')}",
                    'expected_sql': f"SELECT {cat_column}, COUNT(*) as count FROM {full_table} GROUP BY {cat_column} ORDER BY count DESC",
                    'expected_result_type': 'table',
                    'description': f"Count grouped by category",
                    'difficulty': 'medium',
                    'tags': ['aggregation', 'group_by', 'count']
                })
        
        # Query 5: Multiple aggregations
        if categorical_cols:
            cat_col = [c for c in categorical_cols if c['table_name'] == table_name]
            if cat_col:
                cat_column = cat_col[0]['column_name']
                queries.append({
                    'id': None,
                    'user_query': f"Show me statistics of {column_name.replace('_', ' ')} by {cat_column.replace('_', ' ')}",
                    'expected_sql': f"SELECT {cat_column}, COUNT(*) as count, SUM({column_name}) as total, AVG({column_name}) as average, MIN({column_name}) as minimum, MAX({column_name}) as maximum FROM {full_table} GROUP BY {cat_column} ORDER BY total DESC",
                    'expected_result_type': 'table',
                    'description': f"Multiple aggregations with grouping",
                    'difficulty': 'hard',
                    'tags': ['aggregation', 'group_by', 'multiple_metrics']
                })
        
        logger.info(f"Generated {len(queries)} aggregation queries")
        return queries
    
    def generate_join_queries(self) -> List[Dict]:
        """
        Generate queries with JOINs based on relationships.
        
        Returns:
            List of query dictionaries
        """
        queries = []
        
        if not self.relationships:
            logger.warning("No relationships found, skipping join queries")
            return queries
        
        # Find many-to-one relationships for joins
        many_to_one = [r for r in self.relationships if r['type'] == 'many-to-one']
        
        if not many_to_one:
            logger.warning("No many-to-one relationships found")
            return queries
        
        # Query 1: Simple 2-table join
        rel = many_to_one[0]
        from_parts = rel['from'].split('.')
        to_parts = rel['to'].split('.')
        from_table = from_parts[0]
        from_col = from_parts[1]
        to_table = to_parts[0]
        to_col = to_parts[1]
        
        # Get some columns from both tables
        from_table_obj = next((t for t in self.tables if t['name'] == from_table), None)
        to_table_obj = next((t for t in self.tables if t['name'] == to_table), None)
        
        if from_table_obj and to_table_obj:
            from_cols = [c['name'] for c in from_table_obj['columns'][:3]]
            to_cols = [c['name'] for c in to_table_obj['columns'][:2] if c['name'] != to_col]
            
            select_cols = [f"t1.{c}" for c in from_cols] + [f"t2.{c}" for c in to_cols]
            
            queries.append({
                'id': None,
                'user_query': f"Show me {from_table.replace('insurance_', '')} with their {to_table.replace('insurance_', '')} information",
                'expected_sql': f"SELECT {', '.join(select_cols)} FROM {self._get_full_table_name(from_table)} t1 INNER JOIN {self._get_full_table_name(to_table)} t2 ON t1.{from_col} = t2.{to_col} LIMIT 100",
                'expected_result_type': 'table',
                'description': f"Inner join between {from_table} and {to_table}",
                'difficulty': 'medium',
                'tags': ['join', 'inner_join', 'two_tables']
            })
        
        # Query 2: Join with aggregation
        if from_table_obj:
            queries.append({
                'id': None,
                'user_query': f"How many {from_table.replace('insurance_', '')} does each {to_table.replace('insurance_', '')} have?",
                'expected_sql': f"SELECT t2.{to_cols[0] if to_cols else 'name'}, COUNT(*) as count FROM {self._get_full_table_name(from_table)} t1 INNER JOIN {self._get_full_table_name(to_table)} t2 ON t1.{from_col} = t2.{to_col} GROUP BY t2.{to_cols[0] if to_cols else 'name'} ORDER BY count DESC",
                'expected_result_type': 'table',
                'description': f"Count with join and grouping",
                'difficulty': 'hard',
                'tags': ['join', 'aggregation', 'group_by']
            })
        
        # Query 3: Multi-table join (3 tables)
        if len(many_to_one) >= 2:
            rel2 = many_to_one[1]
            from_parts2 = rel2['from'].split('.')
            to_parts2 = rel2['to'].split('.')
            
            # Check if we can create a 3-table join (both rels share a table)
            if from_parts2[0] == from_table:
                to_table2 = to_parts2[0]
                to_col2 = to_parts2[1]
                from_col2 = from_parts2[1]
                
                queries.append({
                    'id': None,
                    'user_query': f"Show me {from_table.replace('insurance_', '')} with their {to_table.replace('insurance_', '')} and {to_table2.replace('insurance_', '')} details",
                    'expected_sql': f"SELECT t1.*, t2.name as {to_table.replace('insurance_', '')}_name, t3.name as {to_table2.replace('insurance_', '')}_name FROM {self._get_full_table_name(from_table)} t1 INNER JOIN {self._get_full_table_name(to_table)} t2 ON t1.{from_col} = t2.{to_col} INNER JOIN {self._get_full_table_name(to_table2)} t3 ON t1.{from_col2} = t3.{to_col2} LIMIT 100",
                    'expected_result_type': 'table',
                    'description': f"Three-table join with multiple relationships",
                    'difficulty': 'hard',
                    'tags': ['join', 'inner_join', 'multi_table', 'complex']
                })
        
        # Query 4: LEFT JOIN (include unmatched records)
        if from_table_obj and to_table_obj:
            queries.append({
                'id': None,
                'user_query': f"Show all {from_table.replace('insurance_', '')} including those without {to_table.replace('insurance_', '')}",
                'expected_sql': f"SELECT t1.*, t2.name FROM {self._get_full_table_name(from_table)} t1 LEFT JOIN {self._get_full_table_name(to_table)} t2 ON t1.{from_col} = t2.{to_col} LIMIT 100",
                'expected_result_type': 'table',
                'description': f"Left join to include all records from {from_table}",
                'difficulty': 'medium',
                'tags': ['join', 'left_join', 'outer_join']
            })
        
        # Query 5: Join with date filter and aggregation
        date_cols = self.find_date_columns()
        numeric_cols = self.find_numeric_columns()
        
        date_in_from = [d for d in date_cols if d['table_name'] == from_table]
        numeric_in_from = [n for n in numeric_cols if n['table_name'] == from_table]
        
        if date_in_from and numeric_in_from and to_table_obj:
            date_col = date_in_from[0]['column_name']
            num_col = numeric_in_from[0]['column_name']
            to_name_col = to_cols[0] if to_cols else 'name'
            
            queries.append({
                'id': None,
                'user_query': f"Show me total {num_col.replace('_', ' ')} by {to_table.replace('insurance_', '')} for last 90 days",
                'expected_sql': f"SELECT t2.{to_name_col}, SUM(t1.{num_col}) as total_{num_col}, COUNT(*) as count FROM {self._get_full_table_name(from_table)} t1 INNER JOIN {self._get_full_table_name(to_table)} t2 ON t1.{from_col} = t2.{to_col} WHERE t1.{date_col} >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY) GROUP BY t2.{to_name_col} ORDER BY total_{num_col} DESC",
                'expected_result_type': 'table',
                'description': f"Complex join with date filter and aggregation",
                'difficulty': 'hard',
                'tags': ['join', 'aggregation', 'date_filter', 'group_by', 'complex']
            })
        
        logger.info(f"Generated {len(queries)} join queries")
        return queries
    
    def generate_all_queries(self) -> List[Dict]:
        """
        Generate all types of queries and combine them.
        
        Returns:
            Complete list of queries with sequential IDs
        """
        logger.info("=" * 60)
        logger.info("Starting query generation...")
        logger.info("=" * 60)
        
        all_queries = []
        
        # Generate different types of queries
        all_queries.extend(self.generate_count_queries())
        all_queries.extend(self.generate_select_queries())
        all_queries.extend(self.generate_date_filter_queries())
        all_queries.extend(self.generate_aggregation_queries())
        all_queries.extend(self.generate_join_queries())
        
        # Assign sequential IDs
        for idx, query in enumerate(all_queries, start=1):
            query['id'] = idx
        
        logger.info("=" * 60)
        logger.info(f"Query generation complete! Total: {len(all_queries)} queries")
        logger.info("=" * 60)
        
        return all_queries
    
    def save_queries(self, queries: List[Dict], output_path: str = "config/query_examples.json"):
        """
        Save generated queries to a JSON file.
        
        Args:
            queries: List of query dictionaries
            output_path: Path to output file
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"Created directory: {output_dir}")
            
            # Create output structure
            output = {
                "metadata": {
                    "total_queries": len(queries),
                    "database": self.database,
                    "project_id": self.project_id,
                    "generated_from_schema": self.schema_path
                },
                "queries": queries
            }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✓ Queries saved successfully to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save queries to {output_path}: {e}")
            raise
    
    def run(self):
        """
        Main method that orchestrates query generation.
        """
        try:
            logger.info("Starting query generation...")
            
            # Generate all queries
            queries = self.generate_all_queries()
            
            if not queries:
                raise ValueError("No queries were generated")
            
            # Save queries
            self.save_queries(queries)
            
            # Print summary
            print("\n" + "=" * 60)
            print("QUERY GENERATION SUMMARY")
            print("=" * 60)
            print(f"✓ Total queries generated: {len(queries)}")
            print(f"✓ Output file: config/query_examples.json")
            print("=" * 60)
            
            # Count by difficulty
            difficulty_counts = {}
            for q in queries:
                diff = q.get('difficulty', 'unknown')
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
            print("\nQuery Distribution by Difficulty:")
            for difficulty, count in sorted(difficulty_counts.items()):
                print(f"  • {difficulty.capitalize()}: {count} queries")
            
            # Count by tag
            tag_counts = {}
            for q in queries:
                for tag in q.get('tags', []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            print("\nTop Query Types:")
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  • {tag}: {count} queries")
            
            print("\n" + "=" * 60)
            print("NEXT STEPS:")
            print("  1. Review config/query_examples.json")
            print("  2. Adjust queries for your specific use cases")
            print("  3. Test queries against your BigQuery dataset")
            print("  4. Add more custom queries as needed")
            print("=" * 60 + "\n")
            
            logger.info("Query generation complete!")
            
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            raise


if __name__ == "__main__":
    try:
        generator = QueryGenerator()
        generator.run()
        print("\n✓ SUCCESS: Test queries have been generated and saved to config/query_examples.json")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ ERROR: Query generation failed: {e}")
        logger.exception("Full error traceback:")
        sys.exit(1)
