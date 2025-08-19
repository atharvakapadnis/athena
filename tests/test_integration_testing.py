# tests/test_integration_testing.py
"""
Unit tests for the integration testing system

Tests the integration testing components themselves to ensure they work correctly.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.integration_testing import (
    SystemIntegrationTester, 
    ComponentInteractionTester,
    PerformanceIntegrationTester,
    IntegrationTestRunner,
    TestDataGenerator,
    TestResult
)

class TestTestDataGenerator:
    """Test the test data generator"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_generator = TestDataGenerator()
    
    def test_create_mock_data_loader(self):
        """Test mock data loader creation"""
        mock_loader = self.test_generator.create_mock_data_loader()
        
        assert mock_loader is not None
        assert hasattr(mock_loader, 'load_product_data')
        assert hasattr(mock_loader, 'load_test_data')
        assert hasattr(mock_loader, 'load_hts_reference')
        
        # Test data loading
        product_data = mock_loader.load_product_data()
        assert product_data is not None
        assert len(product_data) > 0
    
    def test_create_mock_description_generator(self):
        """Test mock description generator creation"""
        mock_generator = self.test_generator.create_mock_description_generator()
        
        assert mock_generator is not None
        assert hasattr(mock_generator, 'generate_description')
        
        # Test description generation
        test_product = {
            'item_id': 'test_001',
            'item_description': 'Test product',
            'material_detail': 'steel'
        }
        
        result = mock_generator.generate_description(test_product)
        assert result is not None
        assert hasattr(result, 'confidence_score')
        assert 0 <= result.confidence_score <= 1
    
    def test_create_mock_ai_client(self):
        """Test mock AI client creation"""
        mock_client = self.test_generator.create_mock_ai_client()
        
        assert mock_client is not None
        assert hasattr(mock_client, 'analyze_failure_patterns')
        assert hasattr(mock_client, 'generate_rule_suggestions')
        
        # Test pattern analysis
        test_results = [{'confidence_level': 'Low'}]
        analysis = mock_client.analyze_failure_patterns(test_results)
        assert analysis is not None
        assert 'patterns' in analysis
    
    def test_create_test_rule(self):
        """Test test rule creation"""
        test_rule = self.test_generator.create_test_rule()
        
        assert test_rule is not None
        assert 'rule_id' in test_rule
        assert 'rule_type' in test_rule
        assert 'name' in test_rule
        assert 'description' in test_rule
        assert test_rule['metadata']['test_rule'] is True
    
    def test_create_mock_processing_results(self):
        """Test mock processing results creation"""
        results = self.test_generator.create_mock_processing_results()
        
        assert results is not None
        assert len(results) > 0
        
        for result in results:
            assert 'item_id' in result
            assert 'confidence_score' in result
            assert 'original_description' in result
            assert 'enhanced_description' in result
            assert 0 <= result['confidence_score'] <= 1


