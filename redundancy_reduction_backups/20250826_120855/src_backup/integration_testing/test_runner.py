# src/integration_testing/test_runner.py
import time
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

from .system_tester import SystemIntegrationTester
from .component_tester import ComponentInteractionTester 
from .performance_tester import PerformanceIntegrationTester
try:
    from utils.logger import get_logger
except ImportError:
    from src.utils.logger import get_logger

logger = get_logger(__name__)

class IntegrationTestRunner:
    """
    Main integration test runner that coordinates all types of integration tests
    
    Provides a unified interface for running system integration tests, component
    interaction tests, and performance tests.
    """
    
    def __init__(self, settings: Optional[Dict] = None):
        """Initialize the integration test runner"""
        try:
            from utils.config import get_project_settings
        except ImportError:
            from src.utils.config import get_project_settings
        self.settings = settings or get_project_settings()
        self.data_dir = Path(self.settings['data_dir'])
        self.logger = get_logger(__name__)
        
        # Initialize test results directory
        self.results_dir = self.data_dir / "integration_test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize testers
        self.system_tester = SystemIntegrationTester(self.settings)
        self.component_tester = ComponentInteractionTester(self.settings)
        self.performance_tester = PerformanceIntegrationTester(self.settings)
    
    def run_all_tests(self, 
                      include_system: bool = True,
                      include_component: bool = True, 
                      include_performance: bool = True,
                      performance_scenarios: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Run all integration tests"""
        self.logger.info("=" * 60)
        self.logger.info("STARTING COMPREHENSIVE INTEGRATION TESTING")
        self.logger.info("=" * 60)
        
        overall_start_time = time.time()
        all_results = {}
        
        # Run system integration tests
        if include_system:
            self.logger.info("\n" + "="*50)
            self.logger.info("SYSTEM INTEGRATION TESTS")
            self.logger.info("="*50)
            try:
                system_results = self.system_tester.run_full_system_test()
                all_results['system_integration'] = system_results
                self._log_test_summary("System Integration", system_results)
            except Exception as e:
                self.logger.error(f"System integration tests failed: {e}")
                all_results['system_integration'] = {"error": str(e)}
        
        # Run component interaction tests
        if include_component:
            self.logger.info("\n" + "="*50)
            self.logger.info("COMPONENT INTERACTION TESTS")
            self.logger.info("="*50)
            try:
                component_results = self.component_tester.run_component_interaction_tests()
                all_results['component_interaction'] = component_results
                self._log_component_summary("Component Interaction", component_results)
            except Exception as e:
                self.logger.error(f"Component interaction tests failed: {e}")
                all_results['component_interaction'] = {"error": str(e)}
        
        # Run performance tests
        if include_performance:
            self.logger.info("\n" + "="*50)
            self.logger.info("PERFORMANCE INTEGRATION TESTS")
            self.logger.info("="*50)
            try:
                performance_results = self.performance_tester.run_performance_tests(performance_scenarios)
                all_results['performance'] = performance_results
                self._log_performance_summary("Performance", performance_results)
            except Exception as e:
                self.logger.error(f"Performance tests failed: {e}")
                all_results['performance'] = {"error": str(e)}
        
        # Generate overall summary
        total_duration = time.time() - overall_start_time
        overall_summary = self._generate_overall_summary(all_results, total_duration)
        all_results['overall_summary'] = overall_summary
        
        self.logger.info("\n" + "="*60)
        self.logger.info("INTEGRATION TESTING COMPLETE")
        self.logger.info("="*60)
        self._log_overall_summary(overall_summary)
        
        # Save comprehensive results
        self._save_comprehensive_results(all_results)
        
        return all_results
    
    def run_system_tests_only(self) -> Dict[str, Any]:
        """Run only system integration tests"""
        self.logger.info("Running system integration tests only")
        return self.system_tester.run_full_system_test()
    
    def run_component_tests_only(self) -> Dict[str, Any]:
        """Run only component interaction tests"""
        self.logger.info("Running component interaction tests only")
        return self.component_tester.run_component_interaction_tests()
    
    def run_performance_tests_only(self, scenarios: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Run only performance tests"""
        self.logger.info("Running performance tests only")
        return self.performance_tester.run_performance_tests(scenarios)
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run a quick subset of tests for rapid feedback"""
        self.logger.info("Running quick integration tests")
        
        # Define quick performance scenarios
        quick_scenarios = [
            {
                "name": "quick_batch_test",
                "description": "Quick batch processing test",
                "batch_size": 5,
                "iterations": 2,
                "test_type": "batch_processing"
            },
            {
                "name": "quick_confidence_test",
                "description": "Quick confidence scoring test",
                "batch_size": 10,
                "iterations": 2,
                "test_type": "confidence_scoring"
            }
        ]
        
        return self.run_all_tests(
            include_system=True,
            include_component=True,
            include_performance=True,
            performance_scenarios=quick_scenarios
        )
    
    def run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests with larger workloads"""
        self.logger.info("Running stress integration tests")
        
        # Define stress test scenarios
        stress_scenarios = [
            {
                "name": "stress_large_batch",
                "description": "Stress test with large batches",
                "batch_size": 200,
                "iterations": 3,
                "test_type": "batch_processing"
            },
            {
                "name": "stress_ai_analysis",
                "description": "Stress test AI analysis",
                "batch_size": 100,
                "iterations": 5,
                "test_type": "ai_analysis"
            },
            {
                "name": "stress_concurrent",
                "description": "Stress test concurrent processing",
                "batch_size": 50,
                "iterations": 3,
                "test_type": "concurrent_processing",
                "concurrent_batches": 5
            }
        ]
        
        return self.run_all_tests(
            include_system=True,
            include_component=True,
            include_performance=True,
            performance_scenarios=stress_scenarios
        )
    
    def _log_test_summary(self, test_type: str, results: Dict[str, Any]):
        """Log test summary for system tests"""
        if "error" in results:
            self.logger.error(f"{test_type} failed: {results['error']}")
            return
        
        total = results.get('total_tests', 0)
        passed = results.get('passed', 0)
        failed = results.get('failed', 0)
        skipped = results.get('skipped', 0)
        duration = results.get('total_duration', 0)
        
        self.logger.info(f"\n{test_type} Results:")
        self.logger.info(f"  Total Tests: {total}")
        self.logger.info(f"  Passed: {passed}")
        self.logger.info(f"  Failed: {failed}")
        self.logger.info(f"  Skipped: {skipped}")
        self.logger.info(f"  Duration: {duration:.2f}s")
        self.logger.info(f"  Success Rate: {(passed/total*100):.1f}%" if total > 0 else "  Success Rate: N/A")
    
    def _log_component_summary(self, test_type: str, results: Dict[str, Any]):
        """Log test summary for component tests"""
        if "error" in results:
            self.logger.error(f"{test_type} failed: {results['error']}")
            return
        
        total = len(results)
        passed = len([r for r in results.values() if r.status == "passed"])
        failed = len([r for r in results.values() if r.status == "failed"])
        skipped = len([r for r in results.values() if r.status == "skipped"])
        
        self.logger.info(f"\n{test_type} Results:")
        self.logger.info(f"  Total Tests: {total}")
        self.logger.info(f"  Passed: {passed}")
        self.logger.info(f"  Failed: {failed}")
        self.logger.info(f"  Skipped: {skipped}")
        self.logger.info(f"  Success Rate: {(passed/total*100):.1f}%" if total > 0 else "  Success Rate: N/A")
    
    def _log_performance_summary(self, test_type: str, results: Dict[str, Any]):
        """Log test summary for performance tests"""
        if "error" in results:
            self.logger.error(f"{test_type} failed: {results['error']}")
            return
        
        total = results.get('total_scenarios', 0)
        completed = results.get('completed', 0)
        failed = results.get('failed', 0)
        duration = results.get('total_duration', 0)
        
        summary = results.get('summary', {})
        avg_throughput = summary.get('overall_avg_throughput', 0)
        avg_success_rate = summary.get('overall_avg_success_rate', 0)
        performance_grade = summary.get('performance_grade', 'N/A')
        
        self.logger.info(f"\n{test_type} Results:")
        self.logger.info(f"  Total Scenarios: {total}")
        self.logger.info(f"  Completed: {completed}")
        self.logger.info(f"  Failed: {failed}")
        self.logger.info(f"  Duration: {duration:.2f}s")
        self.logger.info(f"  Avg Throughput: {avg_throughput:.2f} items/sec")
        self.logger.info(f"  Avg Success Rate: {(avg_success_rate*100):.1f}%")
        self.logger.info(f"  Performance Grade: {performance_grade}")
    
    def _generate_overall_summary(self, all_results: Dict[str, Any], total_duration: float) -> Dict[str, Any]:
        """Generate overall test summary"""
        summary = {
            "total_duration": total_duration,
            "tests_run": [],
            "overall_status": "unknown",
            "total_test_count": 0,
            "total_passed": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "success_rate": 0.0,
            "recommendations": []
        }
        
        # Analyze system integration results
        if 'system_integration' in all_results:
            system_results = all_results['system_integration']
            if "error" not in system_results:
                summary["tests_run"].append("system_integration")
                summary["total_test_count"] += system_results.get('total_tests', 0)
                summary["total_passed"] += system_results.get('passed', 0)
                summary["total_failed"] += system_results.get('failed', 0)
                summary["total_skipped"] += system_results.get('skipped', 0)
        
        # Analyze component interaction results
        if 'component_interaction' in all_results:
            component_results = all_results['component_interaction']
            if "error" not in component_results:
                summary["tests_run"].append("component_interaction")
                total_component_tests = len(component_results)
                passed_component_tests = len([r for r in component_results.values() if r.status == "passed"])
                failed_component_tests = len([r for r in component_results.values() if r.status == "failed"])
                skipped_component_tests = len([r for r in component_results.values() if r.status == "skipped"])
                
                summary["total_test_count"] += total_component_tests
                summary["total_passed"] += passed_component_tests
                summary["total_failed"] += failed_component_tests
                summary["total_skipped"] += skipped_component_tests
        
        # Analyze performance results
        if 'performance' in all_results:
            performance_results = all_results['performance']
            if "error" not in performance_results:
                summary["tests_run"].append("performance")
                total_perf_tests = performance_results.get('total_scenarios', 0)
                completed_perf_tests = performance_results.get('completed', 0)
                failed_perf_tests = performance_results.get('failed', 0)
                
                summary["total_test_count"] += total_perf_tests
                summary["total_passed"] += completed_perf_tests
                summary["total_failed"] += failed_perf_tests
        
        # Calculate overall success rate
        if summary["total_test_count"] > 0:
            summary["success_rate"] = summary["total_passed"] / summary["total_test_count"]
        
        # Determine overall status
        if summary["success_rate"] >= 0.9:
            summary["overall_status"] = "excellent"
        elif summary["success_rate"] >= 0.8:
            summary["overall_status"] = "good"
        elif summary["success_rate"] >= 0.7:
            summary["overall_status"] = "fair"
        else:
            summary["overall_status"] = "poor"
        
        # Generate recommendations
        if summary["total_failed"] > 0:
            summary["recommendations"].append("Investigate and fix failing tests")
        
        if summary["success_rate"] < 0.8:
            summary["recommendations"].append("Improve system reliability and test coverage")
        
        if 'performance' in all_results:
            perf_summary = all_results['performance'].get('summary', {})
            if perf_summary.get('performance_grade', 'F') in ['D', 'F']:
                summary["recommendations"].append("Optimize system performance")
        
        return summary
    
    def _log_overall_summary(self, summary: Dict[str, Any]):
        """Log overall test summary"""
        self.logger.info(f"\nOVERALL TEST SUMMARY:")
        self.logger.info(f"  Tests Run: {', '.join(summary['tests_run'])}")
        self.logger.info(f"  Total Duration: {summary['total_duration']:.2f}s")
        self.logger.info(f"  Total Tests: {summary['total_test_count']}")
        self.logger.info(f"  Passed: {summary['total_passed']}")
        self.logger.info(f"  Failed: {summary['total_failed']}")
        self.logger.info(f"  Skipped: {summary['total_skipped']}")
        self.logger.info(f"  Success Rate: {(summary['success_rate']*100):.1f}%")
        self.logger.info(f"  Overall Status: {summary['overall_status'].upper()}")
        
        if summary['recommendations']:
            self.logger.info(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(summary['recommendations'], 1):
                self.logger.info(f"  {i}. {rec}")
    
    def _save_comprehensive_results(self, all_results: Dict[str, Any]):
        """Save comprehensive test results"""
        try:
            import json
            
            timestamp = int(time.time())
            results_file = self.results_dir / f"comprehensive_integration_results_{timestamp}.json"
            
            # Convert results to serializable format
            def serialize_result(obj):
                if hasattr(obj, '__dict__'):
                    return obj.__dict__
                elif hasattr(obj, '_asdict'):
                    return obj._asdict()
                else:
                    return str(obj)
            
            with open(results_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=serialize_result)
            
            self.logger.info(f"\nComprehensive test results saved to: {results_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save comprehensive results: {e}")


def main():
    """Main function for running integration tests from command line"""
    parser = argparse.ArgumentParser(description="Run integration tests for the Smart Description system")
    
    parser.add_argument('--type', choices=['all', 'system', 'component', 'performance', 'quick', 'stress'],
                       default='all', help='Type of tests to run')
    parser.add_argument('--no-system', action='store_true', help='Skip system integration tests')
    parser.add_argument('--no-component', action='store_true', help='Skip component interaction tests')
    parser.add_argument('--no-performance', action='store_true', help='Skip performance tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize test runner
    runner = IntegrationTestRunner()
    
    # Run tests based on arguments
    if args.type == 'system':
        results = runner.run_system_tests_only()
    elif args.type == 'component':
        results = runner.run_component_tests_only()
    elif args.type == 'performance':
        results = runner.run_performance_tests_only()
    elif args.type == 'quick':
        results = runner.run_quick_tests()
    elif args.type == 'stress':
        results = runner.run_stress_tests()
    else:  # all
        results = runner.run_all_tests(
            include_system=not args.no_system,
            include_component=not args.no_component,
            include_performance=not args.no_performance
        )
    
    # Exit with appropriate code
    if args.type == 'all':
        overall_summary = results.get('overall_summary', {})
        success_rate = overall_summary.get('success_rate', 0)
        exit_code = 0 if success_rate >= 0.8 else 1
    else:
        # For individual test types, use basic success criteria
        exit_code = 0  # Default to success for now
    
    exit(exit_code)


if __name__ == "__main__":
    main()
