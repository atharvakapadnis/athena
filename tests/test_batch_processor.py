# tests/test_batch_processor.py
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import json
from datetime import datetime

from src.batch_processor import BatchProcessingSystem, BatchConfig
from src.batch_processor.processor import BatchProcessor
from src.batch_processor.batch_manager import BatchManager, BatchStatus
from src.batch_processor.progress_tracker import ProgressTracker
from src.utils.smart_description_generator import DescriptionResult

class TestBatchProcessor:
    """Test batch processing functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_data_loader = Mock()
        self.mock_description_generator = Mock()
        self.mock_settings = {
            'data_dir': str(Path.cwd() / 'test_data'),
            'batches_dir': str(Path.cwd() / 'test_data' / 'batches'),
            'batch_size': 50
        }
        
        # Mock sample data
        self.sample_products = [
            {
                'item_id': 'test_1',
                'item_description': '36 C153 MJ 22 TN431 ZINC',
                'final_hts': '7307.19.30.70',
                'material_detail': 'ductile iron'
            },
            {
                'item_id': 'test_2', 
                'item_description': 'SMITH BLAIR 170008030 SPACER, 18" ; DI ;',
                'final_hts': '7307.19.30.70',
                'material_detail': 'ductile iron'
            }
        ]
        
        self.mock_data_loader.load_product_data.return_value = pd.DataFrame(self.sample_products)
    
    def test_batch_creation(self):
        """Test batch creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {**self.mock_settings, 'batches_dir': tmpdir}
            
            batch_manager = BatchManager(self.mock_data_loader, settings)
            config = BatchConfig(batch_size=2)
            
            batch_id = batch_manager.create_batch(config)
            
            assert batch_id is not None
            assert len(batch_id) > 0
            
            # Verify batch files created
            batch_data, batch_metadata = batch_manager.load_batch(batch_id)
            assert len(batch_data) == 2
            assert batch_metadata['batch_id'] == batch_id
    
    def test_batch_processing(self):
        """Test batch processing"""
        processor = BatchProcessor(self.mock_description_generator)
        
        # Mock description generation
        mock_result = DescriptionResult(
            original_description='test',
            enhanced_description='enhanced test',
            confidence_score=0.8,
            confidence_level='High',
            extracted_features={'test': 'feature'},
            hts_context={'hts_code': '7307.19.30.70'},
            processing_metadata={'timestamp': datetime.now().isoformat()}
        )
        
        self.mock_description_generator.generate_description.return_value = mock_result
        
        config = BatchConfig()
        batch_result = processor.process_batch(self.sample_products, config)
        
        assert batch_result.total_items == 2
        assert batch_result.successful_items == 2
        assert batch_result.confidence_distribution['High'] == 2
    
    def test_batch_processing_with_failures(self):
        """Test batch processing with some failures"""
        processor = BatchProcessor(self.mock_description_generator)
        
        # Mock one success, one failure
        def mock_generate(product_data):
            if product_data['item_id'] == 'test_1':
                return DescriptionResult(
                    original_description='test',
                    enhanced_description='enhanced test',
                    confidence_score=0.8,
                    confidence_level='High',
                    extracted_features={'test': 'feature'},
                    hts_context={'hts_code': '7307.19.30.70'},
                    processing_metadata={'timestamp': datetime.now().isoformat()}
                )
            else:
                raise Exception("Processing failed")
        
        self.mock_description_generator.generate_description.side_effect = mock_generate
        
        config = BatchConfig()
        batch_result = processor.process_batch(self.sample_products, config)
        
        assert batch_result.total_items == 2
        assert batch_result.successful_items == 1
        assert batch_result.failed_items == 1
        assert batch_result.confidence_distribution['High'] == 1
        assert batch_result.confidence_distribution['Low'] == 1
    
    def test_batch_status_tracking(self):
        """Test batch status tracking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {**self.mock_settings, 'batches_dir': tmpdir}
            
            batch_manager = BatchManager(self.mock_data_loader, settings)
            
            # Create a batch
            config = BatchConfig(batch_size=2)
            batch_id = batch_manager.create_batch(config)
            
            # Create and update status
            status = BatchStatus(
                batch_id=batch_id,
                status='processing',
                total_items=2,
                processed_items=0,
                successful_items=0,
                failed_items=0,
                high_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
                start_time=datetime.now()
            )
            
            batch_manager.update_batch_status(batch_id, status)
            
            # Retrieve status
            retrieved_status = batch_manager.get_batch_status(batch_id)
            
            assert retrieved_status is not None
            assert retrieved_status.batch_id == batch_id
            assert retrieved_status.status == 'processing'
            assert retrieved_status.total_items == 2
    
    def test_progress_tracking(self):
        """Test progress tracking functionality"""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_tracker = ProgressTracker(Path(tmpdir))
            
            # Add some test data
            batch_result = {
                'batch_id': 'test_batch_1',
                'total_items': 10,
                'successful_items': 8,
                'failed_items': 2,
                'confidence_distribution': {'High': 5, 'Medium': 3, 'Low': 2},
                'processing_time': 15.5
            }
            
            progress_tracker.add_to_history(batch_result)
            
            # Get overall progress
            progress = progress_tracker.get_overall_progress()
            
            assert progress['total_items_processed'] == 10
            assert progress['successful_items'] == 8
            assert progress['success_rate'] == 0.8

class TestBatchIntegration:
    """Test batch processing integration"""
    
    def setup_method(self):
        """Setup test environment with mocked components"""
        self.mock_data_loader = Mock()
        self.mock_description_generator = Mock()
        self.settings = {
            'data_dir': str(Path.cwd() / 'test_data'),
            'batches_dir': str(Path.cwd() / 'test_data' / 'batches'),
            'batch_size': 50
        }
        
        # Mock sample data
        self.sample_products = [
            {
                'item_id': 'test_1',
                'item_description': '36 C153 MJ 22 TN431 ZINC',
                'final_hts': '7307.19.30.70',
                'material_detail': 'ductile iron'
            },
            {
                'item_id': 'test_2', 
                'item_description': 'SMITH BLAIR 170008030 SPACER, 18" ; DI ;',
                'final_hts': '7307.19.30.70',
                'material_detail': 'ductile iron'
            },
            {
                'item_id': 'test_3',
                'item_description': 'MUELLER 12 COUPLING FLG DI',
                'final_hts': '7307.19.30.70',
                'material_detail': 'ductile iron'
            }
        ]
        
        self.mock_data_loader.load_product_data.return_value = pd.DataFrame(self.sample_products)
    
    def test_complete_batch_processing_cycle(self):
        """Test complete batch processing cycle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {**self.settings, 'data_dir': tmpdir, 'batches_dir': f"{tmpdir}/batches"}
            
            # Mock description generation with varying confidence
            def mock_generate(product_data):
                confidence_scores = [0.9, 0.6, 0.3]  # High, Medium, Low
                confidence_levels = ['High', 'Medium', 'Low']
                idx = int(product_data['item_id'].split('_')[1]) - 1
                
                return DescriptionResult(
                    original_description=product_data['item_description'],
                    enhanced_description=f"Enhanced {product_data['item_description']}",
                    confidence_score=confidence_scores[idx],
                    confidence_level=confidence_levels[idx],
                    extracted_features={'product_type': 'fitting'},
                    hts_context={'hts_code': product_data['final_hts']},
                    processing_metadata={'timestamp': datetime.now().isoformat()}
                )
            
            self.mock_description_generator.generate_description.side_effect = mock_generate
            
            # Create batch system
            batch_system = BatchProcessingSystem(
                self.mock_data_loader,
                self.mock_description_generator,
                settings
            )
            
            # Run a batch
            config = BatchConfig(batch_size=3)
            batch_result = batch_system.run_batch(config)
            
            # Verify results
            assert batch_result.total_items == 3
            assert batch_result.successful_items == 3
            assert batch_result.confidence_distribution['High'] == 1
            assert batch_result.confidence_distribution['Medium'] == 1
            assert batch_result.confidence_distribution['Low'] == 1
            
            # Check progress tracking
            progress = batch_system.get_progress()
            assert progress['total_items_processed'] == 3
            assert progress['successful_items'] == 3
    
    def test_confidence_distribution(self):
        """Test that confidence distribution is calculated correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {**self.settings, 'data_dir': tmpdir, 'batches_dir': f"{tmpdir}/batches"}
            
            # Mock all high confidence results
            mock_result = DescriptionResult(
                original_description='test',
                enhanced_description='enhanced test',
                confidence_score=0.9,
                confidence_level='High',
                extracted_features={'product_type': 'fitting'},
                hts_context={'hts_code': '7307.19.30.70'},
                processing_metadata={'timestamp': datetime.now().isoformat()}
            )
            
            self.mock_description_generator.generate_description.return_value = mock_result
            
            batch_system = BatchProcessingSystem(
                self.mock_data_loader,
                self.mock_description_generator,
                settings
            )
            
            config = BatchConfig(batch_size=3)
            batch_result = batch_system.run_batch(config)
            
            # Should have all high confidence results
            total_items = sum(batch_result.confidence_distribution.values())
            assert total_items == 3
            assert batch_result.confidence_distribution['High'] == 3
            assert batch_result.confidence_distribution['Medium'] == 0
            assert batch_result.confidence_distribution['Low'] == 0
    
    def test_error_handling(self):
        """Test error handling in batch processing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = {**self.settings, 'data_dir': tmpdir, 'batches_dir': f"{tmpdir}/batches"}
            
            # Mock description generator to raise exception
            self.mock_description_generator.generate_description.side_effect = Exception("Test error")
            
            batch_system = BatchProcessingSystem(
                self.mock_data_loader,
                self.mock_description_generator,
                settings
            )
            
            config = BatchConfig(batch_size=3)
            
            # This should not raise an exception, but handle it gracefully
            batch_result = batch_system.run_batch(config)
            
            assert batch_result.total_items == 3
            assert batch_result.successful_items == 0
            assert batch_result.failed_items == 3
            assert batch_result.confidence_distribution['Low'] == 3