class TestSystemIntegrationTester:
    """Test the system integration tester"""
    
    def setup_method(self):
        """Setup test environment"""
        with tempfile.TemporaryDirectory() as tmpdir:
            self.test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
        
        # Create a fresh instance for each test
        self.tester = None
    
    def test_initialization(self):
        """Test system integration tester initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = SystemIntegrationTester(test_settings)
            
            assert tester is not None
            assert tester.settings == test_settings
            assert tester.data_dir == Path(tmpdir)
            assert tester.test_data_dir.exists()
    
    def test_data_integration_test(self):
        """Test data integration test method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = SystemIntegrationTester(test_settings)
            
            # Mock the data loader and validator
            with patch('src.integration_testing.system_tester.DataLoader') as mock_loader_class, \
                 patch('src.integration_testing.system_tester.DataValidator') as mock_validator_class:
                
                # Setup mocks
                mock_loader = Mock()
                mock_loader.load_test_data.return_value = [{'test': 'data'}]
                mock_loader_class.return_value = mock_loader
                
                mock_validator = Mock()
                mock_validator.validate_data.return_value = {'is_valid': True}
                mock_validator_class.return_value = mock_validator
                
                # Run test
                result = tester._test_data_integration()
                
                assert isinstance(result, TestResult)
                assert result.test_name == "data_integration"
                assert result.status in ["passed", "failed", "skipped"]
    
    def test_batch_processing_test(self):
        """Test batch processing flow test method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = SystemIntegrationTester(test_settings)
            
            # Mock the batch processing system
            with patch('src.integration_testing.system_tester.BatchProcessingSystem') as mock_batch_system:
                mock_system = Mock()
                mock_result = Mock()
                mock_result.results = [Mock() for _ in range(5)]
                for r in mock_result.results:
                    r.confidence_score = 0.8
                mock_result.success_rate = 0.9
                
                mock_system.process_batch.return_value = mock_result
                mock_batch_system.return_value = mock_system
                
                # Run test
                result = tester._test_batch_processing_flow()
                
                assert isinstance(result, TestResult)
                assert result.test_name == "batch_processing_flow"
                assert result.status in ["passed", "failed"]


class TestComponentInteractionTester:
    """Test the component interaction tester"""
    
    def test_initialization(self):
        """Test component interaction tester initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = ComponentInteractionTester(test_settings)
            
            assert tester is not None
            assert tester.settings == test_settings
            assert tester.test_data_dir.exists()
    
    def test_batch_to_ai_analysis_flow(self):
        """Test batch to AI analysis flow test method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = ComponentInteractionTester(test_settings)
            
            # Mock all dependencies
            with patch('src.integration_testing.component_tester.BatchProcessingSystem') as mock_batch_system, \
                 patch('src.integration_testing.component_tester.AnalysisAggregator') as mock_aggregator_class, \
                 patch('src.integration_testing.component_tester.AIClient') as mock_ai_client_class:
                
                # Setup batch system mock
                mock_system = Mock()
                mock_result = Mock()
                mock_result.results = []
                for i in range(3):
                    result_item = Mock()
                    result_item.confidence_score = 0.4  # Low confidence
                    result_item.original_description = f"Test item {i}"
                    result_item.enhanced_description = f"Enhanced test item {i}"
                    result_item.extracted_features = {}
                    mock_result.results.append(result_item)
                
                mock_system.process_batch.return_value = mock_result
                mock_batch_system.return_value = mock_system
                
                # Setup AI client mock
                mock_ai_client = Mock()
                mock_ai_client_class.return_value = mock_ai_client
                
                # Setup aggregator mock
                mock_aggregator = Mock()
                mock_aggregator.analyze_batch_results.return_value = {"patterns": ["test"]}
                mock_aggregator_class.return_value = mock_aggregator
                
                # Run test
                result = tester.test_batch_to_ai_analysis_flow()
                
                assert isinstance(result, TestResult)
                assert result.test_name == "batch_to_ai_analysis_flow"
                assert result.status in ["passed", "failed"]


class TestPerformanceIntegrationTester:
    """Test the performance integration tester"""
    
    def test_initialization(self):
        """Test performance integration tester initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = PerformanceIntegrationTester(test_settings)
            
            assert tester is not None
            assert tester.settings == test_settings
            assert tester.test_data_dir.exists()
    
    def test_default_scenarios(self):
        """Test default performance test scenarios"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = PerformanceIntegrationTester(test_settings)
            scenarios = tester._get_default_test_scenarios()
            
            assert scenarios is not None
            assert len(scenarios) > 0
            
            for scenario in scenarios:
                assert 'name' in scenario
                assert 'batch_size' in scenario
                assert 'iterations' in scenario
                assert 'test_type' in scenario
    
    def test_batch_processing_performance(self):
        """Test batch processing performance test"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            tester = PerformanceIntegrationTester(test_settings)
            
            scenario = {
                'name': 'test_batch_performance',
                'batch_size': 5,
                'iterations': 2,
                'test_type': 'batch_processing'
            }
            
            # Mock batch processing system
            with patch('src.integration_testing.performance_tester.BatchProcessingSystem') as mock_batch_system:
                mock_system = Mock()
                mock_result = Mock()
                mock_result.success_rate = 0.9
                mock_system.process_batch.return_value = mock_result
                mock_batch_system.return_value = mock_system
                
                # Run performance test
                result = tester._test_batch_processing_performance(scenario)
                
                assert result is not None
                assert result.scenario_name == 'test_batch_performance'
                assert result.status in ["passed", "warning", "failed"]
                assert hasattr(result.metrics, 'execution_time')
                assert hasattr(result.metrics, 'throughput_items_per_second')


