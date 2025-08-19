#!/usr/bin/env python3
"""
Comprehensive Integration Test Runner for Smart Description Iterative Improvement System

This script provides a command-line interface for running all types of integration tests
including system integration tests, component interaction tests, and performance tests.

Usage:
    python scripts/run_integration_tests.py --type all
    python scripts/run_integration_tests.py --type quick
    python scripts/run_integration_tests.py --type system
    python scripts/run_integration_tests.py --type performance
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root and src directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from integration_testing import IntegrationTestRunner
from utils.logger import get_logger
from utils.config import get_project_settings

logger = get_logger(__name__)

def main():
    """Main function for running integration tests"""
    parser = argparse.ArgumentParser(
        description="Run comprehensive integration tests for Smart Description system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_integration_tests.py --type all              # Run all tests
  python scripts/run_integration_tests.py --type quick            # Run quick tests
  python scripts/run_integration_tests.py --type system           # System tests only
  python scripts/run_integration_tests.py --type component        # Component tests only
  python scripts/run_integration_tests.py --type performance      # Performance tests only
  python scripts/run_integration_tests.py --type stress           # Stress tests
  python scripts/run_integration_tests.py --no-performance        # Skip performance tests
        """
    )
    
    parser.add_argument(
        '--type', 
        choices=['all', 'system', 'component', 'performance', 'quick', 'stress'],
        default='all', 
        help='Type of integration tests to run (default: all)'
    )
    
    parser.add_argument(
        '--no-system', 
        action='store_true', 
        help='Skip system integration tests'
    )
    
    parser.add_argument(
        '--no-component', 
        action='store_true', 
        help='Skip component interaction tests'
    )
    
    parser.add_argument(
        '--no-performance', 
        action='store_true', 
        help='Skip performance tests'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Custom directory for test results (default: data/integration_test_results)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,  # 30 minutes
        help='Overall timeout for tests in seconds (default: 1800)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    logger.info("Starting Smart Description Integration Test Suite")
    logger.info("=" * 60)
    
    try:
        # Load settings
        settings = get_project_settings()
        
        # Override output directory if specified
        if args.output_dir:
            settings['data_dir'] = args.output_dir
        
        # Initialize test runner
        logger.info("Initializing integration test runner...")
        runner = IntegrationTestRunner(settings)
        
        # Check test environment
        logger.info("Checking test environment...")
        environment_check = check_test_environment(settings)
        if not environment_check['ready']:
            logger.warning("Test environment issues detected:")
            for issue in environment_check['issues']:
                logger.warning(f"  - {issue}")
            logger.info("Continuing with available components...")
        
        # Run tests based on arguments
        logger.info(f"Running integration tests: type={args.type}")
        
        if args.type == 'system':
            logger.info("Running system integration tests only...")
            results = runner.run_system_tests_only()
        elif args.type == 'component':
            logger.info("Running component interaction tests only...")
            results = runner.run_component_tests_only()
        elif args.type == 'performance':
            logger.info("Running performance tests only...")
            results = runner.run_performance_tests_only()
        elif args.type == 'quick':
            logger.info("Running quick integration tests...")
            results = runner.run_quick_tests()
        elif args.type == 'stress':
            logger.info("Running stress integration tests...")
            results = runner.run_stress_tests()
        else:  # all
            logger.info("Running comprehensive integration tests...")
            results = runner.run_all_tests(
                include_system=not args.no_system,
                include_component=not args.no_component,
                include_performance=not args.no_performance
            )
        
        # Display final results
        display_final_results(results, args.type)
        
        # Determine exit code
        exit_code = determine_exit_code(results, args.type)
        
        logger.info(f"Integration tests completed with exit code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        logger.warning("Integration tests interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.error(f"Integration tests failed with error: {e}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        return 1


def check_test_environment(settings: dict) -> dict:
    """Check if the test environment is ready"""
    issues = []
    ready = True
    
    try:
        # Check data directory
        data_dir = Path(settings.get('data_dir', 'data'))
        if not data_dir.exists():
            issues.append(f"Data directory not found: {data_dir}")
            ready = False
        
        # Check for test data
        input_dir = Path(settings.get('input_dir', 'data/input'))
        if input_dir.exists():
            test_files = list(input_dir.glob('*.csv')) + list(input_dir.glob('*.json'))
            if not test_files:
                issues.append("No test data files found in input directory")
        else:
            issues.append(f"Input directory not found: {input_dir}")
        
        # Check OpenAI API key availability
        from utils.config import get_openai_api_key
        api_key = get_openai_api_key()
        if not api_key:
            issues.append("OpenAI API key not available (will use mock AI client)")
        
        # Check dependencies
        try:
            import pandas as pd
        except ImportError as e:
            issues.append(f"Missing required dependency: {e}")
            ready = False
        
        # Check optional dependencies
        try:
            import psutil
        except ImportError:
            issues.append("psutil not available (performance metrics will be limited)")
        
    except Exception as e:
        issues.append(f"Environment check error: {e}")
        ready = False
    
    return {
        'ready': ready,
        'issues': issues
    }


def display_final_results(results: dict, test_type: str):
    """Display final test results in a formatted way"""
    logger.info("\n" + "=" * 70)
    logger.info("FINAL INTEGRATION TEST RESULTS")
    logger.info("=" * 70)
    
    if test_type == 'all' and 'overall_summary' in results:
        summary = results['overall_summary']
        
        logger.info(f"\nOVERALL SUMMARY:")
        logger.info(f"  Tests Run: {', '.join(summary.get('tests_run', []))}")
        logger.info(f"  Total Duration: {summary.get('total_duration', 0):.2f}s")
        logger.info(f"  Total Tests: {summary.get('total_test_count', 0)}")
        logger.info(f"  Passed: {summary.get('total_passed', 0)}")
        logger.info(f"  Failed: {summary.get('total_failed', 0)}")
        logger.info(f"  Skipped: {summary.get('total_skipped', 0)}")
        logger.info(f"  Success Rate: {(summary.get('success_rate', 0)*100):.1f}%")
        logger.info(f"  Overall Status: {summary.get('overall_status', 'unknown').upper()}")
        
        if summary.get('recommendations'):
            logger.info(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(summary['recommendations'], 1):
                logger.info(f"  {i}. {rec}")
    
    # Display individual test type results
    if 'system_integration' in results:
        system_results = results['system_integration']
        if 'error' not in system_results:
            logger.info(f"\nSYSTEM INTEGRATION TESTS:")
            logger.info(f"  Passed: {system_results.get('passed', 0)}/{system_results.get('total_tests', 0)}")
            logger.info(f"  Duration: {system_results.get('total_duration', 0):.2f}s")
        else:
            logger.info(f"\nSYSTEM INTEGRATION TESTS: FAILED")
            logger.info(f"  Error: {system_results['error']}")
    
    if 'component_interaction' in results:
        component_results = results['component_interaction']
        if 'error' not in component_results:
            total = len(component_results)
            passed = len([r for r in component_results.values() if getattr(r, 'status', None) == 'passed'])
            logger.info(f"\nCOMPONENT INTERACTION TESTS:")
            logger.info(f"  Passed: {passed}/{total}")
        else:
            logger.info(f"\nCOMPONENT INTERACTION TESTS: FAILED")
            logger.info(f"  Error: {component_results['error']}")
    
    if 'performance' in results:
        performance_results = results['performance']
        if 'error' not in performance_results:
            logger.info(f"\nPERFORMANCE TESTS:")
            logger.info(f"  Completed: {performance_results.get('completed', 0)}/{performance_results.get('total_scenarios', 0)}")
            logger.info(f"  Duration: {performance_results.get('total_duration', 0):.2f}s")
            
            summary = performance_results.get('summary', {})
            if summary:
                logger.info(f"  Avg Throughput: {summary.get('overall_avg_throughput', 0):.2f} items/sec")
                logger.info(f"  Performance Grade: {summary.get('performance_grade', 'N/A')}")
        else:
            logger.info(f"\nPERFORMANCE TESTS: FAILED")
            logger.info(f"  Error: {performance_results['error']}")


def determine_exit_code(results: dict, test_type: str) -> int:
    """Determine appropriate exit code based on test results"""
    if test_type == 'all' and 'overall_summary' in results:
        summary = results['overall_summary']
        success_rate = summary.get('success_rate', 0)
        
        if success_rate >= 0.9:
            return 0  # Excellent
        elif success_rate >= 0.8:
            return 0  # Good enough
        elif success_rate >= 0.5:
            return 2  # Warning - partial success
        else:
            return 1  # Failure
    
    # For individual test types
    if test_type == 'system' and 'system_integration' in results:
        system_results = results['system_integration']
        if 'error' in system_results:
            return 1
        success_rate = system_results.get('passed', 0) / max(system_results.get('total_tests', 1), 1)
        return 0 if success_rate >= 0.8 else 1
    
    if test_type == 'component' and 'component_interaction' in results:
        component_results = results['component_interaction']
        if 'error' in component_results:
            return 1
        total = len(component_results)
        passed = len([r for r in component_results.values() if getattr(r, 'status', None) == 'passed'])
        success_rate = passed / max(total, 1)
        return 0 if success_rate >= 0.8 else 1
    
    if test_type == 'performance' and 'performance' in results:
        performance_results = results['performance']
        if 'error' in performance_results:
            return 1
        summary = performance_results.get('summary', {})
        grade = summary.get('performance_grade', 'F')
        return 0 if grade in ['A', 'B', 'C'] else 1
    
    # Default to success for quick/stress tests if they complete
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
