"""
Debug utilities for Smart Description Iterative Improvement System
"""
import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
from .config import LOGS_DIR

def save_debug_data(data: Dict[str, Any], filename: str):
    """Save debug data to JSON file"""
    debug_dir = LOGS_DIR / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Add timestamp to data
    data['debug_timestamp'] = datetime.now().isoformat()
    
    filepath = debug_dir / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"Debug data saved to: {filepath}")

def load_debug_data(filename: str) -> Dict[str, Any]:
    """Load debug data from JSON file"""
    debug_dir = LOGS_DIR / "debug"
    filepath = debug_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Debug file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_batch_results(batch_results: List[Dict]) -> Dict[str, Any]:
    """Analyze batch processing results for debugging"""
    if not batch_results:
        return {"error": "No batch results provided"}
    
    analysis = {
        'total_items': len(batch_results),
        'successful_items': sum(1 for r in batch_results if r.get('success', False)),
        'failed_items': sum(1 for r in batch_results if not r.get('success', False)),
        'confidence_distribution': {},
        'error_analysis': {},
        'performance_metrics': {}
    }
    
    # Analyze confidence distribution
    confidence_levels = [r.get('confidence_level', 'Unknown') for r in batch_results]
    for level in set(confidence_levels):
        analysis['confidence_distribution'][level] = confidence_levels.count(level)
    
    # Analyze errors
    errors = [r.get('error_message', '') for r in batch_results if r.get('error_message')]
    error_counts = {}
    for error in errors:
        error_counts[error] = error_counts.get(error, 0) + 1
    analysis['error_analysis'] = error_counts
    
    # Performance metrics
    processing_times = [r.get('processing_time', 0) for r in batch_results]
    if processing_times:
        analysis['performance_metrics'] = {
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'min_processing_time': min(processing_times),
            'max_processing_time': max(processing_times),
            'total_processing_time': sum(processing_times)
        }
    
    return analysis

def compare_descriptions(original: str, enhanced: str, confidence_score: float) -> Dict[str, Any]:
    """Compare original and enhanced descriptions for debugging"""
    comparison = {
        'original_length': len(original),
        'enhanced_length': len(enhanced),
        'length_difference': len(enhanced) - len(original),
        'confidence_score': confidence_score,
        'improvement_ratio': len(enhanced) / len(original) if len(original) > 0 else 0,
        'original_words': len(original.split()),
        'enhanced_words': len(enhanced.split()),
        'word_difference': len(enhanced.split()) - len(original.split())
    }
    
    return comparison

def export_batch_to_csv(batch_results: List[Dict], filename: str):
    """Export batch results to CSV for external analysis"""
    debug_dir = LOGS_DIR / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame
    df_data = []
    for result in batch_results:
        row = {
            'item_id': result.get('item_id', ''),
            'original_description': result.get('original_description', ''),
            'enhanced_description': result.get('enhanced_description', ''),
            'confidence_score': result.get('confidence_score', 0.0),
            'confidence_level': result.get('confidence_level', ''),
            'success': result.get('success', False),
            'processing_time': result.get('processing_time', 0.0),
            'error_message': result.get('error_message', '')
        }
        
        # Add extracted features
        features = result.get('extracted_features', {})
        for key, value in features.items():
            row[f'feature_{key}'] = value
        
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    
    filepath = debug_dir / filename
    df.to_csv(filepath, index=False)
    print(f"Batch results exported to: {filepath}")

def create_debug_report(batch_id: str, batch_results: List[Dict], 
                       analysis_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a comprehensive debug report"""
    report = {
        'batch_id': batch_id,
        'timestamp': datetime.now().isoformat(),
        'batch_analysis': analyze_batch_results(batch_results),
        'analysis_results': analysis_results or {},
        'summary': {
            'total_items': len(batch_results),
            'success_rate': sum(1 for r in batch_results if r.get('success', False)) / len(batch_results) if batch_results else 0,
            'avg_confidence': sum(r.get('confidence_score', 0) for r in batch_results) / len(batch_results) if batch_results else 0
        }
    }
    
    # Save report
    save_debug_data(report, f"debug_report_{batch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    return report
