# src/rule_editor/validator.py
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of rule validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    conflicts: List[str]

class RuleValidator:
    """Validates rule syntax and potential conflicts"""
    
    def __init__(self, existing_rules: List[Dict]):
        self.existing_rules = existing_rules
    
    def validate_rule(self, rule: Dict) -> ValidationResult:
        """Validate a single rule"""
        errors = []
        warnings = []
        conflicts = []
        
        # Check required fields
        required_fields = ['rule_type', 'pattern', 'replacement']
        for field in required_fields:
            if field not in rule or not rule[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate pattern syntax
        if 'pattern' in rule and rule['pattern']:
            try:
                re.compile(rule['pattern'])
            except re.error as e:
                errors.append(f"Invalid regex pattern: {e}")
        
        # Check for potential conflicts
        conflicts.extend(self._check_conflicts(rule))
        
        # Check for warnings
        warnings.extend(self._check_warnings(rule))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            conflicts=conflicts
        )
    
    def _check_conflicts(self, rule: Dict) -> List[str]:
        """Check for conflicts with existing rules"""
        conflicts = []
        
        # Skip conflict checking if essential fields are missing
        if 'pattern' not in rule or 'rule_type' not in rule:
            return conflicts
        
        for existing_rule in self.existing_rules:
            # Skip if existing rule is missing essential fields
            if 'pattern' not in existing_rule or 'rule_type' not in existing_rule:
                continue
                
            # Check for overlapping patterns
            if self._patterns_overlap(rule['pattern'], existing_rule['pattern']):
                conflicts.append(f"Pattern overlaps with existing rule: {existing_rule['pattern']}")
            
            # Check for conflicting replacements
            if rule['rule_type'] == existing_rule['rule_type'] and \
               rule['pattern'] == existing_rule['pattern'] and \
               rule.get('replacement') != existing_rule.get('replacement'):
                conflicts.append(f"Conflicting replacement for pattern: {rule['pattern']}")
        
        return conflicts
    
    def _check_warnings(self, rule: Dict) -> List[str]:
        """Check for potential issues"""
        warnings = []
        
        # Very short patterns
        if len(rule.get('pattern', '')) < 2:
            warnings.append("Very short pattern may cause false matches")
        
        # Very long replacements
        if len(rule.get('replacement', '')) > 100:
            warnings.append("Very long replacement may affect performance")
        
        # Generic patterns
        if rule.get('pattern') in [r'\w+', r'\d+', r'.*']:
            warnings.append("Very generic pattern may cause unintended matches")
        
        # Empty replacement
        if not rule.get('replacement', '').strip():
            warnings.append("Empty replacement may remove content unintentionally")
        
        # Pattern same as replacement
        if rule.get('pattern') == rule.get('replacement'):
            warnings.append("Pattern and replacement are identical - rule has no effect")
        
        # Special characters in pattern without escaping
        special_chars = ['.', '*', '+', '?', '^', '$', '(', ')', '[', ']', '{', '}', '|', '\\']
        pattern = rule.get('pattern', '')
        for char in special_chars:
            if char in pattern and f'\\{char}' not in pattern:
                warnings.append(f"Special regex character '{char}' found - consider escaping if literal match intended")
                break
        
        return warnings
    
    def _patterns_overlap(self, pattern1: str, pattern2: str) -> bool:
        """Check if two patterns might overlap"""
        try:
            # Simple overlap detection - check if one pattern matches the other
            if re.search(pattern1, pattern2) or re.search(pattern2, pattern1):
                return True
            
            # Check for similar literal strings
            if pattern1.lower() in pattern2.lower() or pattern2.lower() in pattern1.lower():
                return True
                
        except re.error:
            pass
        
        return False
    
    def validate_rule_batch(self, rules: List[Dict]) -> Dict[str, ValidationResult]:
        """Validate a batch of rules"""
        results = {}
        
        for i, rule in enumerate(rules):
            rule_id = rule.get('id', f'rule_{i}')
            results[rule_id] = self.validate_rule(rule)
        
        return results
    
    def get_rule_conflicts(self, new_rules: List[Dict]) -> List[Dict]:
        """Get detailed conflict analysis between new rules and existing rules"""
        conflicts = []
        
        for new_rule in new_rules:
            for existing_rule in self.existing_rules:
                conflict_details = self._analyze_conflict(new_rule, existing_rule)
                if conflict_details:
                    conflicts.append(conflict_details)
        
        return conflicts
    
    def _analyze_conflict(self, rule1: Dict, rule2: Dict) -> Optional[Dict]:
        """Analyze specific conflict between two rules"""
        if rule1['rule_type'] != rule2['rule_type']:
            return None
        
        conflict_type = None
        severity = "low"
        
        if rule1['pattern'] == rule2['pattern']:
            if rule1['replacement'] != rule2['replacement']:
                conflict_type = "exact_pattern_different_replacement"
                severity = "high"
            else:
                conflict_type = "duplicate_rule"
                severity = "medium"
        elif self._patterns_overlap(rule1['pattern'], rule2['pattern']):
            conflict_type = "overlapping_patterns"
            severity = "medium"
        
        if conflict_type:
            return {
                'type': conflict_type,
                'severity': severity,
                'rule1': rule1,
                'rule2': rule2,
                'description': self._get_conflict_description(conflict_type, rule1, rule2)
            }
        
        return None
    
    def _get_conflict_description(self, conflict_type: str, rule1: Dict, rule2: Dict) -> str:
        """Get human-readable description of conflict"""
        descriptions = {
            'exact_pattern_different_replacement': f"Same pattern '{rule1['pattern']}' has different replacements: '{rule1['replacement']}' vs '{rule2['replacement']}'",
            'duplicate_rule': f"Duplicate rule with pattern '{rule1['pattern']}' and replacement '{rule1['replacement']}'",
            'overlapping_patterns': f"Patterns '{rule1['pattern']}' and '{rule2['pattern']}' may overlap"
        }
        
        return descriptions.get(conflict_type, "Unknown conflict type")
    
    def update_existing_rules(self, new_rules: List[Dict]):
        """Update the validator with new existing rules"""
        self.existing_rules.extend(new_rules)
    
    def remove_existing_rule(self, rule_id: str):
        """Remove a rule from existing rules"""
        self.existing_rules = [rule for rule in self.existing_rules if rule.get('id') != rule_id]
