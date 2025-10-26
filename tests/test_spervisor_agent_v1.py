#!/usr/bin/env python3
"""
Test Script for Supervisor Agent v1 - Dynamic Question Loading with Pricing Agent Integration

This test script dynamically loads questions from config/sample_questions.md
and tests the Supervisor Agent's orchestration capabilities with real-world
automotive manufacturing queries and GCP pricing queries.

Features:
- Dynamic question loading from markdown file (no hardcoded questions)
- Comprehensive testing of LLM-driven orchestration
- Integrated testing of GCP Pricing Agent
- 5 verified pricing questions for testing pricing agent integration
- Detailed test reporting and metrics
- Error handling and validation
- Support for different question categories and difficulty levels

Usage:
    # Test all questions (default behavior)
    python tests/test_spervisor_agent_v1.py
    
    # Test limited number of questions
    python tests/test_spervisor_agent_v1.py --max-questions 10
    
    # Test specific category only
    python tests/test_spervisor_agent_v1.py --category "Vehicle Inventory"
    
    # Set custom success rate threshold
    python tests/test_spervisor_agent_v1.py --min-success-rate 90.0
    
Requirements:
    - config/sample_questions.md must exist
    - All environment variables must be configured
    - BigQuery access must be available
"""

import os
import sys
import re
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.supervisor import SupervisorAgent
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupervisorAgentTester:
    """
    Comprehensive test suite for Supervisor Agent using dynamic question loading.
    """
    
    def __init__(self):
        """Initialize the tester with supervisor agent and question loader."""
        load_dotenv()
        
        # File paths
        self.project_root = Path(__file__).parent.parent
        self.sample_questions_file = self.project_root / "config" / "sample_questions.md"
        
        # Test results storage
        self.test_results = []
        self.test_metrics = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'error_tests': 0,
            'skipped_tests': 0,
            'total_time': 0,
            'avg_response_time': 0
        }
        
        # Initialize supervisor agent (with GCP Pricing Agent integration)
        self.supervisor = None
        self._initialize_supervisor()
    
    def _initialize_supervisor(self):
        """Initialize the supervisor agent with error handling."""
        try:
            logger.info("🚀 Initializing Supervisor Agent...")
            self.supervisor = SupervisorAgent(orchestration_model="gemini-2.5-flash-lite")
            logger.info("✅ Supervisor Agent initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supervisor Agent: {e}")
            raise
    
    def load_questions_from_markdown(self) -> List[Dict[str, Any]]:
        """
        Dynamically load questions from sample_questions.md file.
        
        Returns:
            List of question dictionaries with metadata
        """
        if not self.sample_questions_file.exists():
            raise FileNotFoundError(f"Sample questions file not found: {self.sample_questions_file}")
        
        logger.info(f"📖 Loading questions from: {self.sample_questions_file}")
        
        questions = []
        current_category = "Unknown"
        current_difficulty = "Unknown"
        
        with open(self.sample_questions_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Track categories from headers
            if line.startswith('### '):
                current_category = line[4:].strip()
                # Extract difficulty from category if present
                if 'Easy' in current_category:
                    current_difficulty = 'Easy'
                elif 'Medium' in current_category:
                    current_difficulty = 'Medium'
                elif 'Hard' in current_category:
                    current_difficulty = 'Hard'
                else:
                    current_difficulty = 'Unknown'
            
            # Extract questions from bullet points
            if line.startswith('- "') and line.endswith('"'):
                question_text = line[3:-1]  # Remove '- "' and '"'
                
                questions.append({
                    'question': question_text,
                    'category': current_category,
                    'difficulty': current_difficulty,
                    'line_number': line_num,
                    'source': 'sample_questions.md'
                })
        
        logger.info(f"✅ Loaded {len(questions)} questions from markdown file")
        
        # Add verified pricing questions for testing the pricing agent integration
        pricing_questions = self.get_pricing_test_questions()
        questions.extend(pricing_questions)
        
        logger.info(f"✅ Total questions (including {len(pricing_questions)} pricing tests): {len(questions)}")
        
        # Log question breakdown by category
        category_counts = {}
        for q in questions:
            category = q['category']
            category_counts[category] = category_counts.get(category, 0) + 1
        
        logger.info("📊 Question distribution by category:")
        for category, count in category_counts.items():
            logger.info(f"   {category}: {count} questions")
        
        return questions
    
    def get_pricing_test_questions(self) -> List[Dict[str, Any]]:
        """
        Get the 5 verified pricing questions for testing the pricing agent integration.
        
        Returns:
            List of verified pricing questions
        """
        pricing_questions = [
            {
                'question': 'How much does 3 million Gemini input tokens cost?',
                'category': 'GCP Pricing - Gemini',
                'difficulty': 'Easy',
                'line_number': 0,
                'source': 'verified_pricing_questions',
                'expected_cost': 1.50
            },
            {
                'question': 'What is the cost for 1000 Cloud Functions invocations?',
                'category': 'GCP Pricing - Cloud Functions', 
                'difficulty': 'Easy',
                'line_number': 0,
                'source': 'verified_pricing_questions',
                'expected_cost': 0.00
            },
            {
                'question': 'What is the cost for processing 10 million Gemini input tokens?',
                'category': 'GCP Pricing - Gemini',
                'difficulty': 'Medium',
                'line_number': 0,
                'source': 'verified_pricing_questions',
                'expected_cost': 5.00
            },
            {
                'question': 'How much do 10000 Cloud Functions invocations cost?',
                'category': 'GCP Pricing - Cloud Functions',
                'difficulty': 'Medium', 
                'line_number': 0,
                'source': 'verified_pricing_questions',
                'expected_cost': 0.00
            },
            {
                'question': 'How much does 5 million Gemini input tokens cost?',
                'category': 'GCP Pricing - Gemini',
                'difficulty': 'Easy',
                'line_number': 0,
                'source': 'verified_pricing_questions',
                'expected_cost': 2.50
            }
        ]
        
        logger.info(f"✅ Added {len(pricing_questions)} verified pricing test questions")
        return pricing_questions
    
    def validate_question(self, question: str) -> Tuple[bool, str]:
        """
        Validate if a question is well-formed for testing.
        
        Args:
            question: The question string to validate
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if not question or not isinstance(question, str):
            return False, "Question is empty or not a string"
        
        question = question.strip()
        
        if len(question) < 10:
            return False, "Question is too short (< 10 characters)"
        
        if len(question) > 500:
            return False, "Question is too long (> 500 characters)"
        
        # Check for placeholder text or incomplete questions
        placeholder_indicators = [
            "...", "[placeholder]", "TODO", "TBD", "xxx", "yyy", "zzz",
            "(example)", "(sample)", "(fill in)", "insert_value_here"
        ]
        
        question_lower = question.lower()
        for placeholder in placeholder_indicators:
            if placeholder in question_lower:
                return False, f"Question contains placeholder text: {placeholder}"
        
        # Check if question looks like it's asking for something meaningful
        question_starters = [
            "get", "show", "list", "find", "what", "how", "which", "where", "when",
            "display", "retrieve", "fetch", "give", "provide", "analyze", "tell",
            "generate", "create", "produce", "return", "identify", "select"
        ]
        
        starts_properly = any(question_lower.startswith(starter) for starter in question_starters)
        if not starts_properly:
            return False, "Question doesn't start with a proper query word"
        
        # Additional checks for automotive context or pricing queries
        automotive_keywords = [
            "vehicle", "vin", "plant", "campaign", "defect", "repair", "quality",
            "connected", "dtc", "tire", "battery", "engine", "shipping", "inventory",
            "ford", "manufacturing", "assembly", "navis", "vmacs", "samis"
        ]
        
        pricing_keywords = [
            "cost", "price", "pricing", "rate", "expense", "spend", "budget",
            "gemini", "cloud functions", "bigquery", "vertex ai", "gcp service"
        ]
        
        has_automotive_context = any(keyword in question_lower for keyword in automotive_keywords)
        has_pricing_context = any(keyword in question_lower for keyword in pricing_keywords)
        
        if not (has_automotive_context or has_pricing_context):
            return False, "Question doesn't appear to be related to automotive manufacturing or GCP pricing"
        
        return True, "Question is well-formed"
    
    def test_single_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test supervisor agent with a single question.
        
        Args:
            question_data: Dictionary containing question and metadata
            
        Returns:
            Test result dictionary
        """
        question = question_data['question']
        start_time = time.time()
        
        logger.info(f"🧪 Testing Question: {question}")
        logger.info(f"   Category: {question_data['category']}")
        logger.info(f"   Difficulty: {question_data['difficulty']}")
        
        result = {
            'question': question,
            'category': question_data['category'],
            'difficulty': question_data['difficulty'],
            'line_number': question_data['line_number'],
            'start_time': start_time,
            'end_time': None,
            'duration': None,
            'status': 'UNKNOWN',
            'success': False,
            'error_message': None,
            'response_data': None,
            'orchestration_metrics': None,
            'sql_generated': None,
            'results_count': 0,
            'validation_status': None
        }
        
        # Validate question before testing
        is_valid, validation_reason = self.validate_question(question)
        result['validation_status'] = {
            'is_valid': is_valid,
            'reason': validation_reason
        }
        
        if not is_valid:
            end_time = time.time()
            result['end_time'] = end_time
            result['duration'] = end_time - start_time
            result['status'] = 'SKIPPED'
            result['error_message'] = f"Question validation failed: {validation_reason}"
            
            logger.warning(f"⚠️ SKIPPED: {question[:60]}...")
            logger.warning(f"   Reason: {validation_reason}")
            return result
        
        try:
            # Call supervisor agent
            response = self.supervisor.handle_query(question)
            
            end_time = time.time()
            result['end_time'] = end_time
            result['duration'] = end_time - start_time
            result['response_data'] = response
            
            # Analyze response
            if response.get('success', False):
                result['status'] = 'PASSED'
                result['success'] = True
                
                # Extract additional metrics
                if 'sql' in response:
                    result['sql_generated'] = response['sql']
                
                if 'results' in response and isinstance(response['results'], list):
                    result['results_count'] = len(response['results'])
                
                if 'orchestration_metrics' in response:
                    result['orchestration_metrics'] = response['orchestration_metrics']
                    
                    # Validate pricing agent usage for pricing questions
                    if question_data.get('source') == 'verified_pricing_questions':
                        decisions = response['orchestration_metrics'].get('decisions', [])
                        used_pricing_agent = any(d.get('action') == 'CALL_PRICING_AGENT' for d in decisions)
                        
                        if used_pricing_agent:
                            logger.info(f"✅ Pricing agent correctly used for pricing question")
                        else:
                            logger.warning(f"⚠️ Pricing question did not use pricing agent - check orchestration")
                
                logger.info(f"✅ PASSED: {question[:60]}...")
                logger.info(f"   Duration: {result['duration']:.2f}s")
                logger.info(f"   Results: {result['results_count']} rows")
                
            else:
                result['status'] = 'FAILED'
                result['error_message'] = response.get('error', 'Unknown failure')
                logger.warning(f"❌ FAILED: {question[:60]}...")
                logger.warning(f"   Error: {result['error_message']}")
                
        except Exception as e:
            end_time = time.time()
            result['end_time'] = end_time
            result['duration'] = end_time - start_time
            result['status'] = 'ERROR'
            result['error_message'] = str(e)
            
            logger.error(f"💥 ERROR: {question[:60]}...")
            logger.error(f"   Exception: {str(e)}")
        
        return result
    
    def run_all_tests(self, max_questions: int = None, category_filter: str = None) -> Dict[str, Any]:
        """
        Run tests on all questions from sample_questions.md.
        
        Args:
            max_questions: Optional limit on number of questions to test
            category_filter: Optional filter to test only specific category
            
        Returns:
            Complete test results and metrics
        """
        logger.info("🎯 Starting Supervisor Agent Test Suite v1")
        logger.info("=" * 80)
        
        # Load questions dynamically
        questions = self.load_questions_from_markdown()
        
        total_questions_loaded = len(questions)
        logger.info(f"📖 Total questions loaded: {total_questions_loaded}")
        
        # Apply category filter if specified
        if category_filter:
            questions = [q for q in questions if category_filter.lower() in q['category'].lower()]
            logger.info(f"🏷️ Filtered to {len(questions)} questions matching category: {category_filter}")
        
        # Apply max questions limit if specified
        if max_questions:
            questions = questions[:max_questions]
            logger.info(f"🔢 Limited to first {max_questions} questions")
        
        if not questions:
            logger.warning("⚠️ No questions to test after filtering!")
            return self._generate_final_report()
        
        logger.info(f"🚀 Starting tests on {len(questions)} questions...")
        
        total_start_time = time.time()
        
        # Run tests
        for i, question_data in enumerate(questions, 1):
            # Progress indicator
            progress_percent = (i / len(questions)) * 100
            logger.info(f"\n[Test {i}/{len(questions)} - {progress_percent:.1f}%] " + "=" * 50)
            
            result = self.test_single_question(question_data)
            self.test_results.append(result)
            
            # Show interim progress every 10 questions for large test runs
            if len(questions) > 20 and i % 10 == 0:
                interim_passed = sum(1 for r in self.test_results if r['status'] == 'PASSED')
                interim_success_rate = (interim_passed / i) * 100
                logger.info(f"📊 Interim Progress: {interim_passed}/{i} passed ({interim_success_rate:.1f}%)")
            
            # Update metrics
            self.test_metrics['total_tests'] += 1
            if result['status'] == 'PASSED':
                self.test_metrics['passed_tests'] += 1
            elif result['status'] == 'FAILED':
                self.test_metrics['failed_tests'] += 1
            elif result['status'] == 'ERROR':
                self.test_metrics['error_tests'] += 1
            elif result['status'] == 'SKIPPED':
                self.test_metrics['skipped_tests'] += 1
        
        total_end_time = time.time()
        self.test_metrics['total_time'] = total_end_time - total_start_time
        
        # Calculate average response time
        valid_durations = [r['duration'] for r in self.test_results if r['duration'] is not None]
        if valid_durations:
            self.test_metrics['avg_response_time'] = sum(valid_durations) / len(valid_durations)
        
        return self._generate_final_report()
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        logger.info("\n" + "=" * 80)
        logger.info("🏁 SUPERVISOR AGENT TEST RESULTS - FINAL REPORT")
        logger.info("=" * 80)
        
        # Overall metrics
        metrics = self.test_metrics
        tested_questions = metrics['total_tests'] - metrics['skipped_tests']
        success_rate = (metrics['passed_tests'] / tested_questions * 100) if tested_questions > 0 else 0
        
        logger.info(f"📊 Overall Results:")
        logger.info(f"   Total Questions: {metrics['total_tests']}")
        logger.info(f"   ✅ Passed: {metrics['passed_tests']}")
        logger.info(f"   ❌ Failed: {metrics['failed_tests']}")
        logger.info(f"   💥 Errors: {metrics['error_tests']}")
        logger.info(f"   ⏭️ Skipped: {metrics['skipped_tests']}")
        logger.info(f"   🧪 Actually Tested: {tested_questions}")
        logger.info(f"   🎯 Success Rate: {success_rate:.1f}%")
        logger.info(f"   ⏱️  Total Time: {metrics['total_time']:.2f}s")
        logger.info(f"   ⚡ Avg Response Time: {metrics['avg_response_time']:.2f}s")
        
        # Results by category
        category_stats = {}
        for result in self.test_results:
            category = result['category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'passed': 0, 'failed': 0, 'error': 0, 'skipped': 0}
            
            category_stats[category]['total'] += 1
            if result['status'] == 'PASSED':
                category_stats[category]['passed'] += 1
            elif result['status'] == 'FAILED':
                category_stats[category]['failed'] += 1
            elif result['status'] == 'ERROR':
                category_stats[category]['error'] += 1
            elif result['status'] == 'SKIPPED':
                category_stats[category]['skipped'] += 1
        
        logger.info("\n📈 Results by Category:")
        for category, stats in category_stats.items():
            tested_in_category = stats['total'] - stats['skipped']
            cat_success_rate = (stats['passed'] / tested_in_category * 100) if tested_in_category > 0 else 0
            logger.info(f"   {category}:")
            logger.info(f"      Success Rate: {cat_success_rate:.1f}% ({stats['passed']}/{tested_in_category})")
            if stats['skipped'] > 0:
                logger.info(f"      Skipped: {stats['skipped']}")
        
        # Failed/Error/Skipped questions
        problematic_questions = [r for r in self.test_results if r['status'] in ['FAILED', 'ERROR', 'SKIPPED']]
        if problematic_questions:
            logger.info("\n⚠️ Problematic Questions:")
            for result in problematic_questions:
                status_emoji = {'FAILED': '❌', 'ERROR': '💥', 'SKIPPED': '⏭️'}
                emoji = status_emoji.get(result['status'], '⚠️')
                logger.info(f"   {emoji} [{result['status']}] {result['question'][:80]}...")
                if result['error_message']:
                    logger.info(f"      Reason: {result['error_message']}")
        
        # Performance insights
        fast_queries = [r for r in self.test_results if r['duration'] and r['duration'] < 5.0]
        slow_queries = [r for r in self.test_results if r['duration'] and r['duration'] > 15.0]
        
        logger.info(f"\n⚡ Performance Insights:")
        logger.info(f"   Fast Queries (<5s): {len(fast_queries)}")
        logger.info(f"   Slow Queries (>15s): {len(slow_queries)}")
        
        if slow_queries:
            logger.info("   Slowest Queries:")
            slow_queries.sort(key=lambda x: x['duration'], reverse=True)
            for result in slow_queries[:3]:
                logger.info(f"      {result['duration']:.1f}s: {result['question'][:60]}...")
        
        # Generate return data
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_metrics': self.test_metrics,
            'category_stats': category_stats,
            'detailed_results': self.test_results,
            'summary': {
                'total_questions_loaded': metrics['total_tests'],
                'questions_actually_tested': tested_questions,
                'questions_skipped': metrics['skipped_tests'],
                'overall_success_rate': success_rate,
                'avg_response_time': metrics['avg_response_time'],
                'questions_source': str(self.sample_questions_file),
                'supervisor_model': 'gemini-2.5-flash-lite',
                'validation_enabled': True
            }
        }
        
        logger.info("\n✅ Test suite completed successfully!")
        logger.info("=" * 80)
        
        return report
    
    def save_results_to_file(self, report: Dict[str, Any], output_file: str = None):
        """Save test results to JSON file."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"supervisor_test_results_{timestamp}.json"
        
        output_path = self.project_root / "tests" / output_file
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"💾 Test results saved to: {output_path}")


def main():
    """Main test execution function."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Supervisor Agent with dynamic question loading')
    parser.add_argument('--max-questions', type=int, default=None, 
                       help='Maximum number of questions to test (default: all questions)')
    parser.add_argument('--category', type=str, default=None,
                       help='Test only questions from specific category')
    parser.add_argument('--min-success-rate', type=float, default=80.0,
                       help='Minimum success rate to consider test suite passed (default: 80.0)')
    args = parser.parse_args()
    
    try:
        # Initialize tester
        tester = SupervisorAgentTester()
        
        # Log test configuration
        if args.max_questions:
            logger.info(f"🔢 Testing limited to {args.max_questions} questions")
        else:
            logger.info("🌟 Testing ALL questions from sample_questions.md")
        
        if args.category:
            logger.info(f"🏷️ Filtering by category: {args.category}")
        
        # Run tests with all questions by default
        report = tester.run_all_tests(
            max_questions=args.max_questions,
            category_filter=args.category
        )
        
        # Save results
        tester.save_results_to_file(report)
        
        # Return success based on results
        success_rate = report['summary']['overall_success_rate']
        if success_rate >= args.min_success_rate:
            logger.info(f"🎉 Test suite PASSED with {success_rate:.1f}% success rate")
            return 0
        else:
            logger.warning(f"⚠️ Test suite had success rate {success_rate:.1f}% (below {args.min_success_rate}%)")
            return 1
            
    except Exception as e:
        logger.error(f"💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
