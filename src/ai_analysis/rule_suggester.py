# src/ai_analysis/rule_suggester.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class RuleSuggestion:
    """A suggested rule for the system"""
    rule_type: str  # company, specification, dimension, product_type, etc.
    pattern: str
    replacement: str
    confidence: float
    reasoning: str
    examples: List[str]
    priority: int = 1

class RuleSuggester:
    """Suggests new rules based on failure analysis"""
    
    def __init__(self, ai_client):
        self.ai_client = ai_client
        self.logger = logger
    
    def suggest_rules(self, failure_analysis: Dict) -> List[RuleSuggestion]:
        """Generate rule suggestions from failure analysis"""
        suggestions = []
        
        # Get AI suggestions
        ai_suggestions = self.ai_client.suggest_rules(failure_analysis)
        
        # Convert to RuleSuggestion objects
        for suggestion in ai_suggestions:
            rule_suggestion = RuleSuggestion(
                rule_type=suggestion.get('rule_type', 'unknown'),
                pattern=suggestion.get('pattern', ''),
                replacement=suggestion.get('replacement', ''),
                confidence=suggestion.get('confidence', 0.5),
                reasoning=suggestion.get('reasoning', ''),
                examples=suggestion.get('examples', []),
                priority=self._calculate_priority(suggestion)
            )
            suggestions.append(rule_suggestion)
        
        # Add pattern-based suggestions
        pattern_suggestions = self._generate_pattern_based_suggestions(failure_analysis)
        suggestions.extend(pattern_suggestions)
        
        # Sort by priority and confidence
        suggestions.sort(key=lambda x: (x.priority, x.confidence), reverse=True)
        
        self.logger.info(f"Generated {len(suggestions)} rule suggestions")
        return suggestions
    
    def _calculate_priority(self, suggestion: Dict) -> int:
        """Calculate priority for a rule suggestion"""
        priority = 1
        
        # Higher priority for company names and specifications
        if suggestion.get('rule_type') in ['company', 'specification']:
            priority += 2
        
        # Higher priority for high confidence suggestions
        if suggestion.get('confidence', 0) > 0.8:
            priority += 1
        
        # Higher priority for suggestions with examples
        if suggestion.get('examples'):
            priority += 1
        
        return priority
    
    def _generate_pattern_based_suggestions(self, failure_analysis: Dict) -> List[RuleSuggestion]:
        """Generate additional suggestions based on pattern analysis"""
        suggestions = []
        
        # Get pattern analysis data
        pattern_suggestions = failure_analysis.get('suggestions', [])
        common_patterns = failure_analysis.get('common_patterns', {})
        missing_features = failure_analysis.get('missing_features', {})
        
        # Convert pattern analyzer suggestions to RuleSuggestion objects
        for suggestion in pattern_suggestions:
            rule_suggestion = RuleSuggestion(
                rule_type=suggestion.get('type', 'unknown'),
                pattern=suggestion.get('pattern', ''),
                replacement=suggestion.get('replacement', ''),
                confidence=suggestion.get('confidence', 0.5),
                reasoning=suggestion.get('reasoning', ''),
                examples=[],
                priority=self._calculate_priority(suggestion)
            )
            suggestions.append(rule_suggestion)
        
        # Generate suggestions based on missing features
        if missing_features.get('company', 0) > 5:
            suggestions.append(RuleSuggestion(
                rule_type='company',
                pattern='[A-Z]+ [A-Z]+',
                replacement='company name',
                confidence=0.6,
                reasoning=f"Many items ({missing_features['company']}) missing company extraction",
                examples=[],
                priority=2
            ))
        
        if missing_features.get('specification', 0) > 3:
            suggestions.append(RuleSuggestion(
                rule_type='specification',
                pattern='[A-Z]\\d+',
                replacement='specification code',
                confidence=0.7,
                reasoning=f"Many items ({missing_features['specification']}) missing specification extraction",
                examples=[],
                priority=2
            ))
        
        # Generate suggestions based on common abbreviations
        common_abbrevs = common_patterns.get('abbreviations', {})
        for abbrev, count in common_abbrevs.items():
            if count >= 3 and len(abbrev) <= 4:
                # Try to categorize the abbreviation
                rule_type = self._categorize_abbreviation(abbrev)
                replacement = self._suggest_replacement(abbrev, rule_type)
                
                suggestions.append(RuleSuggestion(
                    rule_type=rule_type,
                    pattern=abbrev,
                    replacement=replacement,
                    confidence=0.6,
                    reasoning=f"Abbreviation '{abbrev}' appears {count} times in low-confidence results",
                    examples=[],
                    priority=1
                ))
        
        return suggestions
    
    def _categorize_abbreviation(self, abbrev: str) -> str:
        """Categorize an abbreviation into a rule type"""
        # Material abbreviations
        material_abbrevs = ['DI', 'CI', 'SS', 'CS', 'AL', 'PVC']
        if abbrev in material_abbrevs:
            return 'material'
        
        # Connection type abbreviations
        connection_abbrevs = ['MJ', 'FLG', 'TR', 'WLD', 'PO']
        if abbrev in connection_abbrevs:
            return 'connection_type'
        
        # Specification codes (typically start with letter and have numbers)
        if len(abbrev) >= 3 and abbrev[0].isalpha() and any(c.isdigit() for c in abbrev):
            return 'specification'
        
        # Product type abbreviations
        product_abbrevs = ['TEE', 'ELB', 'RED', 'CAP', 'COUP', 'FLG']
        if abbrev in product_abbrevs:
            return 'product_type'
        
        return 'unknown'
    
    def _suggest_replacement(self, abbrev: str, rule_type: str) -> str:
        """Suggest a replacement for an abbreviation"""
        # Known replacements
        replacements = {
            'DI': 'ductile iron',
            'CI': 'cast iron',
            'SS': 'stainless steel',
            'CS': 'carbon steel',
            'MJ': 'mechanical joint',
            'FLG': 'flanged',
            'TR': 'threaded',
            'WLD': 'welded',
            'PO': 'push-on',
            'TEE': 'tee fitting',
            'ELB': 'elbow',
            'RED': 'reducer',
            'CAP': 'cap',
            'COUP': 'coupling'
        }
        
        if abbrev in replacements:
            return replacements[abbrev]
        
        # Generic replacements based on rule type
        generic_replacements = {
            'material': f'{abbrev.lower()} material',
            'connection_type': f'{abbrev.lower()} connection',
            'specification': f'{abbrev} standard',
            'product_type': f'{abbrev.lower()} fitting',
            'unknown': abbrev.lower()
        }
        
        return generic_replacements.get(rule_type, abbrev.lower())
    
    def validate_suggestion(self, suggestion: RuleSuggestion) -> Dict:
        """Validate a rule suggestion"""
        validation = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check pattern validity
        if not suggestion.pattern:
            validation['valid'] = False
            validation['issues'].append("Empty pattern")
        
        # Check for potential conflicts
        if len(suggestion.pattern) < 2:
            validation['warnings'].append("Very short pattern may cause false matches")
        
        # Check confidence level
        if suggestion.confidence < 0.3:
            validation['warnings'].append("Low confidence suggestion")
        
        # Check if pattern is too generic
        if suggestion.pattern in ['A', 'THE', 'AND', 'OR']:
            validation['valid'] = False
            validation['issues'].append("Pattern is too generic")
        
        # Check replacement validity
        if not suggestion.replacement:
            validation['valid'] = False
            validation['issues'].append("Empty replacement")
        
        return validation
    
    def filter_suggestions(self, suggestions: List[RuleSuggestion], min_confidence: float = 0.5) -> List[RuleSuggestion]:
        """Filter suggestions based on confidence and validation"""
        filtered_suggestions = []
        
        for suggestion in suggestions:
            # Validate suggestion
            validation = self.validate_suggestion(suggestion)
            
            # Skip invalid suggestions
            if not validation['valid']:
                self.logger.warning(f"Skipping invalid suggestion: {suggestion.pattern} - {validation['issues']}")
                continue
            
            # Skip low confidence suggestions
            if suggestion.confidence < min_confidence:
                continue
            
            filtered_suggestions.append(suggestion)
        
        return filtered_suggestions
    
    def rank_suggestions(self, suggestions: List[RuleSuggestion]) -> List[RuleSuggestion]:
        """Rank suggestions by priority and confidence"""
        # Calculate composite score
        for suggestion in suggestions:
            suggestion.composite_score = (
                suggestion.priority * 0.6 + 
                suggestion.confidence * 0.4
            )
        
        # Sort by composite score
        return sorted(suggestions, key=lambda x: x.composite_score, reverse=True)