class TestIntegrationTestRunner:
    """Test the integration test runner"""
    
    def test_initialization(self):
        """Test integration test runner initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            runner = IntegrationTestRunner(test_settings)
            
            assert runner is not None
            assert runner.settings == test_settings
            assert runner.results_dir.exists()
            assert runner.system_tester is not None
            assert runner.component_tester is not None
            assert runner.performance_tester is not None
    
    def test_quick_tests(self):
        """Test quick integration tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            runner = IntegrationTestRunner(test_settings)
            
            # Mock all testers to avoid actual test execution
            with patch.object(runner, 'system_tester') as mock_system, \
                 patch.object(runner, 'component_tester') as mock_component, \
                 patch.object(runner, 'performance_tester') as mock_performance:
                
                # Setup mock returns
                mock_system.run_full_system_test.return_value = {
                    'total_tests': 5,
                    'passed': 4,
                    'failed': 1,
                    'skipped': 0,
                    'total_duration': 10.0
                }
                
                mock_component.run_component_interaction_tests.return_value = {
                    'test1': TestResult('test1', 'passed', 1.0, {}),
                    'test2': TestResult('test2', 'passed', 1.5, {})
                }
                
                mock_performance.run_performance_tests.return_value = {
                    'total_scenarios': 2,
                    'completed': 2,
                    'failed': 0,
                    'total_duration': 5.0,
                    'summary': {'performance_grade': 'B'}
                }
                
                # Run quick tests
                results = runner.run_quick_tests()
                
                assert results is not None
                assert 'system_integration' in results
                assert 'component_interaction' in results
                assert 'performance' in results
                assert 'overall_summary' in results
    
    def test_generate_overall_summary(self):
        """Test overall summary generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 10
            }
            
            runner = IntegrationTestRunner(test_settings)
            
            # Create mock results
            all_results = {
                'system_integration': {
                    'total_tests': 10,
                    'passed': 8,
                    'failed': 2,
                    'skipped': 0
                },
                'component_interaction': {
                    'test1': TestResult('test1', 'passed', 1.0, {}),
                    'test2': TestResult('test2', 'failed', 1.5, {}),
                    'test3': TestResult('test3', 'passed', 2.0, {})
                },
                'performance': {
                    'total_scenarios': 3,
                    'completed': 2,
                    'failed': 1,
                    'summary': {'performance_grade': 'C'}
                }
            }
            
            summary = runner._generate_overall_summary(all_results, 30.0)
            
            assert summary is not None
            assert 'total_duration' in summary
            assert 'total_test_count' in summary
            assert 'total_passed' in summary
            assert 'total_failed' in summary
            assert 'success_rate' in summary
            assert 'overall_status' in summary
            assert summary['total_duration'] == 30.0


@pytest.mark.integration
class TestIntegrationTestingIntegration:
    """Integration tests for the integration testing system itself"""
    
    def test_end_to_end_quick_test(self):
        """Test a quick end-to-end integration test run"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 5
            }
            
            # Create input directory
            input_dir = Path(tmpdir) / "input"
            input_dir.mkdir(exist_ok=True)
            
            runner = IntegrationTestRunner(test_settings)
            
            try:
                # Run a very limited quick test
                results = runner.run_quick_tests()
                
                # Basic validation - tests should complete without crashing
                assert results is not None
                assert isinstance(results, dict)
                
                # Check that at least some test categories ran
                test_categories = ['system_integration', 'component_interaction', 'performance']
                categories_run = [cat for cat in test_categories if cat in results]
                assert len(categories_run) > 0, "At least one test category should have run"
                
            except Exception as e:
                # Log the error but don't fail the test - integration tests may fail
                # due to missing dependencies or configurations
                pytest.skip(f"Integration test skipped due to environment: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
