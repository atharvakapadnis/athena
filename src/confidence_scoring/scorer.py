# src/confidence_scoring/scorer.py
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ConfidenceFactors:
    """Factors contributing to confidence score"""
    feature_extraction_score: float = 0.0
    hts_context_score: float = 0.0
    pattern_match_score: float = 0.0
    completeness_score: float = 0.0
    consistency_score: float = 0.0

class ConfidenceScorer:
    """Calculates confidence scores for description generation results"""
    
    def __init__(self):
        self.logger = logger
        self.feature_weights = {
            'product_type': 0.25,
            'dimensions': 0.20,
            'company': 0.15,
            'specification': 0.15,
            'connection_type': 0.15,
            'material': 0.10
        }
    
    def calculate_confidence(self, result: Dict) -> Tuple[float, ConfidenceFactors]:
        """Calculate confidence score and contributing factors"""
        factors = ConfidenceFactors()
        
        # Feature extraction scoring
        factors.feature_extraction_score = self._score_feature_extraction(result)
        
        # HTS context scoring
        factors.hts_context_score = self._score_hts_context(result)
        
        # Pattern match scoring
        factors.pattern_match_score = self._score_pattern_matches(result)
        
        # Completeness scoring
        factors.completeness_score = self._score_completeness(result)
        
        # Consistency scoring
        factors.consistency_score = self._score_consistency(result)
        
        # Calculate weighted total
        total_score = (
            factors.feature_extraction_score * 0.4 +
            factors.hts_context_score * 0.2 +
            factors.pattern_match_score * 0.2 +
            factors.completeness_score * 0.1 +
            factors.consistency_score * 0.1
        )
        
        return min(total_score, 1.0), factors
    
    def _score_feature_extraction(self, result: Dict) -> float:
        """Score feature extraction quality"""
        extracted_features = result.get('extracted_features', {})
        original_description = result.get('original_description', '')
        
        if not original_description:
            return 0.0
        
        score = 0.0
        total_weight = 0.0
        
        for feature, weight in self.feature_weights.items():
            if feature in extracted_features:
                score += weight
            total_weight += weight
        
        # Bonus for extracting multiple features
        feature_count = len(extracted_features)
        if feature_count >= 3:
            score += 0.1
        elif feature_count >= 2:
            score += 0.05
        
        return min(score / total_weight + 0.1, 1.0)
    
    def _score_hts_context(self, result: Dict) -> float:
        """Score HTS context integration"""
        hts_context = result.get('hts_context', {})
        
        score = 0.0
        
        if hts_context.get('hierarchical_description'):
            score += 0.4
        if hts_context.get('product_category'):
            score += 0.3
        if hts_context.get('material_requirements'):
            score += 0.3
        
        return score
    
    def _score_pattern_matches(self, result: Dict) -> float:
        """Score pattern matching quality"""
        original = result.get('original_description', '')
        enhanced = result.get('enhanced_description', '')
        
        if not original or not enhanced:
            return 0.0
        
        # Check for key information preservation
        score = 0.0
        
        # Preserve numbers
        original_numbers = re.findall(r'\d+(?:\.\d+)?', original)
        enhanced_numbers = re.findall(r'\d+(?:\.\d+)?', enhanced)
        if len(original_numbers) > 0:
            preserved_ratio = len(set(enhanced_numbers) & set(original_numbers)) / len(original_numbers)
            score += preserved_ratio * 0.4
        
        # Preserve key words
        original_words = set(re.findall(r'\b[A-Z]{2,}\b', original.upper()))
        enhanced_words = set(re.findall(r'\b[A-Z]{2,}\b', enhanced.upper()))
        if len(original_words) > 0:
            preserved_ratio = len(enhanced_words & original_words) / len(original_words)
            score += preserved_ratio * 0.3
        
        # Length appropriateness
        length_ratio = len(enhanced) / len(original) if len(original) > 0 else 0
        if 0.5 <= length_ratio <= 3.0:
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_completeness(self, result: Dict) -> float:
        """Score description completeness"""
        enhanced = result.get('enhanced_description', '')
        
        if not enhanced:
            return 0.0
        
        score = 0.0
        
        # Check for essential components
        if any(word in enhanced.lower() for word in ['inch', 'mm', 'cm']):
            score += 0.3
        if any(word in enhanced.lower() for word in ['fitting', 'valve', 'flange', 'coupling']):
            score += 0.3
        if any(word in enhanced.lower() for word in ['iron', 'steel', 'stainless']):
            score += 0.2
        if len(enhanced.split()) >= 5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_consistency(self, result: Dict) -> float:
        """Score internal consistency"""
        enhanced = result.get('enhanced_description', '')
        extracted_features = result.get('extracted_features', {})
        
        if not enhanced:
            return 0.0
        
        score = 1.0
        
        # Check for contradictions
        if 'dimensions' in extracted_features:
            dims = extracted_features['dimensions']
            if 'inch' in dims.lower() and 'mm' in enhanced.lower():
                score -= 0.3
            if 'mm' in dims.lower() and 'inch' in enhanced.lower():
                score -= 0.3
        
        # Check for redundancy
        words = enhanced.lower().split()
        if len(set(words)) / len(words) < 0.7:
            score -= 0.2
        
        return max(score, 0.0)
