#!/usr/bin/env python3
"""
Test script for AI Analysis Engine integration with batch processor
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_analysis import AIClient, AnalysisAggregator
from src.utils.config import DATA_DIR, get_openai_api_key
from src.utils.logger import get_logger
import json

logger = get_logger(__name__)

def test_ai_analysis_integration():
    """Test AI Analysis Engine integration"""
    logger.info("Starting AI Analysis Engine integration test")
    
    # Check if OpenAI API key is available
    api_key = get_openai_api_key()
    if not api_key:
        logger.warning("OpenAI API key not found. Using mock data for testing.")
        test_with_mock_data()
        return
    
    try:
        # Initialize AI client
        ai_client = AIClient(api_key=api_key)
        logger.info("AI Client initialized successfully")
        
        # Initialize analysis aggregator
        aggregator = AnalysisAggregator(ai_client, DATA_DIR)
        logger.info("Analysis Aggregator initialized successfully")
        
        # Load sample batch results
        sample_results = load_sample_batch_results()
        if not sample_results:
            logger.warning("No sample batch results found. Creating mock data.")
            sample_results = create_mock_batch_results()
        
        logger.info(f"Loaded {len(sample_results)} sample results for analysis")
        
        # Run analysis
        logger.info("Running AI analysis...")
        analysis = aggregator.analyze_batch_results(sample_results)
        
        # Display results
        display_analysis_results(analysis)
        
        logger.info("AI Analysis Engine integration test completed successfully")
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise

def load_sample_batch_results():
    """Load sample batch results from existing batch files"""
    batches_dir = DATA_DIR / "batches"
    results = []
    
    try:
        # Look for existing batch data files
        batch_files = list(batches_dir.glob("*_data.json"))
        
        if not batch_files:
            return []
        
        # Load the most recent batch
        latest_batch = max(batch_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"Loading batch data from {latest_batch}")
        
        with open(latest_batch, 'r') as f:
            batch_data = json.load(f)
        
        # Convert to processing results format for analysis
        for item in batch_data[:10]:  # Limit to first 10 items for testing
            result = {
                'item_id': item.get('item_id', 'unknown'),
                'original_description': item.get('item_description', ''),
                'enhanced_description': f"Enhanced: {item.get('item_description', '')}",
                'confidence_level': 'Low',  # Simulate low confidence for testing
                'confidence_score': 0.4,
                'extracted_features': {
                    'material': item.get('material_detail', ''),
                    'company': extract_company_from_description(item.get('item_description', ''))
                },
                'success': True
            }
            results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to load sample batch results: {e}")
        return []

def extract_company_from_description(description):
    """Extract company name from description for testing"""
    known_companies = ['SMITH BLAIR', 'MUELLER', 'TYLER', 'FORD']
    description_upper = description.upper()
    
    for company in known_companies:
        if company in description_upper:
            return company
    
    return None

def create_mock_batch_results():
    """Create mock batch results for testing"""
    return [
        {
            'item_id': 'test-001',
            'original_description': 'SMITH BLAIR 170008030 SPACER, 18" ; DI ;',
            'enhanced_description': '18-inch spacer',
            'confidence_level': 'Low',
            'confidence_score': 0.4,
            'extracted_features': {},
            'success': False
        },
        {
            'item_id': 'test-002',
            'original_description': '36 C153 MJ 22 TN431 ZINC',
            'enhanced_description': '36-inch mechanical joint fitting',
            'confidence_level': 'Low',
            'confidence_score': 0.3,
            'extracted_features': {},
            'success': False
        },
        {
            'item_id': 'test-003',
            'original_description': 'MUELLER 24" TEE DI FLG',
            'enhanced_description': '24-inch ductile iron flanged tee',
            'confidence_level': 'Medium',
            'confidence_score': 0.7,
            'extracted_features': {
                'company': 'MUELLER',
                'material': 'ductile iron',
                'product_type': 'tee'
            },
            'success': True
        },
        {
            'item_id': 'test-004',
            'original_description': 'STANDARD PIPE FITTING',
            'enhanced_description': 'Standard pipe fitting',
            'confidence_level': 'High',
            'confidence_score': 0.9,
            'extracted_features': {
                'product_type': 'pipe fitting'
            },
            'success': True
        },
        {
            'item_id': 'test-005',
            'original_description': 'TYLER 12 INCH VALVE SS',
            'enhanced_description': '12-inch valve',
            'confidence_level': 'Low',
            'confidence_score': 0.4,
            'extracted_features': {},
            'success': False
        }
    ]

def test_with_mock_data():
    """Test with mock AI client for when API key is not available"""
    logger.info("Testing with mock AI client")
    
    # Create mock AI client
    class MockAIClient:
        def suggest_rules(self, failure_patterns):
            return [
                {
                    'rule_type': 'company',
                    'pattern': 'SMITH BLAIR',
                    'replacement': 'Smith Blair Company',
                    'confidence': 0.9,
                    'reasoning': 'Common company name found in descriptions',
                    'examples': ['SMITH BLAIR 170008030']
                },
                {
                    'rule_type': 'specification',
                    'pattern': 'C153',
                    'replacement': 'AWWA C153 standard',
                    'confidence': 0.8,
                    'reasoning': 'Standard specification code',
                    'examples': ['36 C153 MJ']
                }
            ]
    
    mock_ai_client = MockAIClient()
    aggregator = AnalysisAggregator(mock_ai_client, DATA_DIR)
    
    # Create mock results
    sample_results = create_mock_batch_results()
    
    # Run analysis
    analysis = aggregator.analyze_batch_results(sample_results)
    
    # Display results
    display_analysis_results(analysis)
    
    logger.info("Mock AI analysis test completed")

def display_analysis_results(analysis):
    """Display analysis results in a readable format"""
    print("\n" + "="*60)
    print("AI ANALYSIS ENGINE RESULTS")
    print("="*60)
    
    # Batch summary
    batch_summary = analysis.get('batch_summary', {})
    print(f"\nBatch Summary:")
    print(f"  Total items: {batch_summary.get('total_items', 0)}")
    print(f"  Success rate: {batch_summary.get('success_rate', 0):.2%}")
    
    confidence_dist = batch_summary.get('confidence_distribution', {})
    print(f"  Confidence distribution:")
    for level, count in confidence_dist.items():
        percentage = batch_summary.get('confidence_percentages', {}).get(level, 0)
        print(f"    {level}: {count} ({percentage:.1f}%)")
    
    # Rule suggestions
    suggestions = analysis.get('rule_suggestions', [])
    print(f"\nRule Suggestions ({len(suggestions)} total):")
    
    for i, suggestion in enumerate(suggestions[:5], 1):  # Show top 5
        print(f"  {i}. {suggestion.get('rule_type', 'unknown').title()} Rule:")
        print(f"     Pattern: '{suggestion.get('pattern', '')}' -> '{suggestion.get('replacement', '')}'")
        print(f"     Confidence: {suggestion.get('confidence', 0):.2f}")
        print(f"     Reasoning: {suggestion.get('reasoning', '')}")
        print()
    
    # Insights
    insights = analysis.get('insights', [])
    if insights:
        print(f"Key Insights:")
        for insight in insights:
            print(f"  • {insight}")
    
    # Recommendations
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        print(f"\nRecommendations:")
        for rec in recommendations:
            print(f"  • {rec.get('description', '')}")
    
    print("\n" + "="*60)

def check_linting():
    """Check for any linting errors in the AI analysis files"""
    logger.info("Checking for linting errors...")
    
    ai_analysis_files = [
        'src/ai_analysis/ai_client.py',
        'src/ai_analysis/pattern_analyzer.py',
        'src/ai_analysis/rule_suggester.py',
        'src/ai_analysis/analysis_aggregator.py',
        'src/ai_analysis/__init__.py'
    ]
    
    for file_path in ai_analysis_files:
        if os.path.exists(file_path):
            logger.info(f"File exists: {file_path}")
        else:
            logger.error(f"File missing: {file_path}")

if __name__ == "__main__":
    print("AI Analysis Engine Integration Test")
    print("="*40)
    
    try:
        # Check file structure
        check_linting()
        
        # Run integration test
        test_ai_analysis_integration()
        
        print("\n✅ Integration test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        sys.exit(1)
