"""
Integration tests for data integration phase
"""
import pytest
import pandas as pd
from src.utils.data_loader import DataLoader
from src.utils.smart_description_generator import SmartDescriptionGenerator
from src.utils.hts_hierarchy import HTSHierarchy

class TestDataIntegration:
    """Test data integration and system compatibility"""
    
    def setup_method(self):
        """Setup test environment"""
        self.loader = DataLoader()
        self.df = self.loader.load_product_data()
        self.hts_data = self.loader.load_hts_reference()
        self.hts_hierarchy = HTSHierarchy(self.hts_data)
        self.generator = SmartDescriptionGenerator(self.hts_hierarchy)
    
    def test_data_loading(self):
        """Test that data loads correctly"""
        assert len(self.df) > 0, "Should load product data"
        assert len(self.hts_data) > 0, "Should load HTS reference"
        
        # Check required columns
        required_columns = ['item_id', 'item_description', 'final_hts', 'material_detail']
        for col in required_columns:
            assert col in self.df.columns, f"Missing required column: {col}"
    
    def test_hts_validation(self):
        """Test HTS code validation"""
        # Check HTS code format
        hts_pattern = r'^\d{4}\.\d{2}\.\d{2}\.\d{2}$'
        valid_hts = self.df['final_hts'].astype(str).str.match(hts_pattern)
        assert valid_hts.all(), "All HTS codes should match expected format"
    
    def test_description_generation(self):
        """Test description generation with sample data"""
        # Test with first product
        sample_product = self.df.iloc[0].to_dict()
        result = self.generator.generate_description(sample_product)
        
        assert result.original_description == sample_product['item_description']
        assert len(result.enhanced_description) > 0
        assert result.confidence_score >= 0.0 and result.confidence_score <= 1.0
        assert result.confidence_level in ["High", "Medium", "Low"]
    
    def test_confidence_distribution(self):
        """Test confidence score distribution"""
        results = []
        scores = []
        for i in range(min(20, len(self.df))):  # Test first 20 products
            product = self.df.iloc[i].to_dict()
            result = self.generator.generate_description(product)
            results.append(result.confidence_level)
            scores.append(result.confidence_score)
        
        # Should have some variation in confidence levels OR reasonable confidence scores
        unique_levels = set(results)
        avg_score = sum(scores) / len(scores)
        
        # Pass if we have variation OR if average confidence is reasonable
        assert len(unique_levels) > 1 or avg_score >= 0.3, f"Should have variation in confidence levels or reasonable scores. Levels: {unique_levels}, Avg score: {avg_score:.2f}"
    
    def test_feature_extraction(self):
        """Test feature extraction capabilities"""
        # Test with known pattern
        test_description = "36 C153 MJ 22 TN431 ZINC"
        parsed = self.generator._parse_product_description(test_description)
        
        # Should extract dimensions or specifications
        assert 'dimensions' in parsed or 'specification' in parsed, "Should extract features"
    
    def test_data_summary(self):
        """Test data summary generation"""
        summary = self.loader.get_data_summary()
        
        assert 'products' in summary
        assert 'hts_reference' in summary
        assert summary['products']['total'] > 0
        assert summary['hts_reference']['total_codes'] > 0
    
    def test_validation_results(self):
        """Test data validation results"""
        # Test product data validation
        validation_results = self.loader.validator.validate_product_data(self.df)
        assert validation_results['total_products'] > 0
        assert validation_results['data_quality_score'] >= 0.0 and validation_results['data_quality_score'] <= 1.0
        
        # Test HTS reference validation
        hts_validation = self.loader.validator.validate_hts_reference(self.hts_data)
        assert hts_validation['total_codes'] > 0
        assert hts_validation['valid_hierarchy'] == True
