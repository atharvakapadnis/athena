# src/integration_testing/performance_tester.py
import time
import statistics
import threading
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from .system_tester import TestResult
from .test_data_generator import TestDataGenerator

# Import system components
try:
    from batch_processor import BatchProcessingSystem, BatchConfig
    from ai_analysis import AnalysisAggregator, AIClient
    from rule_editor import RuleManager
    from confidence_scoring import ConfidenceScoringSystem
    from utils.logger import get_logger
except ImportError:
    # Fallback for different import contexts
    from src.batch_processor import BatchProcessingSystem, BatchConfig
    from src.ai_analysis import AnalysisAggregator, AIClient
    from src.rule_editor import RuleManager
    from src.confidence_scoring import ConfidenceScoringSystem
    from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_items_per_second: float
    success_rate: float
    error_count: int

@dataclass
class ScenarioResult:
    """Performance scenario result"""
    scenario_name: str
    metrics: PerformanceMetrics
    iterations: int
    batch_size: int
    status: str
    details: Dict[str, Any]

class PerformanceIntegrationTester:
    """
    Performance integration tester for system components
    
    Tests system performance under various scenarios including different batch sizes,
    concurrent operations, and stress testing.
    """
    
    def __init__(self, settings: Optional[Dict] = None):
        """Initialize the performance integration tester"""
        try:
            from utils.config import get_project_settings
        except ImportError:
            from src.utils.config import get_project_settings
        self.settings = settings or get_project_settings()
        self.data_dir = Path(self.settings['data_dir'])
        self.test_data_generator = TestDataGenerator()
        self.logger = get_logger(__name__)
        self.performance_metrics = {}
        
        # Initialize test data directory
        self.test_data_dir = self.data_dir / "performance_tests"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Warn if psutil is not available
        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil is not available - memory and CPU monitoring will be disabled")
    
    def run_performance_tests(self, test_scenarios: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Run comprehensive performance tests"""
        self.logger.info("Starting performance integration tests")
        
        if test_scenarios is None:
            test_scenarios = self._get_default_test_scenarios()
        
        scenario_results = {}
        overall_start_time = time.time()
        
        for scenario in test_scenarios:
            self.logger.info(f"Running performance scenario: {scenario['name']}")
            try:
                result = self._run_performance_scenario(scenario)
                scenario_results[scenario['name']] = result
                
                if result.status == "passed":
                    self.logger.info(f"✓ {scenario['name']} completed ({result.metrics.execution_time:.2f}s)")
                else:
                    self.logger.warning(f"○ {scenario['name']} completed with issues")
                    
            except Exception as e:
                error_result = ScenarioResult(
                    scenario_name=scenario['name'],
                    metrics=PerformanceMetrics(0, 0, 0, 0, 0, 1),
                    iterations=scenario.get('iterations', 1),
                    batch_size=scenario.get('batch_size', 0),
                    status="failed",
                    details={"error": str(e)}
                )
                scenario_results[scenario['name']] = error_result
                self.logger.error(f"✗ {scenario['name']} failed: {e}")
        
        total_duration = time.time() - overall_start_time
        
        summary = {
            "total_scenarios": len(test_scenarios),
            "completed": len([r for r in scenario_results.values() if r.status in ["passed", "warning"]]),
            "failed": len([r for r in scenario_results.values() if r.status == "failed"]),
            "total_duration": total_duration,
            "scenarios": scenario_results,
            "summary": self._generate_performance_summary(scenario_results)
        }
        
        self.logger.info(f"Performance tests completed: {summary['completed']}/{summary['total_scenarios']} scenarios successful")
        self._save_performance_results(summary)
        
        return summary
    
    def _get_default_test_scenarios(self) -> List[Dict]:
        """Get default performance test scenarios"""
        return [
            {
                "name": "small_batch_performance",
                "description": "Test performance with small batches",
                "batch_size": 10,
                "iterations": 5,
                "test_type": "batch_processing"
            },
            {
                "name": "medium_batch_performance", 
                "description": "Test performance with medium batches",
                "batch_size": 50,
                "iterations": 3,
                "test_type": "batch_processing"
            },
            {
                "name": "large_batch_performance",
                "description": "Test performance with large batches",
                "batch_size": 100,
                "iterations": 2,
                "test_type": "batch_processing"
            },
            {
                "name": "ai_analysis_performance",
                "description": "Test AI analysis performance",
                "batch_size": 20,
                "iterations": 3,
                "test_type": "ai_analysis"
            },
            {
                "name": "confidence_scoring_performance",
                "description": "Test confidence scoring performance",
                "batch_size": 100,
                "iterations": 5,
                "test_type": "confidence_scoring"
            },
            {
                "name": "rule_management_performance",
                "description": "Test rule management performance",
                "batch_size": 50,
                "iterations": 3,
                "test_type": "rule_management"
            },
            {
                "name": "concurrent_batch_processing",
                "description": "Test concurrent batch processing",
                "batch_size": 25,
                "iterations": 2,
                "test_type": "concurrent_processing",
                "concurrent_batches": 3
            }
        ]
    
    def _run_performance_scenario(self, scenario: Dict) -> ScenarioResult:
        """Run a single performance scenario"""
        scenario_name = scenario["name"]
        test_type = scenario["test_type"]
        batch_size = scenario["batch_size"]
        iterations = scenario["iterations"]
        
        self.logger.debug(f"Running scenario {scenario_name}: {test_type} with batch_size={batch_size}, iterations={iterations}")
        
        if test_type == "batch_processing":
            return self._test_batch_processing_performance(scenario)
        elif test_type == "ai_analysis":
            return self._test_ai_analysis_performance(scenario)
        elif test_type == "confidence_scoring":
            return self._test_confidence_scoring_performance(scenario)
        elif test_type == "rule_management":
            return self._test_rule_management_performance(scenario)
        elif test_type == "concurrent_processing":
            return self._test_concurrent_processing_performance(scenario)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
    
    def _test_batch_processing_performance(self, scenario: Dict) -> ScenarioResult:
        """Test batch processing performance"""
        batch_size = scenario["batch_size"]
        iterations = scenario["iterations"]
        
        processing_times = []
        memory_usages = []
        cpu_usages = []
        success_rates = []
        error_count = 0
        
        # Initialize batch processing system
        mock_data_loader = self.test_data_generator.create_mock_data_loader()
        mock_description_generator = self.test_data_generator.create_mock_description_generator()
        
        batch_system = BatchProcessingSystem(
            mock_data_loader,
            mock_description_generator,
            self.settings
        )
        
        for i in range(iterations):
            # Monitor system resources (if psutil is available)
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                cpu_before = process.cpu_percent()
            else:
                memory_before = 0
                cpu_before = 0
            
            start_time = time.time()
            
            try:
                # Process batch
                batch_config = BatchConfig(batch_size=batch_size)
                result = batch_system.run_batch(batch_config)
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                
                # Monitor resources after processing (if psutil is available)
                if PSUTIL_AVAILABLE:
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    cpu_after = process.cpu_percent()
                    memory_usages.append(memory_after - memory_before)
                    cpu_usages.append(max(cpu_after - cpu_before, 0))
                else:
                    memory_usages.append(0)
                    cpu_usages.append(0)
                
                if result and hasattr(result, 'success_rate'):
                    success_rates.append(result.success_rate)
                else:
                    success_rates.append(0.0)
                    
            except Exception as e:
                self.logger.error(f"Error in batch processing iteration {i}: {e}")
                error_count += 1
                processing_times.append(0)
                memory_usages.append(0)
                cpu_usages.append(0)
                success_rates.append(0)
        
        # Calculate metrics
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        avg_memory_usage = statistics.mean(memory_usages) if memory_usages else 0
        avg_cpu_usage = statistics.mean(cpu_usages) if cpu_usages else 0
        avg_success_rate = statistics.mean(success_rates) if success_rates else 0
        throughput = (batch_size / avg_processing_time) if avg_processing_time > 0 else 0
        
        metrics = PerformanceMetrics(
            execution_time=avg_processing_time,
            memory_usage_mb=avg_memory_usage,
            cpu_usage_percent=avg_cpu_usage,
            throughput_items_per_second=throughput,
            success_rate=avg_success_rate,
            error_count=error_count
        )
        
        # Determine status
        status = "passed"
        if error_count > 0 or avg_success_rate < 0.5:
            status = "warning" if error_count < iterations / 2 else "failed"
        
        return ScenarioResult(
            scenario_name=scenario["name"],
            metrics=metrics,
            iterations=iterations,
            batch_size=batch_size,
            status=status,
            details={
                "processing_times": processing_times,
                "memory_usages": memory_usages,
                "cpu_usages": cpu_usages,
                "success_rates": success_rates
            }
        )
    
    def _test_ai_analysis_performance(self, scenario: Dict) -> ScenarioResult:
        """Test AI analysis performance"""
        batch_size = scenario["batch_size"]
        iterations = scenario["iterations"]
        
        processing_times = []
        memory_usages = []
        error_count = 0
        
        # Create mock AI client and analysis data
        try:
            ai_client = AIClient()
        except ValueError:
            ai_client = self.test_data_generator.create_mock_ai_client()
        
        aggregator = AnalysisAggregator(ai_client, self.data_dir)
        
        for i in range(iterations):
            if PSUTIL_AVAILABLE:
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
            else:
                memory_before = 0
            
            start_time = time.time()
            
            try:
                # Create mock analysis data
                mock_results = self.test_data_generator.create_mock_low_confidence_results()
                
                # Extend data to match batch size
                extended_results = []
                for j in range(batch_size):
                    result = mock_results[j % len(mock_results)].copy()
                    result['item_id'] = f"test_ai_{i}_{j}"
                    extended_results.append(result)
                
                # Run analysis
                analysis_result = aggregator.analyze_batch_results(extended_results)
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                
                if PSUTIL_AVAILABLE:
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB
                    memory_usages.append(memory_after - memory_before)
                else:
                    memory_usages.append(0)
                
            except Exception as e:
                self.logger.error(f"Error in AI analysis iteration {i}: {e}")
                error_count += 1
                processing_times.append(0)
                memory_usages.append(0)
        
        # Calculate metrics
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        avg_memory_usage = statistics.mean(memory_usages) if memory_usages else 0
        throughput = (batch_size / avg_processing_time) if avg_processing_time > 0 else 0
        
        metrics = PerformanceMetrics(
            execution_time=avg_processing_time,
            memory_usage_mb=avg_memory_usage,
            cpu_usage_percent=0,  # Not measured for AI analysis
            throughput_items_per_second=throughput,
            success_rate=1.0 - (error_count / iterations) if iterations > 0 else 0,
            error_count=error_count
        )
        
        status = "passed" if error_count == 0 else "warning" if error_count < iterations / 2 else "failed"
        
        return ScenarioResult(
            scenario_name=scenario["name"],
            metrics=metrics,
            iterations=iterations,
            batch_size=batch_size,
            status=status,
            details={
                "processing_times": processing_times,
                "memory_usages": memory_usages
            }
        )
    
    def _test_confidence_scoring_performance(self, scenario: Dict) -> ScenarioResult:
        """Test confidence scoring performance"""
        batch_size = scenario["batch_size"]
        iterations = scenario["iterations"]
        
        processing_times = []
        error_count = 0
        
        confidence_system = ConfidenceScoringSystem()
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                # Create test data for confidence scoring
                test_results = self.test_data_generator.create_mock_processing_results()
                
                # Extend to match batch size
                extended_results = []
                for j in range(batch_size):
                    result = test_results[j % len(test_results)].copy()
                    result['item_id'] = f"test_conf_{i}_{j}"
                    extended_results.append(result)
                
                # Score all results
                scored_results = []
                for result in extended_results:
                    scored_result = confidence_system.score_and_categorize(result)
                    confidence_score = scored_result.get('confidence_score', 0.0)
                    scored_results.append(confidence_score)
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                
            except Exception as e:
                self.logger.error(f"Error in confidence scoring iteration {i}: {e}")
                error_count += 1
                processing_times.append(0)
        
        # Calculate metrics
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        throughput = (batch_size / avg_processing_time) if avg_processing_time > 0 else 0
        
        metrics = PerformanceMetrics(
            execution_time=avg_processing_time,
            memory_usage_mb=0,  # Not measured for confidence scoring
            cpu_usage_percent=0,
            throughput_items_per_second=throughput,
            success_rate=1.0 - (error_count / iterations) if iterations > 0 else 0,
            error_count=error_count
        )
        
        status = "passed" if error_count == 0 else "warning" if error_count < iterations / 2 else "failed"
        
        return ScenarioResult(
            scenario_name=scenario["name"],
            metrics=metrics,
            iterations=iterations,
            batch_size=batch_size,
            status=status,
            details={
                "processing_times": processing_times
            }
        )
    
    def _test_rule_management_performance(self, scenario: Dict) -> ScenarioResult:
        """Test rule management performance"""
        batch_size = scenario["batch_size"]  # Number of rules to create/manage
        iterations = scenario["iterations"]
        
        processing_times = []
        error_count = 0
        
        # Create test rule management system
        test_rules_dir = self.test_data_dir / f"perf_rules_{int(time.time())}"
        test_rules_dir.mkdir(exist_ok=True)
        
        rule_manager = RuleManager(test_rules_dir)
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                # Create multiple rules
                rule_ids = []
                for j in range(batch_size):
                    test_rule = self.test_data_generator.create_test_rule()
                    test_rule['rule_id'] = f"perf_rule_{i}_{j}"
                    test_rule['name'] = f"Performance Test Rule {i}-{j}"
                    
                    rule_id = rule_manager.add_rule(test_rule)
                    rule_ids.append(rule_id)
                
                # Retrieve all rules
                for rule_id in rule_ids:
                    retrieved_rule = rule_manager.get_rule(rule_id)
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                
            except Exception as e:
                self.logger.error(f"Error in rule management iteration {i}: {e}")
                error_count += 1
                processing_times.append(0)
        
        # Calculate metrics
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        throughput = (batch_size / avg_processing_time) if avg_processing_time > 0 else 0
        
        metrics = PerformanceMetrics(
            execution_time=avg_processing_time,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            throughput_items_per_second=throughput,
            success_rate=1.0 - (error_count / iterations) if iterations > 0 else 0,
            error_count=error_count
        )
        
        status = "passed" if error_count == 0 else "warning" if error_count < iterations / 2 else "failed"
        
        return ScenarioResult(
            scenario_name=scenario["name"],
            metrics=metrics,
            iterations=iterations,
            batch_size=batch_size,
            status=status,
            details={
                "processing_times": processing_times
            }
        )
    
    def _test_concurrent_processing_performance(self, scenario: Dict) -> ScenarioResult:
        """Test concurrent processing performance"""
        batch_size = scenario["batch_size"]
        iterations = scenario["iterations"]
        concurrent_batches = scenario.get("concurrent_batches", 3)
        
        processing_times = []
        error_count = 0
        
        # Initialize batch processing system
        mock_data_loader = self.test_data_generator.create_mock_data_loader()
        mock_description_generator = self.test_data_generator.create_mock_description_generator()
        
        batch_system = BatchProcessingSystem(
            mock_data_loader,
            mock_description_generator,
            self.settings
        )
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                # Create threads for concurrent processing
                threads = []
                results = []
                
                def process_batch_thread(thread_id):
                    try:
                        batch_config = BatchConfig(batch_size=batch_size)
                        result = batch_system.run_batch(batch_config)
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Concurrent batch {thread_id} failed: {e}")
                        results.append(None)
                
                # Start concurrent batches
                for j in range(concurrent_batches):
                    thread = threading.Thread(target=process_batch_thread, args=(j,))
                    threads.append(thread)
                    thread.start()
                
                # Wait for all threads to complete
                for thread in threads:
                    thread.join()
                
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                
                # Count errors
                batch_errors = len([r for r in results if r is None])
                if batch_errors > 0:
                    error_count += batch_errors
                
            except Exception as e:
                self.logger.error(f"Error in concurrent processing iteration {i}: {e}")
                error_count += 1
                processing_times.append(0)
        
        # Calculate metrics
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0
        total_items = batch_size * concurrent_batches
        throughput = (total_items / avg_processing_time) if avg_processing_time > 0 else 0
        
        metrics = PerformanceMetrics(
            execution_time=avg_processing_time,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            throughput_items_per_second=throughput,
            success_rate=1.0 - (error_count / (iterations * concurrent_batches)) if iterations > 0 else 0,
            error_count=error_count
        )
        
        status = "passed" if error_count == 0 else "warning" if error_count < (iterations * concurrent_batches) / 2 else "failed"
        
        return ScenarioResult(
            scenario_name=scenario["name"],
            metrics=metrics,
            iterations=iterations,
            batch_size=total_items,
            status=status,
            details={
                "processing_times": processing_times,
                "concurrent_batches": concurrent_batches
            }
        )
    
    def _generate_performance_summary(self, results: Dict[str, ScenarioResult]) -> Dict:
        """Generate performance summary across all scenarios"""
        if not results:
            return {"error": "No results to summarize"}
        
        all_execution_times = []
        all_throughputs = []
        all_success_rates = []
        
        for scenario_result in results.values():
            if scenario_result.status != "failed":
                all_execution_times.append(scenario_result.metrics.execution_time)
                all_throughputs.append(scenario_result.metrics.throughput_items_per_second)
                all_success_rates.append(scenario_result.metrics.success_rate)
        
        if not all_execution_times:
            return {"error": "No successful scenarios to summarize"}
        
        # Find best and worst performing scenarios
        best_throughput_scenario = max(results.keys(), 
                                     key=lambda k: results[k].metrics.throughput_items_per_second 
                                     if results[k].status != "failed" else 0)
        
        worst_throughput_scenario = min(results.keys(),
                                      key=lambda k: results[k].metrics.throughput_items_per_second
                                      if results[k].status != "failed" else float('inf'))
        
        return {
            "overall_avg_execution_time": statistics.mean(all_execution_times),
            "overall_avg_throughput": statistics.mean(all_throughputs),
            "overall_avg_success_rate": statistics.mean(all_success_rates),
            "best_throughput_scenario": best_throughput_scenario,
            "worst_throughput_scenario": worst_throughput_scenario,
            "total_scenarios_tested": len(results),
            "successful_scenarios": len([r for r in results.values() if r.status == "passed"]),
            "performance_grade": self._calculate_performance_grade(all_throughputs, all_success_rates)
        }
    
    def _calculate_performance_grade(self, throughputs: List[float], success_rates: List[float]) -> str:
        """Calculate overall performance grade"""
        if not throughputs or not success_rates:
            return "F"
        
        avg_throughput = statistics.mean(throughputs)
        avg_success_rate = statistics.mean(success_rates)
        
        # Simple grading based on throughput and success rate
        if avg_success_rate >= 0.95 and avg_throughput >= 10:
            return "A"
        elif avg_success_rate >= 0.9 and avg_throughput >= 5:
            return "B"
        elif avg_success_rate >= 0.8 and avg_throughput >= 2:
            return "C"
        elif avg_success_rate >= 0.7 and avg_throughput >= 1:
            return "D"
        else:
            return "F"
    
    def _save_performance_results(self, summary: Dict[str, Any]):
        """Save performance results to file"""
        try:
            import json
            
            results_file = self.test_data_dir / f"performance_test_results_{int(time.time())}.json"
            
            # Convert results to serializable format
            serializable_summary = summary.copy()
            serializable_scenarios = {}
            
            for scenario_name, result in summary.get('scenarios', {}).items():
                if isinstance(result, ScenarioResult):
                    serializable_scenarios[scenario_name] = {
                        'scenario_name': result.scenario_name,
                        'metrics': {
                            'execution_time': result.metrics.execution_time,
                            'memory_usage_mb': result.metrics.memory_usage_mb,
                            'cpu_usage_percent': result.metrics.cpu_usage_percent,
                            'throughput_items_per_second': result.metrics.throughput_items_per_second,
                            'success_rate': result.metrics.success_rate,
                            'error_count': result.metrics.error_count
                        },
                        'iterations': result.iterations,
                        'batch_size': result.batch_size,
                        'status': result.status,
                        'details': result.details
                    }
                else:
                    serializable_scenarios[scenario_name] = result
            
            serializable_summary['scenarios'] = serializable_scenarios
            
            with open(results_file, 'w') as f:
                json.dump(serializable_summary, f, indent=2, default=str)
            
            self.logger.info(f"Performance test results saved to {results_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save performance results: {e}")
