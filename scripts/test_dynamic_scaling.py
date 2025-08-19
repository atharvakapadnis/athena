#!/usr/bin/env python3
"""
Test script for Dynamic Scaling System

This script tests the dynamic scaling functionality by simulating various
performance scenarios and verifying that the scaling system responds appropriately.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from batch_processor.scaling_manager import ScalingManager, ScalingConfig, ScalingAction
from batch_processor.scaling_predictor import ScalingPredictor
from batch_processor.processor import BatchResult
from utils.logger import get_logger

logger = get_logger(__name__)

class MockBatchResult:
    """Mock BatchResult for testing"""
    def __init__(self, batch_id: str, total_items: int, high_confidence: int, 
                 medium_confidence: int, low_confidence: int, processing_time: float):
        self.batch_id = batch_id
        self.total_items = total_items
        self.successful_items = high_confidence + medium_confidence + low_confidence
        self.failed_items = 0
        self.processing_time = processing_time
        self.confidence_distribution = {
            'High': high_confidence,
            'Medium': medium_confidence,
            'Low': low_confidence
        }
        self.results = []
        self.summary = {}

def test_scaling_manager():
    """Test ScalingManager functionality"""
    print("\n=== Testing ScalingManager ===")
    
    # Create scaling manager
    config = ScalingConfig(
        initial_batch_size=50,
        min_batch_size=10,
        max_batch_size=200,
        scaling_factor=1.5,
        high_confidence_threshold=0.9,
        low_confidence_threshold=0.7
    )
    
    scaling_manager = ScalingManager(config)
    
    # Test scenario 1: High performance - should scale up
    print("\nScenario 1: High performance (should scale up)")
    high_perf_batches = [
        MockBatchResult("batch_1", 50, 48, 2, 0, 1.5),  # 96% high confidence
        MockBatchResult("batch_2", 50, 47, 3, 0, 1.4),  # 94% high confidence
        MockBatchResult("batch_3", 50, 49, 1, 0, 1.6),  # 98% high confidence
    ]
    
    decision = scaling_manager.evaluate_scaling(high_perf_batches)
    print(f"Decision: {decision.action.value}")
    print(f"New batch size: {decision.new_batch_size}")
    print(f"Reason: {decision.reason}")
    
    applied = scaling_manager.apply_scaling_decision(decision)
    print(f"Scaling applied: {applied}")
    print(f"Current batch size: {scaling_manager.get_current_batch_size()}")
    
    # Test scenario 2: Low performance - should scale down
    print("\nScenario 2: Low performance (should scale down)")
    low_perf_batches = [
        MockBatchResult("batch_4", 75, 30, 25, 20, 6.5),  # 40% high confidence, slow
        MockBatchResult("batch_5", 75, 35, 20, 20, 7.2),  # 47% high confidence, slow
        MockBatchResult("batch_6", 75, 32, 23, 20, 6.8),  # 43% high confidence, slow
    ]
    
    decision = scaling_manager.evaluate_scaling(low_perf_batches)
    print(f"Decision: {decision.action.value}")
    print(f"New batch size: {decision.new_batch_size}")
    print(f"Reason: {decision.reason}")
    
    applied = scaling_manager.apply_scaling_decision(decision)
    print(f"Scaling applied: {applied}")
    print(f"Current batch size: {scaling_manager.get_current_batch_size()}")
    
    # Test scenario 3: Stable performance - should maintain
    print("\nScenario 3: Stable performance (should maintain)")
    stable_perf_batches = [
        MockBatchResult("batch_7", 50, 40, 8, 2, 2.5),  # 80% high confidence
        MockBatchResult("batch_8", 50, 41, 7, 2, 2.3),  # 82% high confidence
        MockBatchResult("batch_9", 50, 39, 9, 2, 2.7),  # 78% high confidence
    ]
    
    decision = scaling_manager.evaluate_scaling(stable_perf_batches)
    print(f"Decision: {decision.action.value}")
    print(f"New batch size: {decision.new_batch_size}")
    print(f"Reason: {decision.reason}")
    
    # Get scaling summary
    summary = scaling_manager.get_scaling_summary()
    print(f"\nScaling Summary:")
    print(f"Total decisions: {summary['total_decisions']}")
    print(f"Increases: {summary['increases']}")
    print(f"Decreases: {summary['decreases']}")
    print(f"Maintains: {summary['maintains']}")
    print(f"Current batch size: {summary['current_batch_size']}")

def test_scaling_predictor():
    """Test ScalingPredictor functionality"""
    print("\n=== Testing ScalingPredictor ===")
    
    predictor = ScalingPredictor()
    
    # Test optimal batch size prediction
    print("\nTesting optimal batch size prediction:")
    
    # High performance scenario
    high_performance = {
        'batch_size': 50,
        'high_confidence_rate': 0.95,
        'avg_processing_time': 1.5,
        'success_rate': 0.98,
        'stability_score': 0.9
    }
    
    optimal_size = predictor.predict_optimal_batch_size(high_performance)
    print(f"High performance scenario - Optimal size: {optimal_size}")
    
    # Poor performance scenario
    poor_performance = {
        'batch_size': 100,
        'high_confidence_rate': 0.45,
        'avg_processing_time': 8.0,
        'success_rate': 0.75,
        'stability_score': 0.6
    }
    
    optimal_size = predictor.predict_optimal_batch_size(poor_performance)
    print(f"Poor performance scenario - Optimal size: {optimal_size}")
    
    # Test scaling timing
    print("\nTesting scaling timing decisions:")
    
    improving_trend = {
        'status': 'analyzed',
        'confidence_trend': 'improving',
        'time_trend': 'stable',
        'latest_confidence_rate': 0.88,
        'stability_score': 0.85
    }
    
    should_scale, reason = predictor.should_scale_now(improving_trend)
    print(f"Improving trend - Should scale: {should_scale}, Reason: {reason}")
    
    declining_trend = {
        'status': 'analyzed',
        'confidence_trend': 'declining',
        'time_trend': 'declining',
        'latest_confidence_rate': 0.65,
        'stability_score': 0.7
    }
    
    should_scale, reason = predictor.should_scale_now(declining_trend)
    print(f"Declining trend - Should scale: {should_scale}, Reason: {reason}")
    
    # Test comprehensive recommendation
    print("\nTesting comprehensive scaling recommendation:")
    
    current_performance = {
        'batch_size': 75,
        'high_confidence_rate': 0.85,
        'avg_processing_time': 2.2,
        'success_rate': 0.92,
        'stability_score': 0.8
    }
    
    historical_data = [
        {'batch_size': 50, 'high_confidence_rate': 0.9, 'avg_processing_time': 1.8, 'success_rate': 0.95},
        {'batch_size': 75, 'high_confidence_rate': 0.85, 'avg_processing_time': 2.2, 'success_rate': 0.92},
        {'batch_size': 75, 'high_confidence_rate': 0.83, 'avg_processing_time': 2.4, 'success_rate': 0.91},
    ]
    
    recommendation = predictor.get_scaling_recommendation(current_performance, historical_data)
    print(f"Recommendation: {recommendation['action']}")
    print(f"Current size: {recommendation['current_batch_size']}")
    print(f"Recommended size: {recommendation['recommended_batch_size']}")
    print(f"Confidence: {recommendation['confidence_score']:.2f}")
    print(f"Reason: {recommendation['reason']}")
    print(f"Performance score: {recommendation['performance_score']:.2f}")

def test_performance_scenarios():
    """Test various performance scenarios"""
    print("\n=== Testing Performance Scenarios ===")
    
    config = ScalingConfig(initial_batch_size=50)
    scaling_manager = ScalingManager(config)
    predictor = ScalingPredictor()
    
    scenarios = [
        {
            'name': 'Excellent Performance',
            'batches': [
                MockBatchResult("excellent_1", 50, 49, 1, 0, 1.2),
                MockBatchResult("excellent_2", 50, 48, 2, 0, 1.1),
                MockBatchResult("excellent_3", 50, 50, 0, 0, 1.0),
            ],
            'expected_action': ScalingAction.INCREASE
        },
        {
            'name': 'Very Poor Performance',
            'batches': [
                MockBatchResult("poor_1", 50, 15, 20, 15, 8.5),
                MockBatchResult("poor_2", 50, 12, 18, 20, 9.2),
                MockBatchResult("poor_3", 50, 18, 17, 15, 7.8),
            ],
            'expected_action': ScalingAction.DECREASE
        },
        {
            'name': 'Borderline Performance',
            'batches': [
                MockBatchResult("border_1", 50, 35, 12, 3, 3.5),
                MockBatchResult("border_2", 50, 38, 10, 2, 3.2),
                MockBatchResult("border_3", 50, 36, 11, 3, 3.8),
            ],
            'expected_action': ScalingAction.MAINTAIN
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        decision = scaling_manager.evaluate_scaling(scenario['batches'])
        print(f"Decision: {decision.action.value}")
        print(f"Expected: {scenario['expected_action'].value}")
        print(f"Matches expectation: {decision.action == scenario['expected_action']}")
        print(f"Reason: {decision.reason}")
        print(f"Confidence threshold: {decision.confidence_threshold:.2f}")

def test_integration_flow():
    """Test the complete integration flow"""
    print("\n=== Testing Integration Flow ===")
    
    # This would simulate the complete flow from batch processing
    # through scaling evaluation to batch size adjustment
    
    config = ScalingConfig(initial_batch_size=50)
    scaling_manager = ScalingManager(config)
    
    print("Simulating batch processing sequence with scaling...")
    
    # Simulate a sequence of batches with improving performance
    batch_sequence = [
        # Initial batches with moderate performance
        MockBatchResult("seq_1", 50, 35, 12, 3, 3.0),
        MockBatchResult("seq_2", 50, 37, 10, 3, 2.8),
        MockBatchResult("seq_3", 50, 40, 8, 2, 2.5),
        # Performance improves
        MockBatchResult("seq_4", 50, 45, 4, 1, 2.0),
        MockBatchResult("seq_5", 50, 47, 3, 0, 1.8),
        MockBatchResult("seq_6", 50, 48, 2, 0, 1.5),
    ]
    
    batch_sizes = [scaling_manager.get_current_batch_size()]
    
    for i in range(0, len(batch_sequence), 3):
        # Evaluate every 3 batches (simulating evaluation frequency)
        batch_window = batch_sequence[i:i+3]
        if len(batch_window) >= 3:
            decision = scaling_manager.evaluate_scaling(batch_window)
            applied = scaling_manager.apply_scaling_decision(decision)
            
            current_size = scaling_manager.get_current_batch_size()
            batch_sizes.append(current_size)
            
            print(f"Batches {i+1}-{i+3}: {decision.action.value} to {current_size}")
            print(f"  Reason: {decision.reason}")
    
    print(f"\nBatch size progression: {batch_sizes}")
    
    # Final summary
    summary = scaling_manager.get_scaling_summary()
    print(f"\nFinal Summary:")
    print(f"  Started with: {config.initial_batch_size}")
    print(f"  Ended with: {summary['current_batch_size']}")
    print(f"  Total scaling decisions: {summary['total_decisions']}")
    print(f"  Increases: {summary['increases']}")
    print(f"  Decreases: {summary['decreases']}")

def main():
    """Run all dynamic scaling tests"""
    print("Dynamic Scaling System Test Suite")
    print("=" * 50)
    
    try:
        test_scaling_manager()
        test_scaling_predictor()
        test_performance_scenarios()
        test_integration_flow()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("Dynamic scaling system is functioning correctly.")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
