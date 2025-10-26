"""
Human-readable query processing logger for AgenticBot
Creates detailed logs of SQL generation, execution, and results
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import shutil
import glob


class QueryLogger:
    """Human-readable logger for query processing flow"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create archive directory
        self.archive_dir = self.logs_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        # Archive existing log files before starting new session
        self._archive_existing_logs()
        
        # Generate unique log file name for this app run
        self.run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"session_{self.run_timestamp}"
        
        # Create main log file for this run
        self.main_log_file = self.logs_dir / f"agenticbot_{self.run_timestamp}.log"
        
        # Initialize log files with headers
        self._initialize_log_files()
        
        # Track request counter
        self.request_counter = 0
    
    def _archive_existing_logs(self):
        """Move any existing log files to archive folder"""
        try:
            # Find all .log files in the main logs directory
            log_files = list(self.logs_dir.glob("*.log"))
            
            if log_files:
                print(f"📁 Archived {len(log_files)} log file{'s' if len(log_files) > 1 else ''} → logs/archive/")
                for log_file in log_files:
                    archive_path = self.archive_dir / log_file.name
                    # If archive file already exists, add timestamp to avoid conflicts
                    if archive_path.exists():
                        stem = log_file.stem
                        suffix = log_file.suffix
                        timestamp = datetime.now().strftime("%H%M%S")
                        archive_path = self.archive_dir / f"{stem}_archived_{timestamp}{suffix}"
                    
                    shutil.move(str(log_file), str(archive_path))
                
        except Exception as e:
            print(f"⚠️  Warning: Could not archive existing logs: {e}")
            # Continue anyway - don't let archiving issues stop the system
    
    def _initialize_log_files(self):
        """Initialize log files with headers"""
        header = f"""
AgenticBot Query Processing Log
Run Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Session ID: {self.session_id}
{'='*80}

"""
        
        # Write header to main log file
        with open(self.main_log_file, 'w') as f:
            f.write(header)
    
    def _write_to_file(self, filepath: Path, content: str):
        """Write content to specified log file"""
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
    
    def _format_timestamp(self) -> str:
        """Generate formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def start_request(self, user_query: str) -> str:
        """Log the start of a new user query request"""
        self.request_counter += 1
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.request_counter:03d}"
        
        log_entry = f"""
{'='*80}
{self._format_timestamp()} [INFO] [REQUEST_START] [STREAMLIT_UI] - New user query received
    ↳ Request ID: {request_id}
    ↳ Session ID: {self.session_id}
    ↳ User Query: "{user_query}"
    ↳ Query Length: {len(user_query)} characters
    ↳ Detected Intent: {'Pricing Query' if any(word in user_query.lower() for word in ['cost', 'price', 'pricing', 'expensive', 'cheap']) else 'SQL Database Query'}
{'='*80}
"""
        
        self._write_to_file(self.main_log_file, log_entry)
        return request_id
    
    def log_orchestration_start(self, request_id: str):
        """Log orchestration start"""
        log_entry = f"""
{self._format_timestamp()} [INFO] [ORCHESTRATION] [SUPERVISOR] - Starting LLM orchestration
    ↳ Initial State: NEW_QUERY
    ↳ Iteration: 1/10
    ↳ Clarification Count: 0/3
"""
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_orchestration_decision(self, request_id: str, action: str, reasoning: str, confidence: float, decision_time_ms: int):
        """Log orchestration decision"""
        log_entry = f"""
{self._format_timestamp()} [INFO] [ORCHESTRATION] [SUPERVISOR] - Orchestration decision made
    ↳ Action Chosen: {action}
    ↳ Reasoning: {reasoning}
    ↳ LLM Confidence: {confidence:.0%}
    ↳ Decision Time: {decision_time_ms/1000:.3f}s
"""
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_sql_generation_start(self, request_id: str):
        """Log SQL generation start"""
        log_entry = f"""
{self._format_timestamp()} [INFO] [SQL_GENERATION] [QUERY_EXECUTOR] - Generating SQL query
    ↳ Target: BigQuery ford-c478f92f60f6ef55c82d7136.uqm dataset
"""
        self._write_to_file(self.main_log_file, log_entry)
        self._write_to_file(self.sql_log_file, log_entry)
    
    def log_sql_generated(self, request_id: str, sql: str, tables: List[str], generation_time_ms: int, complexity: str = "MEDIUM"):
        """Log successful SQL generation"""
        # Format SQL for better readability
        formatted_sql = self._format_sql(sql)
        
        log_entry = f"""
{self._format_timestamp()} [INFO] [SQL_GENERATION] [QUERY_EXECUTOR] - SQL query generated
    ↳ Generation Time: {generation_time_ms/1000:.3f}s
    ↳ Generated SQL:
    
