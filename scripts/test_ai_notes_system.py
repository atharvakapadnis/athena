#!/usr/bin/env python3
"""
Test script for AI Notes System implementation
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from ai_analysis import (
    NotesManager, NotesPatternAnalyzer, NotesExporter, NotesIntegration
)
from utils.logger import setup_logging

def test_notes_manager():
    """Test basic NotesManager functionality"""
    print("\n=== Testing NotesManager ===")
    
    # Initialize manager
    manager = NotesManager()
    print(f"✓ NotesManager initialized with {len(manager.notes)} existing notes")
    
    # Add sample notes
    note_id1 = manager.add_ai_note(
        note_type="observation",
        content="Batch processing revealed high failure rate in product descriptions",
        context={"batch_id": "test_001", "failure_rate": 0.35},
        tags=["batch_analysis", "high_failure"],
        priority=4
    )
    print(f"✓ Added observation note: {note_id1}")
    
    note_id2 = manager.add_ai_note(
        note_type="suggestion",
        content="AI suggests adding rule for material abbreviations",
        context={"rule_type": "material", "confidence": 0.85},
        tags=["rule_suggestion", "material"],
        priority=3
    )
    print(f"✓ Added suggestion note: {note_id2}")
    
    # Add human feedback
    feedback_id = manager.add_human_feedback(
        content="Suggestion approved and implemented",
        related_note_id=note_id2,
        action_taken="accepted",
        user_id="test_user"
    )
    print(f"✓ Added human feedback: {feedback_id}")
    
    # Test search functionality
    search_results = manager.search_notes("batch", tags=["batch_analysis"])
    print(f"✓ Search found {len(search_results)} notes")
    
    # Test status update
    success = manager.update_note_status(note_id2, "resolved")
    print(f"✓ Status update: {success}")
    
    # Get summary
    summary = manager.get_summary()
    print(f"✓ Summary: {summary['total_notes']} notes, {summary['total_feedback']} feedback")
    
    return manager

def test_pattern_analyzer(manager):
    """Test NotesPatternAnalyzer functionality"""
    print("\n=== Testing NotesPatternAnalyzer ===")
    
    analyzer = NotesPatternAnalyzer(manager)
    
    # Analyze patterns
    patterns = analyzer.analyze_note_patterns()
    print(f"✓ Pattern analysis completed")
    print(f"  - Note types: {patterns.get('note_type_distribution', {})}")
    print(f"  - Priority distribution: {patterns.get('priority_distribution', {})}")
    
    # Identify insights
    insights = analyzer.identify_insights()
    print(f"✓ Identified {len(insights)} insights")
    for insight in insights[:2]:  # Show first 2
        print(f"  - {insight.get('type', 'Unknown')}: {insight.get('description', 'No description')}")
    
    # Generate recommendations
    recommendations = analyzer.generate_recommendations()
    print(f"✓ Generated {len(recommendations)} recommendations")
    
    # Get quality metrics
    quality = analyzer.get_quality_metrics()
    print(f"✓ Quality metrics: {quality.get('resolution_rate', 0):.1%} resolution rate")
    
    return analyzer

def test_exporter(manager, analyzer):
    """Test NotesExporter functionality"""
    print("\n=== Testing NotesExporter ===")
    
    exporter = NotesExporter(manager)
    
    # Test JSON export
    json_file = "data/ai_notes/test_export.json"
    success = exporter.export_notes_to_json(json_file, min_priority=1)
    print(f"✓ JSON export: {success}")
    
    # Test insights report
    report_file = "data/ai_notes/test_insights_report.md"
    success = exporter.export_insights_report(report_file)
    print(f"✓ Insights report export: {success}")
    
    # Test dashboard export
    dashboard_file = "data/ai_notes/test_dashboard.json"
    success = exporter.export_summary_dashboard(dashboard_file)
    print(f"✓ Dashboard export: {success}")
    
    # Test CSV export
    csv_file = "data/ai_notes/test_export.csv"
    success = exporter.export_notes_to_csv(csv_file)
    print(f"✓ CSV export: {success}")
    
    return exporter

def test_integration(manager):
    """Test NotesIntegration functionality"""
    print("\n=== Testing NotesIntegration ===")
    
    integration = NotesIntegration(manager)
    
    # Test AI analysis observation logging
    mock_analysis = {
        'total_low_confidence': 15,
        'suggestions': [
            {'type': 'material', 'pattern': 'SS', 'confidence': 0.9},
            {'type': 'company', 'pattern': 'SMITH', 'confidence': 0.8}
        ]
    }
    
    note_id = integration.log_ai_analysis_observation("test_batch_001", mock_analysis)
    print(f"✓ Logged AI analysis observation: {note_id}")
    
    # Test rule suggestion logging
    suggestion = {'type': 'material', 'pattern': 'DI', 'confidence': 0.85}
    suggestion_note_id = integration.log_rule_suggestion(suggestion)
    print(f"✓ Logged rule suggestion: {suggestion_note_id}")
    
    # Test human decision logging
    feedback_id = integration.log_human_rule_decision(
        suggestion_note_id, "accept", "Good suggestion, implemented"
    )
    print(f"✓ Logged human decision: {feedback_id}")
    
    # Test batch findings logging
    mock_batch_results = [
        {'confidence_level': 'High', 'original_description': 'SMITH 6" DI PIPE'},
        {'confidence_level': 'Low', 'original_description': 'MUELLER PART 123'},
        {'confidence_level': 'Low', 'original_description': 'CI FITTING'}
    ]
    
    finding_notes = integration.log_batch_processing_findings(mock_batch_results, "test_batch_002")
    print(f"✓ Logged {len(finding_notes)} batch findings")
    
    # Test dashboard summary
    dashboard_summary = integration.get_notes_summary_for_dashboard()
    print(f"✓ Dashboard summary: {dashboard_summary}")
    
    return integration

def test_file_operations():
    """Test that files are created and accessible"""
    print("\n=== Testing File Operations ===")
    
    # Check if data directory exists
    data_dir = Path("data/ai_notes")
    if data_dir.exists():
        print(f"✓ Notes directory exists: {data_dir}")
        
        # List files created
        files = list(data_dir.glob("*"))
        print(f"✓ Files in directory: {len(files)}")
        for file in files:
            print(f"  - {file.name}")
    else:
        print("⚠ Notes directory does not exist yet (will be created on first use)")
    
    return True

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting AI Notes System Tests")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Setup logging
        setup_logging("INFO")
        
        # Test components
        manager = test_notes_manager()
        analyzer = test_pattern_analyzer(manager)
        exporter = test_exporter(manager, analyzer)
        integration = test_integration(manager)
        test_file_operations()
        
        print("\n🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("1. Check the generated files in data/ai_notes/")
        print("2. Review the insights report: data/ai_notes/test_insights_report.md")
        print("3. Integrate with your existing batch processing workflow")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
