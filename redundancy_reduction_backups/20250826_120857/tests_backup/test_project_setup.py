"""
Test project setup and basic functionality
"""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import validate_environment, get_project_settings, ensure_directories
from utils.data_loader import DataLoader
from utils.logger import setup_logging, get_logger

class TestProjectSetup:
    """Test that the project setup is working correctly"""
    
    def test_configuration_validation(self):
        """Test that configuration validation works"""
        try:
            # This will fail if environment is not set up correctly
            validate_environment()
            assert True, "Environment validation passed"
        except ValueError as e:
            pytest.fail(f"Environment validation failed: {e}")
    
    def test_project_settings(self):
        """Test that project settings can be retrieved"""
        settings = get_project_settings()
        
        # Check required settings
        required_keys = [
            'project_root', 'data_dir', 'input_dir', 'batches_dir',
            'rules_dir', 'logs_dir', 'metrics_dir', 'batch_size'
        ]
        
        for key in required_keys:
            assert key in settings, f"Missing setting: {key}"
        
        # Check data types
        assert isinstance(settings['batch_size'], int)
        assert isinstance(settings['confidence_threshold_high'], float)
    
    def test_directory_creation(self):
        """Test that directories can be created"""
        try:
            ensure_directories()
            assert True, "Directory creation successful"
        except Exception as e:
            pytest.fail(f"Directory creation failed: {e}")
    
    def test_logging_setup(self):
        """Test that logging can be set up"""
        try:
            setup_logging(log_level="INFO")
            logger = get_logger("test")
            logger.info("Test log message")
            assert True, "Logging setup successful"
        except Exception as e:
            pytest.fail(f"Logging setup failed: {e}")
    
    def test_data_loader_initialization(self):
        """Test that data loader can be initialized"""
        try:
            loader = DataLoader()
            assert loader is not None, "DataLoader created successfully"
        except Exception as e:
            pytest.fail(f"DataLoader initialization failed: {e}")
    
    def test_data_loading(self):
        """Test that data can be loaded"""
        try:
            loader = DataLoader()
            
            # Load product data
            df = loader.load_product_data()
            assert len(df) > 0, "Product data loaded successfully"
            
            # Load HTS reference
            hts_data = loader.load_hts_reference()
            assert len(hts_data) > 0, "HTS reference data loaded successfully"
            
            # Get data summary
            summary = loader.get_data_summary()
            assert 'products' in summary, "Data summary generated successfully"
            
        except Exception as e:
            pytest.fail(f"Data loading failed: {e}")
    
    def test_sample_data_retrieval(self):
        """Test that sample data can be retrieved"""
        try:
            loader = DataLoader()
            loader.load_product_data()
            
            sample = loader.get_sample_products(n=5)
            assert len(sample) == 5, "Sample data retrieved successfully"
            
            # Check sample structure
            if sample:
                sample_item = sample[0]
                required_fields = ['item_id', 'item_description', 'final_hts']
                for field in required_fields:
                    assert field in sample_item, f"Sample item missing field: {field}"
                    
        except Exception as e:
            pytest.fail(f"Sample data retrieval failed: {e}")

def test_imports():
    """Test that all modules can be imported"""
    try:
        from utils.config import validate_environment
        from utils.data_loader import DataLoader
        from utils.logger import setup_logging
        from utils.debug import save_debug_data
        assert True, "All imports successful"
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")

if __name__ == "__main__":
    # Run basic tests
    print("Running project setup tests...")
    
    # Test configuration
    try:
        validate_environment()
        print("✅ Environment validation passed")
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
    
    # Test data loading
    try:
        loader = DataLoader()
        df = loader.load_product_data()
        hts_data = loader.load_hts_reference()
        print(f"✅ Data loading successful: {len(df)} products, {len(hts_data)} HTS codes")
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
    
    # Test logging
    try:
        setup_logging()
        logger = get_logger("test")
        logger.info("Test message")
        print("✅ Logging setup successful")
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
    
    print("Project setup tests completed")
