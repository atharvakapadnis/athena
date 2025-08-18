#!/usr/bin/env python3
"""
Quick functional test for confidence scoring system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.confidence_scoring import ConfidenceScoringSystem

def test_basic_functionality():
    """Test basic confidence scoring functionality"""
    print("Testing Confidence Scoring System...")
    
    # Initialize system
    system = ConfidenceScoringSystem()
    print("✓ System initialized")
    
    # Test sample result
    sample_result = {
        'original_description': '36 C153 MJ 22 TN431 ZINC',
        'enhanced_description': '36-inch Ductile Iron Pipe Fitting with Mechanical Joint',
        'extracted_features': {
            'dimensions': '36-inch',
            'product_type': 'pipe fitting',
            'connection_type': 'mechanical joint',
            'material': 'ductile iron'
        },
        'hts_context': {
            'hierarchical_description': 'Tube or pipe fittings',
            'product_category': 'fittings',
            'material_requirements': 'iron'
        }
    }
    
    # Score and categorize
    enhanced_result = system.score_and_categorize(sample_result)
    print(f"✓ Confidence Score: {enhanced_result['confidence_score']:.3f}")
    print(f"✓ Confidence Level: {enhanced_result['confidence_level']}")
    
    # Test factors breakdown
    factors = enhanced_result['confidence_factors']
    print("✓ Confidence Factors:")
    for factor, score in factors.items():
        print(f"  - {factor}: {score:.3f}")
    
    # Test batch processing
    batch_results = [sample_result, sample_result.copy()]
    batch_output = system.process_batch(batch_results)
    
    print(f"✓ Batch processed: {len(batch_output['results'])} items")
    print(f"✓ Statistics: {batch_output['statistics']}")
    
    # Test calibration
    print("\nTesting calibration...")
    historical_results = [
        {'confidence_score': 0.9},
        {'confidence_score': 0.8}, 
        {'confidence_score': 0.3},
        {'confidence_score': 0.2}
    ]
    actual_quality = [True, True, False, False]
    
    system.calibrate_system(historical_results, actual_quality)
    print("✓ System calibrated")
    
    # Test validation
    validation = system.validate_calibration(historical_results, actual_quality)
    print(f"✓ Calibration validation: {validation}")
    
    print("\n🎉 All basic functionality tests passed!")

if __name__ == "__main__":
    test_basic_functionality()
