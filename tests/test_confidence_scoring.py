# tests/test_confidence_scoring.py
import pytest
import numpy as np
from src.confidence_scoring import (
    ConfidenceScorer, 
    ConfidenceCategorizer, 
    ConfidenceLevel,
    ConfidenceThresholds,
    QualityValidator,
    ConfidenceCalibrator,
    ConfidenceScoringSystem,
    ConfidenceFactors
)

class TestConfidenceScorer:
    """Test confidence scoring functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.scorer = ConfidenceScorer()
    
    def test_confidence_scoring_basic(self):
        """Test basic confidence score calculation"""
        result = {
            'original_description': '36 C153 MJ 22 TN431 ZINC',
            'enhanced_description': '36-inch Ductile Iron Pipe Fitting with Mechanical Joint',
            'extracted_features': {
                'dimensions': '36-inch',
                'product_type': 'pipe fitting',
                'connection_type': 'mechanical joint'
            },
            'hts_context': {
                'hierarchical_description': 'Tube or pipe fittings',
                'product_category': 'fittings'
            }
        }
        
        score, factors = self.scorer.calculate_confidence(result)
        
        assert 0.0 <= score <= 1.0
        assert isinstance(factors, ConfidenceFactors)
        assert factors.feature_extraction_score > 0.0
        assert factors.hts_context_score > 0.0
        assert factors.pattern_match_score >= 0.0
        assert factors.completeness_score >= 0.0
        assert factors.consistency_score >= 0.0
    
    def test_feature_extraction_scoring(self):
        """Test feature extraction scoring"""
        # Test with good feature extraction
        result_good = {
            'original_description': 'test',
            'extracted_features': {
                'dimensions': '36-inch',
                'product_type': 'pipe fitting',
                'connection_type': 'mechanical joint',
                'material': 'ductile iron'
            }
        }
        score_good = self.scorer._score_feature_extraction(result_good)
        
        # Test with poor feature extraction
        result_poor = {
            'original_description': 'test',
            'extracted_features': {}
        }
        score_poor = self.scorer._score_feature_extraction(result_poor)
        
        assert score_good > score_poor
        assert 0.0 <= score_good <= 1.0
        assert 0.0 <= score_poor <= 1.0
    
    def test_hts_context_scoring(self):
        """Test HTS context scoring"""
        result = {
            'hts_context': {
                'hierarchical_description': 'Test description',
                'product_category': 'fittings',
                'material_requirements': 'iron'
            }
        }
        
        score = self.scorer._score_hts_context(result)
        assert score == 1.0  # All components present
        
        # Test with missing components
        result_partial = {
            'hts_context': {
                'product_category': 'fittings'
            }
        }
        score_partial = self.scorer._score_hts_context(result_partial)
        assert score_partial == 0.3  # Only one component
    
    def test_pattern_matching_scoring(self):
        """Test pattern matching scoring"""
        result = {
            'original_description': '36 INCH PIPE FITTING 123.45',
            'enhanced_description': '36-inch Pipe Fitting model 123.45'
        }
        
        score = self.scorer._score_pattern_matches(result)
        assert score > 0.0
        assert score <= 1.0
    
    def test_completeness_scoring(self):
        """Test completeness scoring"""
        # Test complete description
        result_complete = {
            'enhanced_description': 'This is a 36-inch ductile iron pipe fitting with mechanical joint connection'
        }
        score_complete = self.scorer._score_completeness(result_complete)
        
        # Test incomplete description
        result_incomplete = {
            'enhanced_description': 'pipe'
        }
        score_incomplete = self.scorer._score_completeness(result_incomplete)
        
        assert score_complete > score_incomplete
    
    def test_consistency_scoring(self):
        """Test consistency scoring"""
        # Test consistent description
        result_consistent = {
            'enhanced_description': 'This is a 36-inch pipe fitting with mechanical joint',
            'extracted_features': {
                'dimensions': '36-inch'
            }
        }
        score_consistent = self.scorer._score_consistency(result_consistent)
        
        # Test inconsistent description (inch vs mm)
        result_inconsistent = {
            'enhanced_description': 'This is a 900mm pipe fitting',
            'extracted_features': {
                'dimensions': '36-inch'
            }
        }
        score_inconsistent = self.scorer._score_consistency(result_inconsistent)
        
        assert score_consistent > score_inconsistent


class TestConfidenceCategorizer:
    """Test confidence categorization functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.categorizer = ConfidenceCategorizer()
    
    def test_confidence_categorization(self):
        """Test confidence categorization"""
        # Test high confidence
        level_high = self.categorizer.categorize(0.85)
        assert level_high == ConfidenceLevel.HIGH
        
        # Test medium confidence
        level_medium = self.categorizer.categorize(0.65)
        assert level_medium == ConfidenceLevel.MEDIUM
        
        # Test low confidence
        level_low = self.categorizer.categorize(0.45)
        assert level_low == ConfidenceLevel.LOW
    
    def test_custom_thresholds(self):
        """Test custom confidence thresholds"""
        custom_thresholds = ConfidenceThresholds(
            high_threshold=0.9,
            medium_threshold=0.7
        )
        categorizer = ConfidenceCategorizer(custom_thresholds)
        
        # Should be medium with custom thresholds
        level = categorizer.categorize(0.85)
        assert level == ConfidenceLevel.MEDIUM
    
    def test_categorization_stats(self):
        """Test categorization statistics"""
        results = [
            {'confidence_level': 'High', 'confidence_score': 0.9},
            {'confidence_level': 'Medium', 'confidence_score': 0.7},
            {'confidence_level': 'Low', 'confidence_score': 0.4}
        ]
        
        stats = self.categorizer.get_categorization_stats(results)
        
        assert stats['total_items'] == 3
        assert stats['distribution']['High'] == 1
        assert stats['distribution']['Medium'] == 1
        assert stats['distribution']['Low'] == 1
        assert abs(stats['avg_score'] - 0.67) < 0.1
        assert abs(stats['high_confidence_rate'] - 0.33) < 0.1


