# src/confidence_scoring/categorizer.py
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

@dataclass
class ConfidenceThresholds:
    """Configurable confidence thresholds"""
    high_threshold: float = 0.8
    medium_threshold: float = 0.6
    low_threshold: float = 0.0

class ConfidenceCategorizer:
    """Categorizes confidence scores into levels"""
    
    def __init__(self, thresholds: ConfidenceThresholds = None):
        self.thresholds = thresholds or ConfidenceThresholds()
    
    def categorize(self, confidence_score: float) -> ConfidenceLevel:
        """Categorize confidence score into level"""
        if confidence_score >= self.thresholds.high_threshold:
            return ConfidenceLevel.HIGH
        elif confidence_score >= self.thresholds.medium_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def get_categorization_stats(self, results: List[Dict]) -> Dict:
        """Get statistics on confidence categorization"""
        levels = {'High': 0, 'Medium': 0, 'Low': 0}
        scores = []
        
        for result in results:
            level = result.get('confidence_level', 'Low')
            levels[level] += 1
            scores.append(result.get('confidence_score', 0.0))
        
        return {
            'distribution': levels,
            'total_items': len(results),
            'avg_score': sum(scores) / len(scores) if scores else 0.0,
            'high_confidence_rate': levels['High'] / len(results) if results else 0.0
        }
