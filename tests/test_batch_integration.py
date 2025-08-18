# tests/test_batch_integration.py
import pytest
from pathlib import Path
import tempfile

from src.batch_processor import BatchProcessingSystem, BatchConfig
from src.utils.data_loader import DataLoader
from src.utils.smart_description_generator import SmartDescriptionGenerator
from src.utils.hts_hierarchy import HTSHierarchy
from src.utils.config import get_project_settings

class TestBatchIntegration:
    """Test batch processing integration with real data"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test environment with real data"""
        try:
            # Try to use real data if available
            self.settings = get_project_settings()
            self.data_loader = DataLoader()
            
            # Check if test data exists
            test_data_path = Path(self.settings['input_dir']) / 'cleaned_test_ch73.csv'
            hts_data_path = Path(self.settings['input_dir']) / 'htsdata_ch73.json'
            
            if not test_data_path.exists() or not hts_data_path.exists():
                pytest.skip("Test data files not available")
            
            # Load real data
            self.df = self.data_loader.load_product_data()
            self.hts_data = self.data_loader.load_hts_reference()
            
            # Initialize components
            self.hts_hierarchy = HTSHierarchy(self.hts_data)
            self.description_generator = SmartDescriptionGenerator(self.hts_hierarchy)
            
            # Create batch system with temporary directory for test outputs
            self.test_settings = self.settings.copy()
            
        except Exception as e:
            pytest.skip(f"Could not setup integration test environment: {e}")
    
    def test_small_batch_processing(self):
        """Test processing a small batch with real data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use temporary directory for test outputs
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            config = BatchConfig(batch_size=5, start_index=0)
            
            batch_result = batch_system.run_batch(config)
            
            # Basic validation
            assert batch_result.total_items == 5
            assert batch_result.successful_items > 0
            assert batch_result.confidence_distribution['High'] + \
                   batch_result.confidence_distribution['Medium'] + \
                   batch_result.confidence_distribution['Low'] == 5
            
            # Check that processing time is reasonable
            assert batch_result.processing_time > 0
            assert batch_result.processing_time < 60  # Should complete within 1 minute
    
    def test_confidence_distribution_realistic(self):
        """Test that confidence distribution is reasonable with real data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            config = BatchConfig(batch_size=10, start_index=0)
            
            batch_result = batch_system.run_batch(config)
            
            # Should have variation in confidence levels with real data
            total_items = sum(batch_result.confidence_distribution.values())
            assert total_items == 10
            
            # Should have at least some successful processing
            assert batch_result.successful_items >= 5  # At least 50% success rate
            
            # Should have some high or medium confidence results
            high_medium_count = (batch_result.confidence_distribution['High'] + 
                               batch_result.confidence_distribution['Medium'])
            assert high_medium_count > 0
    
    def test_progress_tracking_with_real_data(self):
        """Test progress tracking functionality with real data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            # Run a small batch
            config = BatchConfig(batch_size=3, start_index=0)
            batch_system.run_batch(config)
            
            # Check progress
            progress = batch_system.get_progress()
            
            assert progress['total_batches'] > 0
            assert progress['completed_batches'] > 0
            assert progress['total_items_processed'] > 0
            assert 0 <= progress['success_rate'] <= 1
            assert 0 <= progress['high_confidence_rate'] <= 1
    
    def test_batch_results_persistence(self):
        """Test that batch results are properly saved and retrievable"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            # Run a batch
            config = BatchConfig(batch_size=3, start_index=0)
            batch_result = batch_system.run_batch(config)
            
            batch_id = batch_result.batch_id
            
            # Verify batch is listed
            batches = batch_system.list_batches()
            assert len(batches) > 0
            
            batch_ids = [b['batch_id'] for b in batches]
            assert batch_id in batch_ids
            
            # Verify batch results can be retrieved
            retrieved_result = batch_system.get_batch_results(batch_id)
            assert retrieved_result is not None
            assert retrieved_result['batch_id'] == batch_id
    
    def test_multiple_batches_processing(self):
        """Test processing multiple consecutive batches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            # Run multiple small batches
            batch_results = []
            for i in range(2):
                config = BatchConfig(batch_size=2, start_index=i*2)
                result = batch_system.run_batch(config)
                batch_results.append(result)
            
            # Verify all batches processed
            assert len(batch_results) == 2
            
            # Check overall progress
            progress = batch_system.get_progress()
            assert progress['total_batches'] == 2
            assert progress['completed_batches'] == 2
            assert progress['total_items_processed'] == 4
    
    def test_performance_metrics_collection(self):
        """Test that performance metrics are collected properly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            # Run a batch
            config = BatchConfig(batch_size=5, start_index=0)
            batch_system.run_batch(config)
            
            # Get performance metrics
            metrics_df = batch_system.get_performance_metrics()
            
            # Should have at least one row of metrics
            assert len(metrics_df) > 0
            
            # Check required columns exist
            required_columns = ['total_items', 'successful_items', 'success_rate', 
                              'high_confidence_rate', 'avg_processing_time']
            for col in required_columns:
                assert col in metrics_df.columns
            
            # Verify metrics are reasonable
            assert all(metrics_df['success_rate'] >= 0)
            assert all(metrics_df['success_rate'] <= 1)
            assert all(metrics_df['high_confidence_rate'] >= 0)
            assert all(metrics_df['high_confidence_rate'] <= 1)
    
    def test_error_resilience_with_real_data(self):
        """Test that the system handles edge cases in real data gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            # Try to process from near the end of dataset
            dataset_size = len(self.df)
            config = BatchConfig(batch_size=5, start_index=max(0, dataset_size-3))
            
            # This should handle edge cases like trying to get more items than available
            batch_result = batch_system.run_batch(config)
            
            # Should process available items without error
            assert batch_result.total_items > 0
            assert batch_result.total_items <= 5  # Should not exceed requested size
            assert batch_result.total_items <= 3   # Should not exceed available items
    
    @pytest.mark.skipif(not Path("data/input/cleaned_test_ch73.csv").exists(),
                       reason="Large dataset test requires full dataset")
    def test_larger_batch_performance(self):
        """Test performance with larger batch size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = self.test_settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                test_settings
            )
            
            # Test with larger batch size
            config = BatchConfig(batch_size=20, start_index=0)
            batch_result = batch_system.run_batch(config)
            
            # Should complete within reasonable time
            assert batch_result.processing_time < 120  # 2 minutes max
            
            # Should maintain reasonable success rate
            success_rate = batch_result.successful_items / batch_result.total_items
            assert success_rate >= 0.7  # At least 70% success rate
