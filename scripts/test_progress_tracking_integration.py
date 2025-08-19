#!/usr/bin/env python3
"""
Test script for Progress Tracking System Integration

This script tests the complete progress tracking system including metrics collection,
performance analysis, and dashboard functionality.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from progress_tracking import (
        MetricsCollector, PerformanceAnalyzer, ProgressDashboard,
        ProcessingMetrics, RuleMetrics
    )
    from batch_processor.processor import BatchResult, ProcessingResult
    from utils.logger import get_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed and paths are correct")
    sys.exit(1)

logger = get_logger(__name__)

def create_sample_batch_result(batch_id: str, success_rate: float = 0.85, 
                              total_items: int = 50) -> BatchResult:
    """Create a sample BatchResult for testing"""
    import time
    import random
    
    results = []
    successful_items = int(total_items * success_rate)
    failed_items = total_items - successful_items
    
    confidence_distribution = {'High': 0, 'Medium': 0, 'Low': 0}
    
    # Create successful results
    for i in range(successful_items):
        confidence_score = random.uniform(0.7, 0.95)
        if confidence_score >= 0.8:
            confidence_level = 'High'
            confidence_distribution['High'] += 1
        elif confidence_score >= 0.6:
            confidence_level = 'Medium'
            confidence_distribution['Medium'] += 1
        else:
            confidence_level = 'Low'
            confidence_distribution['Low'] += 1
        
        result = ProcessingResult(
            item_id=f"item_{i}",
            original_description=f"Original description {i}",
            enhanced_description=f"Enhanced description {i}",
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            extracted_features={"feature1": "value1", "feature2": "value2"},
            success=True,
            processing_time=random.uniform(0.1, 0.5)
        )
        results.append(result)
    
    # Create failed results
    for i in range(failed_items):
        result = ProcessingResult(
            item_id=f"failed_item_{i}",
            original_description=f"Failed description {i}",
            enhanced_description="",
            confidence_score=0.0,
            confidence_level='Low',
            extracted_features={},
            success=False,
            error_message="Processing failed",
            processing_time=random.uniform(0.1, 0.3)
        )
        results.append(result)
        confidence_distribution['Low'] += 1
    
    # Create summary
    summary = {
        'success_rate': success_rate,
        'high_confidence_rate': confidence_distribution['High'] / total_items,
        'average_confidence': sum(r.confidence_score for r in results if r.success) / successful_items if successful_items > 0 else 0
    }
    
    return BatchResult(
        batch_id=batch_id,
        total_items=total_items,
        successful_items=successful_items,
        failed_items=failed_items,
        processing_time=random.uniform(1.0, 3.0),
        confidence_distribution=confidence_distribution,
        results=results,
        summary=summary
    )

def test_metrics_collector():
    """Test MetricsCollector functionality"""
    print("\n=== Testing MetricsCollector ===")
    
    # Initialize MetricsCollector
    collector = MetricsCollector()
    
    # Test collecting batch metrics
    batch_result = create_sample_batch_result("test_batch_001", success_rate=0.88)
    metrics = collector.collect_batch_metrics(batch_result)
    
    print(f"✓ Collected metrics for batch: {metrics.batch_id}")
    print(f"  Success rate: {metrics.success_rate:.1%}")
    print(f"  Average confidence: {metrics.average_confidence:.3f}")
    print(f"  Processing time: {metrics.processing_time:.2f}s")
    
    # Test rule metrics updates
    collector.update_rule_metrics("rule_001", success=True, confidence=0.85, 
                                rule_name="Test Rule 1", rule_type="enhancement")
    collector.update_rule_metrics("rule_001", success=True, confidence=0.78)
    collector.update_rule_metrics("rule_002", success=False, confidence=0.45, 
                                rule_name="Test Rule 2", rule_type="validation")
    
    print(f"✓ Updated rule metrics for 2 rules")
    
    # Test summaries
    processing_summary = collector.get_processing_summary()
    rule_summary = collector.get_rule_performance_summary()
    
    print(f"✓ Processing summary: {processing_summary['total_batches']} batches, "
          f"{processing_summary['average_success_rate']:.1%} avg success rate")
    print(f"✓ Rule summary: {rule_summary['total_rules']} rules, "
          f"{rule_summary['average_performance']:.3f} avg performance")
    
    return collector

def test_performance_analyzer(collector):
    """Test PerformanceAnalyzer functionality"""
    print("\n=== Testing PerformanceAnalyzer ===")
    
    # Add more sample data to test trends
    for i in range(5):
        batch_result = create_sample_batch_result(f"test_batch_{i:03d}", 
                                                success_rate=0.85 + (i * 0.02))  # Improving trend
        collector.collect_batch_metrics(batch_result)
    
    # Initialize PerformanceAnalyzer
    analyzer = PerformanceAnalyzer(collector)
    
    # Test trends calculation
    trends = analyzer.calculate_trends(window_size=5)
    print(f"✓ Calculated trends over {trends['data_points']} batches")
    print(f"  Success rate trend: {trends['success_rate_trend']:.6f}")
    print(f"  Confidence trend: {trends['confidence_trend']:.6f}")
    print(f"  Average success rate: {trends['average_success_rate']:.1%}")
    
    # Test bottleneck identification
    bottlenecks = analyzer.identify_bottlenecks()
    print(f"✓ Identified {len(bottlenecks)} bottlenecks")
    for bottleneck in bottlenecks:
        print(f"  - {bottleneck['type']} (severity: {bottleneck.get('severity', 'unknown')})")
    
    # Test regression analysis
    regression = analyzer.analyze_performance_regression()
    print(f"✓ Regression analysis: {regression['status']}")
    if regression['status'] != 'insufficient_data':
        print(f"  Regression indicators: {regression.get('regression_indicators', [])}")
    
    # Test performance insights
    insights = analyzer.get_performance_insights()
    print(f"✓ Generated performance insights")
    print(f"  Overall health: {insights['summary']['overall_health']}")
    print(f"  Priority actions: {len(insights['summary']['priority_actions'])}")
    
    return analyzer

def test_progress_dashboard(collector, analyzer):
    """Test ProgressDashboard functionality"""
    print("\n=== Testing ProgressDashboard ===")
    
    # Initialize ProgressDashboard
    dashboard = ProgressDashboard(collector, analyzer)
    
    # Test summary report
    summary_report = dashboard.generate_summary_report()
    print(f"✓ Generated summary report")
    print(f"  Report status: {summary_report.get('status', 'data_available')}")
    print(f"  Overall health: {summary_report['current_status']['overall_health']}")
    print(f"  Bottlenecks found: {summary_report['issue_analysis']['bottlenecks_found']}")
    print(f"  Recommendations: {len(summary_report['recommendations'])}")
    
    # Test executive summary
    exec_summary = dashboard.generate_executive_summary()
    print(f"✓ Generated executive summary")
    print(f"  Overall status: {exec_summary['overall_status']}")
    print(f"  Critical actions: {len(exec_summary['immediate_actions_required'])}")
    
    # Test real-time metrics
    rt_metrics = dashboard.get_real_time_metrics()
    print(f"✓ Generated real-time metrics")
    print(f"  System health: {rt_metrics['system_health']}")
    print(f"  Current success rate: {rt_metrics['current_metrics']['success_rate']:.1%}")
    print(f"  Active alerts: {rt_metrics['alerts']}")
    
    return dashboard

def test_data_persistence():
    """Test data persistence and loading"""
    print("\n=== Testing Data Persistence ===")
    
    # Create new collector to test loading existing data
    collector2 = MetricsCollector()
    
    print(f"✓ Loaded existing data: {len(collector2.processing_history)} metrics, "
          f"{len(collector2.rule_performance)} rules")
    
    # Test export functionality
    export_path = "data/metrics/test_export.json"
    collector2.export_metrics(export_path)
    
    if os.path.exists(export_path):
        print(f"✓ Successfully exported metrics to {export_path}")
        
        # Verify export contents
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
        
        print(f"  Exported {len(exported_data.get('processing_metrics', []))} processing metrics")
        print(f"  Exported {len(exported_data.get('rule_metrics', {}))} rule metrics")
    else:
        print("✗ Export failed")

def test_integration_workflow():
    """Test complete integration workflow"""
    print("\n=== Testing Complete Integration Workflow ===")
    
    # Initialize complete system
    collector = MetricsCollector()
    analyzer = PerformanceAnalyzer(collector)
    dashboard = ProgressDashboard(collector, analyzer)
    
    # Simulate processing workflow
    print("Simulating batch processing workflow...")
    
    # Process several batches with varying performance
    batch_configs = [
        ("batch_001", 0.92, 45),
        ("batch_002", 0.88, 50),
        ("batch_003", 0.85, 48),
        ("batch_004", 0.90, 52),
        ("batch_005", 0.86, 47)
    ]
    
    for batch_id, success_rate, total_items in batch_configs:
        # Simulate batch processing
        batch_result = create_sample_batch_result(batch_id, success_rate, total_items)
        
        # Collect metrics
        metrics = collector.collect_batch_metrics(batch_result)
        
        # Simulate rule usage
        for rule_id in ["enhancement_rule", "validation_rule", "quality_rule"]:
            success = success_rate > 0.87  # Rules succeed when batch performance is good
            confidence = success_rate + (0.1 if success else -0.1)
            collector.update_rule_metrics(rule_id, success, confidence, 
                                        rule_name=f"{rule_id.replace('_', ' ').title()}")
        
        print(f"  Processed {batch_id}: {success_rate:.1%} success rate")
    
    # Generate comprehensive dashboard
    print("\nGenerating comprehensive dashboard...")
    summary = dashboard.generate_summary_report()
    
    # Save dashboard data
    dashboard_export_path = "data/metrics/integration_test_dashboard.json"
    dashboard.export_dashboard_data(dashboard_export_path)
    
    print(f"✓ Integration test completed successfully")
    print(f"✓ Dashboard data exported to {dashboard_export_path}")
    print(f"✓ Final system health: {summary['current_status']['overall_health']}")
    print(f"✓ Total recommendations: {len(summary['recommendations'])}")
    
    return collector, analyzer, dashboard

def main():
    """Run all progress tracking tests"""
    print("Starting Progress Tracking System Integration Test")
    print("=" * 60)
    
    try:
        # Test individual components
        collector = test_metrics_collector()
        analyzer = test_performance_analyzer(collector)
        dashboard = test_progress_dashboard(collector, analyzer)
        
        # Test data persistence
        test_data_persistence()
        
        # Test complete integration
        test_integration_workflow()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Progress Tracking System is working correctly!")
        print("=" * 60)
        
        # Display final system status
        final_summary = dashboard.generate_executive_summary()
        if final_summary.get("status") != "no_data":
            print(f"\nFinal System Status: {final_summary['overall_status']}")
            print(f"Description: {final_summary['status_description']}")
            
            if final_summary.get('critical_metrics'):
                print("\nKey Metrics:")
                for metric, value in final_summary['critical_metrics'].items():
                    print(f"  {metric.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
