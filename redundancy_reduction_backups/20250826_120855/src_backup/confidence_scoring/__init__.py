# src/confidence_scoring/__init__.py
"""
Confidence Scoring System for Smart Description Iterative Improvement

This module provides confidence assessment and categorization for generated descriptions.
"""

from .scorer import ConfidenceScorer, ConfidenceFactors
from .categorizer import ConfidenceCategorizer, ConfidenceLevel, ConfidenceThresholds
from .validator import QualityValidator
from .calibrator import ConfidenceCalibrator

__all__ = [
    'ConfidenceScorer',
    'ConfidenceFactors', 
    'ConfidenceCategorizer',
    'ConfidenceLevel',
    'ConfidenceThresholds',
    'QualityValidator',
    'ConfidenceCalibrator',
    'ConfidenceScoringSystem'
]

class ConfidenceScoringSystem:
    """Main interface for confidence scoring functionality"""
    
    def __init__(self, thresholds: ConfidenceThresholds = None):
        """Initialize confidence scoring system"""
        self.scorer = ConfidenceScorer()
        self.categorizer = ConfidenceCategorizer(thresholds)
        self.validator = QualityValidator()
        self.calibrator = ConfidenceCalibrator()
    
    def score_and_categorize(self, result: dict) -> dict:
        """Score a result and categorize confidence level"""
        # Calculate confidence score and factors
        confidence_score, factors = self.scorer.calculate_confidence(result)
        
        # Apply calibration if available
        if self.calibrator.is_calibrated:
            calibrated_scores = self.calibrator.apply_calibration([confidence_score])
            confidence_score = calibrated_scores[0]
        
        # Categorize confidence level
        confidence_level = self.categorizer.categorize(confidence_score)
        
        # Return enhanced result
        enhanced_result = result.copy()
        enhanced_result.update({
            'confidence_score': confidence_score,
            'confidence_level': confidence_level.value,
            'confidence_factors': {
                'feature_extraction_score': factors.feature_extraction_score,
                'hts_context_score': factors.hts_context_score,
                'pattern_match_score': factors.pattern_match_score,
                'completeness_score': factors.completeness_score,
                'consistency_score': factors.consistency_score
            }
        })
        
        return enhanced_result
    
    def process_batch(self, results: list) -> dict:
        """Process a batch of results and return statistics"""
        scored_results = []
        
        for result in results:
            scored_result = self.score_and_categorize(result)
            scored_results.append(scored_result)
        
        # Get categorization statistics
        stats = self.categorizer.get_categorization_stats(scored_results)
        
        return {
            'results': scored_results,
            'statistics': stats
        }
    
    def calibrate_system(self, historical_results: list, actual_quality: list):
        """Calibrate the confidence scoring system using historical data"""
        confidence_scores = [r.get('confidence_score', 0.0) for r in historical_results]
        self.calibrator.calibrate_scores(confidence_scores, actual_quality)
    
    def validate_calibration(self, results: list, actual_quality: list) -> dict:
        """Validate the calibration quality"""
        return self.validator.validate_confidence_calibration(results, actual_quality)