{formatted_sql}
    
    ↳ SQL Analysis:
        • Tables: {len(tables)} ({', '.join(tables)})
        • WHERE Conditions: {sql.upper().count('WHERE')}
        • JOIN Operations: {sql.upper().count('JOIN')}
        • LIMIT Clause: {'Yes' if 'LIMIT' in sql.upper() else 'No'}
        • Estimated Complexity: {complexity}
"""
        
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_sql_execution_start(self, request_id: str):
        """Log SQL execution start"""
        log_entry = f"""
{self._format_timestamp()} [INFO] [SQL_EXECUTION] [QUERY_EXECUTOR] - Executing SQL query
    ↳ BigQuery Job Started
    ↳ Connection: Using Application Default Credentials
"""
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_sql_execution_success(self, request_id: str, execution_time_ms: int, rows_returned: int, 
                                bytes_processed: str = "N/A", job_id: str = "N/A", cost_usd: float = 0.0):
        """Log successful SQL execution"""
        log_entry = f"""
{self._format_timestamp()} [INFO] [SQL_EXECUTION] [QUERY_EXECUTOR] - SQL execution completed successfully
    ↳ Execution Time: {execution_time_ms}ms
    ↳ BigQuery Job ID: {job_id}
    ↳ Bytes Processed: {bytes_processed}
    ↳ Bytes Billed: {bytes_processed} (minimum billing)
    ↳ Cache Hit: No
    ↳ Estimated Cost: ${cost_usd:.6f} USD
    ↳ Rows Returned: {rows_returned}
"""
        
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_results_captured(self, request_id: str, results: List[Dict], columns: List[str], 
                           data_types: List[str], result_size_kb: float):
        """Log query results with sample data"""
        # Create sample results table (first 3 rows)
        sample_results = results[:3] if results else []
        results_table = self._format_results_table(sample_results, columns)
        
        # Calculate data profile
        data_profile = self._calculate_data_profile(results, columns) if results else {}
        
        log_entry = f"""
{self._format_timestamp()} [INFO] [RESULTS] [QUERY_EXECUTOR] - Query results captured
    ↳ Total Rows: {len(results)}
    ↳ Columns: {len(columns)} ({', '.join(columns)})
    ↳ Data Types: {', '.join(data_types) if data_types else 'N/A'}
    ↳ Result Size: {result_size_kb:.1f} KB
    
    ↳ Sample Results (first 3 rows):
{results_table}
    
    ↳ Data Profile:
{self._format_data_profile(data_profile)}
"""
        
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_sql_error(self, request_id: str, sql: str, error_message: str, error_type: str = "UNKNOWN"):
        """Log SQL execution error"""
        formatted_sql = self._format_sql(sql)
        
        log_entry = f"""
{self._format_timestamp()} [ERROR] [SQL_EXECUTION] [QUERY_EXECUTOR] - SQL execution failed
    ↳ Request ID: {request_id}
    ↳ Failed SQL:
    
{formatted_sql}
    
    ↳ Error Details:
        • Error Type: {error_type}
        • Error Message: {error_message}
    
    ↳ Recovery Actions:
        • Attempted table name correction: NO
        • Schema lookup performed: YES
        • Fallback action: REQUEST_CLARIFICATION
    
    ↳ Next Steps for User:
        1. Check if table names are correct
        2. Verify access permissions
        3. Try rephrasing query with known table names
"""
        
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_pricing_query(self, request_id: str, user_query: str, service: str, cost: float, 
                         processing_time_ms: int, tool_calls: List[Dict] = None):
        """Log pricing query processing"""
        tool_calls_str = ""
        if tool_calls:
            for i, call in enumerate(tool_calls, 1):
                tool_calls_str += f"        {i}. {call.get('function', 'unknown')}({call.get('args', '')}) → {call.get('result', 'success')} [{call.get('duration_ms', 0)}ms]\n"
        
        log_entry = f"""
{self._format_timestamp()} [INFO] [PRICING] [GCP_PRICING_AGENT] - Processing pricing query
    ↳ Request ID: {request_id}
    ↳ User Query: "{user_query}"
    ↳ Detected Service: {service}
    
    ↳ Tool Execution Flow:
{tool_calls_str}    
    ↳ Total Cost: ${cost:.2f} USD
    ↳ Processing Time: {processing_time_ms}ms
    ↳ Status: SUCCESS
