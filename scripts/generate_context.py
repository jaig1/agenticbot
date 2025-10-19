#!/usr/bin/env python3
"""
Generate System Context for LLM

Loads schema.json and query_examples.json, then generates a comprehensive
system context file optimized for LLM consumption. The output is human-readable
markdown that can be compressed and sent to an LLM as static context.
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> dict:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path.absolute()}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_system_context(schema_data: dict, query_examples_data: dict) -> str:
    """
    Generate comprehensive system context from schema and query examples.
    
    Args:
        schema_data: Schema configuration dictionary
        query_examples_data: Query examples dictionary
        
    Returns:
        Complete system context as markdown string
    """
    context_parts = []
    
    # Header
    context_parts.append("# BigQuery SQL Generation System Context\n\n")
    context_parts.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Introduction
    context_parts.append("## Role and Task\n\n")
    context_parts.append(
        "You are an expert BigQuery SQL generator with complete knowledge of the database schema below. "
        "Your task is to convert natural language queries into accurate, optimized BigQuery SQL.\n\n"
    )
    
    # Database Info
    project_id = schema_data.get("project_id", "unknown")
    database = schema_data.get("database", "unknown")
    db_type = schema_data.get("database_type", "unknown")
    
    context_parts.append("## Database Information\n\n")
    context_parts.append(f"- **Project ID:** `{project_id}`\n")
    context_parts.append(f"- **Dataset:** `{database}`\n")
    context_parts.append(f"- **Type:** {db_type}\n\n")
    
    # Tables and Columns
    context_parts.append("## Schema: Tables and Columns\n\n")
    
    for table in schema_data.get("tables", []):
        table_name = table["name"]
        table_desc = table.get("description", "No description")
        
        context_parts.append(f"### `{table_name}`\n\n")
        
        if table_desc:
            context_parts.append(f"{table_desc}\n\n")
        
        # Partitioning
        if "partitioning" in table and table["partitioning"]:
            part = table["partitioning"]
            context_parts.append(
                f"**Partitioning:** {part.get('type')} on `{part.get('field')}`\n\n"
            )
        
        # Clustering
        if "clustering" in table and table["clustering"]:
            cluster_fields = ", ".join([f"`{c}`" for c in table["clustering"]])
            context_parts.append(f"**Clustering:** {cluster_fields}\n\n")
        
        # Columns
        context_parts.append("**Columns:**\n\n")
        context_parts.append("| Column | Type | Nullable | Constraints | Description |\n")
        context_parts.append("|--------|------|----------|-------------|-------------|\n")
        
        for col in table.get("columns", []):
            col_name = col["name"]
            col_type = col["type"]
            nullable = "Yes" if col.get("nullable", True) else "No"
            constraints = []
            
            if col.get("primary_key", False):
                constraints.append("PK")
            
            constraints_str = ", ".join(constraints) if constraints else "-"
            description = col.get("description", "-")
            
            context_parts.append(
                f"| `{col_name}` | {col_type} | {nullable} | {constraints_str} | {description} |\n"
            )
        
        context_parts.append("\n")
    
    # Relationships
    context_parts.append("## Relationships\n\n")
    
    relationships = schema_data.get("relationships", [])
    if relationships:
        for rel in relationships:
            rel_type = rel.get("type", "unknown").upper()
            rel_from = rel.get("from", "unknown")
            rel_to = rel.get("to", "unknown")
            rel_desc = rel.get("description", "")
            
            context_parts.append(f"- **{rel_type}:** `{rel_from}` → `{rel_to}`\n")
            
            if rel_desc:
                context_parts.append(f"  - {rel_desc}\n")
            
            if "through" in rel:
                context_parts.append(f"  - Junction table: `{rel['through']}`\n")
        
        context_parts.append("\n")
    else:
        context_parts.append("No relationships defined.\n\n")
    
    # Business Glossary
    context_parts.append("## Business Terminology\n\n")
    context_parts.append(
        "Map these business terms to appropriate database columns:\n\n"
    )
    
    glossary = schema_data.get("business_glossary", {})
    
    # Standard terms
    if "terms" in glossary:
        context_parts.append("**Standard Terms:**\n\n")
        for term, synonyms in glossary["terms"].items():
            if isinstance(synonyms, list) and synonyms:
                syn_str = ", ".join(synonyms)
                context_parts.append(f"- **{term}:** {syn_str}\n")
        context_parts.append("\n")
    
    # Phrases
    if "phrases" in glossary:
        context_parts.append("**Common Phrases:**\n\n")
        for phrase, meaning in glossary["phrases"].items():
            context_parts.append(f"- **{phrase}:** {meaning}\n")
        context_parts.append("\n")
    
    # BigQuery Guidelines
    context_parts.append("## BigQuery SQL Guidelines\n\n")
    context_parts.append("**Table Names:**\n")
    context_parts.append(f"- Always use fully qualified: `` `{project_id}.{database}.table_name` ``\n\n")
    
    context_parts.append("**Date Functions:**\n")
    context_parts.append("- Current date: `CURRENT_DATE()`\n")
    context_parts.append("- Date arithmetic: `DATE_SUB()`, `DATE_ADD()`, `DATE_TRUNC()`\n")
    context_parts.append("- Extract parts: `EXTRACT(YEAR FROM date_column)`\n\n")
    
    context_parts.append("**String Functions:**\n")
    context_parts.append("- `CONCAT()`, `UPPER()`, `LOWER()`, `SUBSTR()`\n\n")
    
    context_parts.append("**Aggregations:**\n")
    context_parts.append("- `SUM()`, `COUNT()`, `AVG()`, `MAX()`, `MIN()`\n\n")
    
    context_parts.append("**Performance:**\n")
    context_parts.append("- Use partition keys in WHERE clauses for partitioned tables\n")
    context_parts.append("- Leverage clustered columns for filtering\n")
    context_parts.append("- Use table aliases for readability\n")
    context_parts.append("- Include LIMIT when appropriate\n\n")
    
    # Example Queries
    context_parts.append("## Example Queries\n\n")
    context_parts.append(
        "Reference these examples for query patterns and syntax:\n\n"
    )
    
    queries = query_examples_data.get("queries", [])
    
    # Group by difficulty for better organization
    easy_queries = [q for q in queries if q.get("difficulty") == "easy"]
    medium_queries = [q for q in queries if q.get("difficulty") == "medium"]
    hard_queries = [q for q in queries if q.get("difficulty") == "hard"]
    
    for difficulty, query_list in [
        ("Easy", easy_queries),
        ("Medium", medium_queries),
        ("Hard", hard_queries)
    ]:
        if not query_list:
            continue
        
        context_parts.append(f"### {difficulty} Queries\n\n")
        
        for query in query_list:
            query_id = query.get("id", "")
            user_query = query.get("user_query", "")
            expected_sql = query.get("expected_sql", "")
            description = query.get("description", "")
            tags = query.get("tags", [])
            
            context_parts.append(f"**Example {query_id}:** {user_query}\n\n")
            
            if description:
                context_parts.append(f"*{description}*\n\n")
            
            context_parts.append("```sql\n")
            context_parts.append(f"{expected_sql}\n")
            context_parts.append("```\n\n")
            
            if tags:
                tags_str = ", ".join([f"`{t}`" for t in tags])
                context_parts.append(f"Tags: {tags_str}\n\n")
            
            context_parts.append("---\n\n")
    
    # Output Instructions
    context_parts.append("## Output Format\n\n")
    context_parts.append("When generating SQL:\n\n")
    context_parts.append("1. Return **ONLY** the SQL query\n")
    context_parts.append("2. Do **NOT** include markdown code blocks\n")
    context_parts.append("3. Do **NOT** include explanations unless requested\n")
    context_parts.append("4. Ensure query is executable and syntactically correct\n")
    context_parts.append("5. Use exact table and column names from schema\n")
    context_parts.append("6. Apply JOINs when multiple tables needed\n")
    context_parts.append("7. Optimize for performance using partitions and clusters\n")
    
    return "".join(context_parts)


def save_context(context: str, output_path: Path):
    """
    Save context to file.
    
    Args:
        context: Context string to save
        output_path: Path to output file
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(context)
    
    logger.info(f"Context saved to: {output_path.absolute()}")