class TestQualityValidator:
    """Test quality validation functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = QualityValidator()
    
    def test_validation_basic(self):
        """Test basic validation functionality"""
        results = [
            {'confidence_score': 0.9},
            {'confidence_score': 0.8},
            {'confidence_score': 0.3},
            {'confidence_score': 0.2}
        ]
        actual_quality = [True, True, False, False]
        
        validation_result = self.validator.validate_confidence_calibration(results, actual_quality)
        
        assert 'calibration_error' in validation_result
        assert 'confidence_quality_correlation' in validation_result
        assert 'is_well_calibrated' in validation_result
        assert isinstance(validation_result['calibration_error'], float)
    
    def test_validation_length_mismatch(self):
        """Test validation with mismatched lengths"""
        results = [{'confidence_score': 0.9}]
        actual_quality = [True, False]
        
        with pytest.raises(ValueError):
            self.validator.validate_confidence_calibration(results, actual_quality)
    
    def test_correlation_calculation(self):
        """Test correlation calculation"""
        results = [
            {'confidence_score': 0.9},
            {'confidence_score': 0.1}
        ]
        actual_quality = [True, False]
        
        correlation = self.validator._calculate_correlation(results, actual_quality)
        assert isinstance(correlation, float)


class TestConfidenceCalibrator:
    """Test confidence calibration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.calibrator = ConfidenceCalibrator()
    
    def test_calibration_basic(self):
        """Test basic calibration functionality"""
        confidence_scores = [0.9, 0.8, 0.3, 0.2]
        actual_quality = [True, True, False, False]
        
        calibrated_scores = self.calibrator.calibrate_scores(confidence_scores, actual_quality)
        
        assert len(calibrated_scores) == len(confidence_scores)
        assert self.calibrator.is_calibrated
        assert all(0.0 <= score <= 1.0 for score in calibrated_scores)
    
    def test_apply_calibration(self):
        """Test applying calibration to new scores"""
        # First calibrate
        confidence_scores = [0.9, 0.8, 0.3, 0.2]
        actual_quality = [True, True, False, False]
        self.calibrator.calibrate_scores(confidence_scores, actual_quality)
        
        # Then apply to new scores
        new_scores = [0.7, 0.5]
        calibrated_new = self.calibrator.apply_calibration(new_scores)
        
        assert len(calibrated_new) == len(new_scores)
        assert all(0.0 <= score <= 1.0 for score in calibrated_new)
    
    def test_calibration_quality_metrics(self):
        """Test calibration quality metrics"""
        quality = self.calibrator.get_calibration_quality()
        assert quality['is_calibrated'] == False
        
        # Calibrate and test again
        confidence_scores = [0.9, 0.8, 0.3, 0.2]
        actual_quality = [True, True, False, False]
        self.calibrator.calibrate_scores(confidence_scores, actual_quality)
        
        quality = self.calibrator.get_calibration_quality()
        assert quality['is_calibrated'] == True


class TestConfidenceScoringSystem:
    """Test integrated confidence scoring system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.system = ConfidenceScoringSystem()
    
    def test_score_and_categorize(self):
        """Test scoring and categorization integration"""
        result = {
            'original_description': '36 C153 MJ 22 TN431 ZINC',
            'enhanced_description': '36-inch Ductile Iron Pipe Fitting with Mechanical Joint',
            'extracted_features': {
                'dimensions': '36-inch',
                'product_type': 'pipe fitting',
                'connection_type': 'mechanical joint'
            },
            'hts_context': {
                'hierarchical_description': 'Tube or pipe fittings',
                'product_category': 'fittings'
            }
        }
        
        enhanced_result = self.system.score_and_categorize(result)
        
        assert 'confidence_score' in enhanced_result
        assert 'confidence_level' in enhanced_result
        assert 'confidence_factors' in enhanced_result
        assert enhanced_result['confidence_level'] in ['High', 'Medium', 'Low']
        assert 0.0 <= enhanced_result['confidence_score'] <= 1.0
    
    def test_process_batch(self):
        """Test batch processing"""
        results = [
            {
                'original_description': 'test 1',
                'enhanced_description': 'enhanced test 1',
                'extracted_features': {'product_type': 'fitting'},
                'hts_context': {}
            },
            {
                'original_description': 'test 2',
                'enhanced_description': 'enhanced test 2',
                'extracted_features': {'dimensions': '36-inch'},
                'hts_context': {'product_category': 'pipe'}
            }
        ]
        
        batch_result = self.system.process_batch(results)
        
        assert 'results' in batch_result
        assert 'statistics' in batch_result
        assert len(batch_result['results']) == 2
        assert 'distribution' in batch_result['statistics']
    
    def test_system_calibration(self):
        """Test system calibration"""
        historical_results = [
            {'confidence_score': 0.9},
            {'confidence_score': 0.8},
            {'confidence_score': 0.3}
        ]
        actual_quality = [True, True, False]
        
        self.system.calibrate_system(historical_results, actual_quality)
        assert self.system.calibrator.is_calibrated
    
    def test_validate_calibration(self):
        """Test calibration validation"""
        results = [
            {'confidence_score': 0.9},
            {'confidence_score': 0.3}
        ]
        actual_quality = [True, False]
        
        validation = self.system.validate_calibration(results, actual_quality)
        assert isinstance(validation, dict)
        assert 'calibration_error' in validation


if __name__ == "__main__":
    pytest.main([__file__])
