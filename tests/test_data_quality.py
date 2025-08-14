"""
Data quality tests for Smart Description Iterative Improvement System
"""
import pytest
import pandas as pd
from src.utils.data_validator import DataValidator
from src.utils.config import get_project_settings

class TestDataQuality:
    """Test data quality and validation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.settings = get_project_settings()
        self.validator = DataValidator()
    
    def test_product_data_quality(self):
        """Test product data quality validation"""
        # Load sample data
        from src.utils.data_loader import DataLoader
        loader = DataLoader()
        df = loader.load_product_data()
        
        results = self.validator.validate_product_data(df)
        
        assert results['total_products'] > 0
        assert results['data_quality_score'] >= 0.0 and results['data_quality_score'] <= 1.0
        assert results['valid_hts_codes'] > 0
        
        # Should have high quality score for production data
        assert results['data_quality_score'] >= 0.8, f"Data quality score too low: {results['data_quality_score']}"
    
    def test_hts_reference_quality(self):
        """Test HTS reference quality validation"""
        # Load sample data
        from src.utils.data_loader import DataLoader
        loader = DataLoader()
        hts_data = loader.load_hts_reference()
        
        results = self.validator.validate_hts_reference(hts_data)
        
        assert results['total_codes'] > 0
        assert results['valid_hierarchy'] == True
        
        # Should have no missing descriptions
        assert results['missing_descriptions'] == 0, f"Missing descriptions: {results['missing_descriptions']}"
    
    def test_hts_code_format(self):
        """Test HTS code format validation"""
        # Test valid HTS codes
        valid_codes = ['7301.10.00.00', '7301.20.00.00', '7302.10.00.00']
        for code in valid_codes:
            assert self.validator.hts_pattern.match(code), f"Valid HTS code failed: {code}"
        
        # Test invalid HTS codes
        invalid_codes = ['7301.10', '7301.10.00', '7301.10.00.00.00', 'abc.def.gh.ij']
        for code in invalid_codes:
            assert not self.validator.hts_pattern.match(code), f"Invalid HTS code passed: {code}"
    
    def test_data_summary_generation(self):
        """Test data summary generation"""
        # Load sample data
        from src.utils.data_loader import DataLoader
        loader = DataLoader()
        df = loader.load_product_data()
        hts_data = loader.load_hts_reference()
        
        summary = self.validator.get_data_summary(df, hts_data)
        
        assert 'products' in summary
        assert 'hts_reference' in summary
        assert summary['products']['total'] > 0
        assert summary['products']['unique_hts_codes'] > 0
        assert summary['hts_reference']['total_codes'] > 0
        assert len(summary['hts_reference']['chapters']) > 0
    
    def test_missing_data_handling(self):
        """Test handling of missing data"""
        # Create test data with missing values
        test_data = pd.DataFrame({
            'item_id': ['1', '2', '3'],
            'item_description': ['Test 1', None, 'Test 3'],
            'final_hts': ['7301.10.00.00', '7301.20.00.00', 'invalid_code'],
            'material_class': ['Iron', 'Steel', 'Iron'],
            'material_detail': ['Ductile Iron', 'Carbon Steel', 'Ductile Iron']
        })
        
        results = self.validator.validate_product_data(test_data)
        
        assert results['missing_descriptions'] == 1
        assert results['valid_hts_codes'] == 2  # One invalid code
        assert results['data_quality_score'] < 1.0  # Should be lower due to issues
