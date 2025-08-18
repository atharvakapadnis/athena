# src/ai_analysis/pattern_analyzer.py
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class PatternAnalyzer:
    """Analyzes failure patterns in batch results"""
    
    def __init__(self):
        self.logger = logger
    
    def analyze_low_confidence_results(self, batch_results: List[Dict]) -> Dict:
        """Analyze patterns in low-confidence results"""
        low_confidence_items = [
            result for result in batch_results 
            if result.get('confidence_level') == 'Low'
        ]
        
        if not low_confidence_items:
            return {"message": "No low-confidence results to analyze"}
        
        analysis = {
            'total_low_confidence': len(low_confidence_items),
            'common_patterns': self._find_common_patterns(low_confidence_items),
            'missing_features': self._analyze_missing_features(low_confidence_items),
            'context_issues': self._analyze_context_issues(low_confidence_items),
            'suggestions': self._generate_suggestions(low_confidence_items)
        }
        
        self.logger.info(f"Analyzed {len(low_confidence_items)} low-confidence results")
        return analysis
    
    def _find_common_patterns(self, items: List[Dict]) -> Dict:
        """Find common patterns in low-confidence items"""
        patterns = {
            'common_words': Counter(),
            'number_patterns': Counter(),
            'abbreviations': Counter(),
            'special_chars': Counter()
        }
        
        for item in items:
            description = item.get('original_description', '').upper()
            
            # Common words
            words = re.findall(r'\b[A-Z]{2,}\b', description)
            patterns['common_words'].update(words)
            
            # Number patterns
            numbers = re.findall(r'\d+(?:\.\d+)?', description)
            patterns['number_patterns'].update(numbers)
            
            # Abbreviations
            abbrevs = re.findall(r'\b[A-Z]{2,4}\b', description)
            patterns['abbreviations'].update(abbrevs)
            
            # Special characters
            special = re.findall(r'[^\w\s]', description)
            patterns['special_chars'].update(special)
        
        return {k: dict(v.most_common(10)) for k, v in patterns.items()}
    
    def _analyze_missing_features(self, items: List[Dict]) -> Dict:
        """Analyze what features are missing from extractions"""
        missing_features = defaultdict(int)
        
        for item in items:
            extracted_features = item.get('extracted_features', {})
            
            # Check what's missing
            if not extracted_features.get('company'):
                missing_features['company'] += 1
            if not extracted_features.get('dimensions'):
                missing_features['dimensions'] += 1
            if not extracted_features.get('product_type'):
                missing_features['product_type'] += 1
            if not extracted_features.get('specification'):
                missing_features['specification'] += 1
            if not extracted_features.get('material'):
                missing_features['material'] += 1
            if not extracted_features.get('connection_type'):
                missing_features['connection_type'] += 1
        
        return dict(missing_features)
    
    def _analyze_context_issues(self, items: List[Dict]) -> List[Dict]:
        """Analyze context interpretation issues"""
        context_issues = []
        
        for item in items:
            original = item.get('original_description', '')
            enhanced = item.get('enhanced_description', '')
            
            # Check for obvious issues
            if len(enhanced) < len(original) * 0.5:
                context_issues.append({
                    'type': 'overly_short',
                    'original': original,
                    'enhanced': enhanced
                })
            
            # Check for missing key information
            if any(word in original.upper() for word in ['INCH', '"', 'MM', 'CM']) and 'dimensions' not in item.get('extracted_features', {}):
                context_issues.append({
                    'type': 'missing_dimensions',
                    'original': original,
                    'enhanced': enhanced
                })
            
            # Check for missing company names
            company_indicators = ['SMITH', 'BLAIR', 'MUELLER', 'TYLER', 'FORD', 'ROMAC']
            if any(company in original.upper() for company in company_indicators) and 'company' not in item.get('extracted_features', {}):
                context_issues.append({
                    'type': 'missing_company',
                    'original': original,
                    'enhanced': enhanced
                })
            
            # Check for specification codes
            if any(code in original.upper() for code in ['C153', 'C110', 'TN431', 'ANSI']) and 'specification' not in item.get('extracted_features', {}):
                context_issues.append({
                    'type': 'missing_specification',
                    'original': original,
                    'enhanced': enhanced
                })
        
        return context_issues
    
    def _generate_suggestions(self, items: List[Dict]) -> List[Dict]:
        """Generate rule suggestions based on analysis"""
        suggestions = []
        
        # Analyze common patterns for rule suggestions
        common_words = Counter()
        for item in items:
            words = re.findall(r'\b[A-Z]{2,}\b', item.get('original_description', '').upper())
            common_words.update(words)
        
        # Suggest company name rules
        potential_companies = [word for word, count in common_words.most_common(20) if count >= 2]
        known_companies = ['SMITH', 'BLAIR', 'MUELLER', 'TYLER', 'FORD', 'ROMAC', 'CONSOLIDATED']
        
        for company in potential_companies[:5]:
            if company in known_companies or len(company) > 3:
                suggestions.append({
                    'type': 'company',
                    'pattern': company,
                    'replacement': company.title(),
                    'confidence': 0.7,
                    'reasoning': f'Appears {common_words[company]} times in low-confidence results'
                })
        
        # Suggest specification rules
        spec_patterns = ['C153', 'C110', 'TN431', 'ANSI']
        for spec in spec_patterns:
            if any(spec in item.get('original_description', '') for item in items):
                suggestions.append({
                    'type': 'specification',
                    'pattern': spec,
                    'replacement': f'{spec} standard',
                    'confidence': 0.8,
                    'reasoning': f'Specification code found in low-confidence results'
                })
        
        # Suggest material rules
        material_patterns = {'DI': 'ductile iron', 'CI': 'cast iron', 'SS': 'stainless steel'}
        for pattern, replacement in material_patterns.items():
            if any(pattern in item.get('original_description', '') for item in items):
                suggestions.append({
                    'type': 'material',
                    'pattern': pattern,
                    'replacement': replacement,
                    'confidence': 0.9,
                    'reasoning': f'Material abbreviation {pattern} found in low-confidence results'
                })
        
        # Suggest dimension rules
        dimension_patterns = [r'\d+\s*"', r'\d+\s*INCH', r'\d+\s*MM']
        for pattern in dimension_patterns:
            if any(re.search(pattern, item.get('original_description', '').upper()) for item in items):
                suggestions.append({
                    'type': 'dimension',
                    'pattern': pattern,
                    'replacement': 'size measurement',
                    'confidence': 0.85,
                    'reasoning': f'Dimension pattern {pattern} found in low-confidence results'
                })
        
        return suggestions
    
    def analyze_confidence_distribution(self, batch_results: List[Dict]) -> Dict:
        """Analyze the distribution of confidence levels"""
        confidence_counts = {'High': 0, 'Medium': 0, 'Low': 0}
        
        for result in batch_results:
            confidence_level = result.get('confidence_level', 'Low')
            confidence_counts[confidence_level] += 1
        
        total = len(batch_results)
        confidence_percentages = {
            level: (count / total * 100) if total > 0 else 0
            for level, count in confidence_counts.items()
        }
        
        return {
            'counts': confidence_counts,
            'percentages': confidence_percentages,
            'total_items': total
        }
    
    def identify_improvement_opportunities(self, batch_results: List[Dict]) -> List[Dict]:
        """Identify specific opportunities for improvement"""
        opportunities = []
        
        # Low confidence rate analysis
        low_confidence_count = sum(1 for r in batch_results if r.get('confidence_level') == 'Low')
        total_count = len(batch_results)
        
        if low_confidence_count / total_count > 0.3:  # More than 30% low confidence
            opportunities.append({
                'type': 'high_low_confidence_rate',
                'description': f'{low_confidence_count}/{total_count} items have low confidence',
                'priority': 'high',
                'suggested_action': 'Focus on pattern analysis and rule creation'
            })
        
        # Missing feature analysis
        feature_counts = defaultdict(int)
        for result in batch_results:
            features = result.get('extracted_features', {})
            for feature_type in ['company', 'material', 'dimensions', 'specification']:
                if not features.get(feature_type):
                    feature_counts[feature_type] += 1
        
        for feature_type, count in feature_counts.items():
            if count / total_count > 0.4:  # More than 40% missing this feature
                opportunities.append({
                    'type': 'missing_feature',
                    'description': f'{count}/{total_count} items missing {feature_type} extraction',
                    'priority': 'medium',
                    'suggested_action': f'Create rules to improve {feature_type} recognition'
                })
        
        return opportunities
