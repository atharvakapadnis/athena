#!/usr/bin/env python3
"""
Test sklearn integration for enhanced confidence scoring features
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.confidence_scoring import ConfidenceScoringSystem, QualityValidator, ConfidenceCalibrator

def test_sklearn_features():
    """Test sklearn-enhanced features"""
    print("Testing sklearn-enhanced confidence scoring features...")
    
    # Test calibrator with sklearn
    print("\n📊 Testing Enhanced Calibration:")
    calibrator = ConfidenceCalibrator()
    
    confidence_scores = [0.9, 0.8, 0.7, 0.3, 0.2, 0.1]
    actual_quality = [True, True, True, False, False, False]
    
    calibrated_scores = calibrator.calibrate_scores(confidence_scores, actual_quality)
    quality_metrics = calibrator.get_calibration_quality()
    
    print(f"✓ Original scores: {confidence_scores}")
    print(f"✓ Calibrated scores: {[f'{s:.3f}' for s in calibrated_scores]}")
    print(f"✓ Calibration model: {quality_metrics}")
    
    # Test validator with sklearn
    print("\n📈 Testing Enhanced Validation:")
    validator = QualityValidator()
    
    test_results = [
        {'confidence_score': 0.9},
        {'confidence_score': 0.8},
        {'confidence_score': 0.7}, 
        {'confidence_score': 0.3},
        {'confidence_score': 0.2}
    ]
    test_quality = [True, True, True, False, False]
    
    validation_result = validator.validate_confidence_calibration(test_results, test_quality)
    
    print(f"✓ Validation completed")
    print(f"✓ Calibration error: {validation_result['calibration_error']:.3f}")
    print(f"✓ Well calibrated: {validation_result['is_well_calibrated']}")
    print(f"✓ Correlation: {validation_result['confidence_quality_correlation']:.3f}")
    
    if 'classification_report' in validation_result:
        print("✓ Classification report available (sklearn detected)")
        accuracy = validation_result['classification_report']['accuracy']
        print(f"✓ Accuracy: {accuracy:.3f}")
    else:
        print("ℹ Classification report not available (sklearn not detected)")
    
    # Test full system with calibration
    print("\n🔄 Testing Full System with Calibration:")
    system = ConfidenceScoringSystem()
    
    # Calibrate system
    historical_results = [
        {'confidence_score': 0.9},
        {'confidence_score': 0.8},
        {'confidence_score': 0.3},
        {'confidence_score': 0.2}
    ]
    historical_quality = [True, True, False, False]
    
    system.calibrate_system(historical_results, historical_quality)
    print("✓ System calibrated with historical data")
    
    # Test on new data
    new_result = {
        'original_description': '48 INCH STEEL PIPE',
        'enhanced_description': '48-inch Steel Pipe with Standard Threading',
        'extracted_features': {
            'dimensions': '48-inch',
            'product_type': 'pipe',
            'material': 'steel'
        },
        'hts_context': {
            'product_category': 'pipes'
        }
    }
    
    scored_result = system.score_and_categorize(new_result)
    print(f"✓ New result scored with calibration:")
    print(f"  - Raw confidence: {scored_result['confidence_score']:.3f}")
    print(f"  - Confidence level: {scored_result['confidence_level']}")
    
    print("\n🎉 sklearn integration test completed successfully!")

if __name__ == "__main__":
    test_sklearn_features()