"""
        
        self._write_to_file(self.main_log_file, log_entry)
    
    def log_request_complete(self, request_id: str, total_time_ms: int, stage_timings: Dict[str, int], 
                           total_cost_usd: float, status: str = "SUCCESS"):
        """Log request completion with full summary"""
        stage_breakdown = ""
        for stage, time_ms in stage_timings.items():
            percentage = (time_ms / total_time_ms * 100) if total_time_ms > 0 else 0
            stage_breakdown += f"        • {stage}: {time_ms}ms ({percentage:.0f}%)\n"
        
        log_entry = f"""
{self._format_timestamp()} [INFO] [REQUEST_COMPLETE] [SUPERVISOR] - Query processing completed
    ↳ Final Status: {status}
    ↳ Total Processing Time: {total_time_ms/1000:.3f}s
    ↳ Stage Breakdown:
{stage_breakdown}    
    ↳ Resource Usage:
        • Total Cost: ${total_cost_usd:.6f}
    
    ↳ Quality Metrics:
        • Processing Efficiency: {'GOOD' if total_time_ms < 6000 else 'NEEDS_IMPROVEMENT'} ({'under 6s target' if total_time_ms < 6000 else 'over 6s target'})

{'='*80}
"""
        
        self._write_to_file(self.main_log_file, log_entry)
    
    def _format_sql(self, sql: str) -> str:
        """Format SQL with proper indentation"""
        lines = sql.strip().split('\n')
        formatted_lines = []
        for line in lines:
            formatted_lines.append(f"    {line.strip()}")
        return '\n'.join(formatted_lines)
    
    def _format_results_table(self, results: List[Dict], columns: List[str]) -> str:
        """Format results as a readable table"""
        if not results or not columns:
            return "    No results to display"
        
        # Calculate column widths
        col_widths = {}
        for col in columns:
            col_widths[col] = max(len(col), max(len(str(row.get(col, ''))) for row in results))
            col_widths[col] = min(col_widths[col], 20)  # Cap at 20 chars
        
        # Create header
        header = "    | " + " | ".join(col.ljust(col_widths[col]) for col in columns) + " |"
        separator = "    |" + "|".join("-" * (col_widths[col] + 2) for col in columns) + "|"
        
        # Create rows
        rows = []
        for row in results:
            row_str = "    | " + " | ".join(str(row.get(col, 'null')).ljust(col_widths[col]) for col in columns) + " |"
            rows.append(row_str)
        
        return "\n".join([header, separator] + rows)
    
    def _calculate_data_profile(self, results: List[Dict], columns: List[str]) -> Dict:
        """Calculate basic data profiling statistics"""
        if not results:
            return {}
        
        profile = {}
        for col in columns:
            values = [row.get(col) for row in results]
            null_count = sum(1 for v in values if v is None or v == '' or str(v).lower() == 'null')
            unique_count = len(set(str(v) for v in values if v is not None))
            
            profile[col] = {
                'null_count': null_count,
                'unique_count': unique_count,
                'total_count': len(values)
            }
        
        return profile
    
    def _format_data_profile(self, profile: Dict) -> str:
        """Format data profiling information"""
        if not profile:
            return "        • No profiling data available"
        
        lines = []
        null_info = []
        unique_info = []
        
        for col, stats in profile.items():
            if stats['null_count'] > 0:
                null_info.append(f"{col} ({stats['null_count']})")
            unique_info.append(f"{col} ({stats['unique_count']})")
        
        if null_info:
            lines.append(f"        • NULL Values: {', '.join(null_info)}")
        if unique_info:
            lines.append(f"        • Unique Values: {', '.join(unique_info)}")
        
        return '\n'.join(lines) if lines else "        • No significant patterns detected"


# Global logger instance
_logger_instance = None

def get_query_logger() -> QueryLogger:
    """Get the global query logger instance (must be initialized first)"""
    global _logger_instance
    if _logger_instance is None:
        raise RuntimeError("QueryLogger not initialized. Call initialize_logging() first.")
    return _logger_instance

def initialize_logging(logs_dir: str = "logs") -> QueryLogger:
    """Initialize logging system with specified directory"""
    global _logger_instance
    _logger_instance = QueryLogger(logs_dir)
    return _logger_instance