def main():
    """Main execution function."""
    try:
        logger.info("Starting system context generation...")
        
        # Define paths
        schema_path = Path("config/schema.json")
        query_examples_path = Path("config/query_examples.json")
        output_path = Path("config/systemcontext.md")
        
        # Load schema
        logger.info(f"Loading schema from {schema_path}...")
        schema_data = load_json_file(schema_path)
        table_count = len(schema_data.get("tables", []))
        logger.info(f"Schema loaded: {table_count} tables")
        
        # Load query examples
        logger.info(f"Loading query examples from {query_examples_path}...")
        query_examples_data = load_json_file(query_examples_path)
        query_count = len(query_examples_data.get("queries", []))
        logger.info(f"Query examples loaded: {query_count} queries")
        
        # Generate context
        logger.info("Generating system context...")
        context = generate_system_context(schema_data, query_examples_data)
        
        context_size = len(context)
        estimated_tokens = context_size // 4
        logger.info(f"Context generated: {context_size} characters (~{estimated_tokens} tokens)")
        
        # Save context
        save_context(context, output_path)
        
        # Print summary
        print("\n" + "=" * 60)
        print("SYSTEM CONTEXT GENERATION SUMMARY")
        print("=" * 60)
        print(f"✓ Tables: {table_count}")
        print(f"✓ Relationships: {len(schema_data.get('relationships', []))}")
        print(f"✓ Example queries: {query_count}")
        print(f"✓ Context size: {context_size} characters (~{estimated_tokens} tokens)")
        print(f"✓ Output: {output_path.absolute()}")
        print("=" * 60)
        print("\nContext is ready for LLM consumption!")
        print("=" * 60 + "\n")
        
        logger.info("System context generation complete!")
        
    except Exception as e:
        logger.error(f"Failed to generate system context: {e}")
        raise


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
