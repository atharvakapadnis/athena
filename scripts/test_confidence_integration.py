#!/usr/bin/env python3
"""
Integration test for confidence scoring with batch processor
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.confidence_scoring import ConfidenceScoringSystem
from src.batch_processor.processor import BatchProcessor, ProcessingResult

def test_integration():
    """Test integration between confidence scoring and batch processor"""
    print("Testing Confidence Scoring Integration...")
    
    # Initialize systems
    confidence_system = ConfidenceScoringSystem()
    print("✓ Confidence scoring system initialized")
    
    # Create sample processing results (simulating batch processor output)
    sample_processing_results = [
        ProcessingResult(
            item_id="item_1",
            original_description="36 C153 MJ 22 TN431 ZINC",
            enhanced_description="36-inch Ductile Iron Pipe Fitting with Mechanical Joint",
            confidence_score=0.0,  # Will be calculated
            confidence_level="",   # Will be calculated
            extracted_features={
                'dimensions': '36-inch',
                'product_type': 'pipe fitting',
                'connection_type': 'mechanical joint'
            },
            processing_time=0.1,
            success=True
        ),
        ProcessingResult(
            item_id="item_2", 
            original_description="24 FLANGE STEEL",
            enhanced_description="24-inch Steel Flange Fitting",
            confidence_score=0.0,  # Will be calculated
            confidence_level="",   # Will be calculated
            extracted_features={
                'dimensions': '24-inch',
                'product_type': 'flange',
                'material': 'steel'
            },
            processing_time=0.1,
            success=True
        ),
        ProcessingResult(
            item_id="item_3",
            original_description="UNKNOWN PART",
            enhanced_description="Unknown Component",
            confidence_score=0.0,  # Will be calculated
            confidence_level="",   # Will be calculated
            extracted_features={},
            processing_time=0.1,
            success=True
        )
    ]
    
    print(f"✓ Created {len(sample_processing_results)} sample results")
    
    # Convert to dict format for confidence scoring
    results_for_scoring = []
    for result in sample_processing_results:
        result_dict = {
            'original_description': result.original_description,
            'enhanced_description': result.enhanced_description,
            'extracted_features': result.extracted_features,
            'hts_context': {}  # Simulated empty HTS context
        }
        results_for_scoring.append(result_dict)
    
    # Process through confidence system
    batch_output = confidence_system.process_batch(results_for_scoring)
    scored_results = batch_output['results']
    
    print("✓ Confidence scoring completed")
    print(f"✓ Statistics: {batch_output['statistics']}")
    
    # Update original processing results with confidence scores
    for i, scored_result in enumerate(scored_results):
        sample_processing_results[i].confidence_score = scored_result['confidence_score']
        sample_processing_results[i].confidence_level = scored_result['confidence_level']
    
    # Display results
    print("\n📊 Integration Results:")
    for result in sample_processing_results:
        print(f"Item: {result.item_id}")
        print(f"  Original: {result.original_description}")
        print(f"  Enhanced: {result.enhanced_description}")
        print(f"  Confidence: {result.confidence_score:.3f} ({result.confidence_level})")
        print(f"  Features: {len(result.extracted_features)} extracted")
        print()
    
    # Test confidence distribution
    distribution = batch_output['statistics']['distribution']
    total = batch_output['statistics']['total_items']
    
    print("📈 Confidence Distribution:")
    for level, count in distribution.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  {level}: {count} items ({percentage:.1f}%)")
    
    print(f"\n✓ High confidence rate: {batch_output['statistics']['high_confidence_rate']:.1%}")
    print(f"✓ Average confidence score: {batch_output['statistics']['avg_score']:.3f}")
    
    print("\n🎉 Integration test completed successfully!")

if __name__ == "__main__":
    test_integration()
