# src/rule_versioning/conflict_resolver.py
import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    """Types of conflicts that can occur between rules"""
    PATTERN_OVERLAP = "pattern_overlap"
    REGEX_CONFLICT = "regex_conflict"
    REPLACEMENT_AMBIGUITY = "replacement_ambiguity"
    PRIORITY_CONFLICT = "priority_conflict"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    PERFORMANCE_IMPACT = "performance_impact"

class ConflictSeverity(Enum):
    """Severity levels for conflicts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RuleConflict:
    """Represents a conflict between rules"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    rule1_id: str
    rule2_id: str
    rule1_data: Dict
    rule2_data: Dict
    description: str
    suggested_resolution: str
    impact_assessment: str
    auto_resolvable: bool = False

class ResolutionStrategy(Enum):
    """Strategies for resolving conflicts"""
    KEEP_HIGHER_PRIORITY = "keep_higher_priority"
    KEEP_MORE_SPECIFIC = "keep_more_specific"
    KEEP_NEWER = "keep_newer"
    MERGE_RULES = "merge_rules"
    MANUAL_REVIEW = "manual_review"
    DISABLE_CONFLICTING = "disable_conflicting"

class RuleConflictResolver:
    """
    Detects and resolves conflicts between rules with sophisticated
    pattern analysis and resolution strategies.
    """
    
    def __init__(self):
        self.conflict_history: List[RuleConflict] = []
        self.resolution_preferences: Dict[ConflictType, ResolutionStrategy] = {
            ConflictType.PATTERN_OVERLAP: ResolutionStrategy.KEEP_MORE_SPECIFIC,
            ConflictType.REGEX_CONFLICT: ResolutionStrategy.MANUAL_REVIEW,
            ConflictType.REPLACEMENT_AMBIGUITY: ResolutionStrategy.KEEP_HIGHER_PRIORITY,
            ConflictType.PRIORITY_CONFLICT: ResolutionStrategy.KEEP_NEWER,
            ConflictType.CIRCULAR_DEPENDENCY: ResolutionStrategy.DISABLE_CONFLICTING,
            ConflictType.PERFORMANCE_IMPACT: ResolutionStrategy.MANUAL_REVIEW
        }
    
    def detect_conflicts(self, new_rule: Dict, existing_rules: List[Dict]) -> List[RuleConflict]:
        """
        Detect potential conflicts between a new rule and existing rules
        
        Args:
            new_rule: The new rule to check for conflicts
            existing_rules: List of existing rules to check against
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            for existing_rule in existing_rules:
                rule_conflicts = self._analyze_rule_pair(new_rule, existing_rule)
                conflicts.extend(rule_conflicts)
            
            # Check for multi-rule conflicts
            multi_conflicts = self._detect_multi_rule_conflicts(new_rule, existing_rules)
            conflicts.extend(multi_conflicts)
            
            logger.info(f"Detected {len(conflicts)} conflicts for new rule")
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
        
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[RuleConflict], 
                         resolution_strategy: Optional[ResolutionStrategy] = None) -> Dict:
        """
        Resolve detected conflicts using specified or default strategies
        
        Args:
            conflicts: List of conflicts to resolve
            resolution_strategy: Optional override strategy
            
        Returns:
            Resolution results with actions taken
        """
        resolution_results = {
            'resolved_conflicts': [],
            'unresolved_conflicts': [],
            'actions_taken': [],
            'manual_review_required': []
        }
        
        try:
            for conflict in conflicts:
                strategy = resolution_strategy or self.resolution_preferences.get(
                    conflict.conflict_type, ResolutionStrategy.MANUAL_REVIEW
                )
                
                resolution_result = self._resolve_single_conflict(conflict, strategy)
                
                if resolution_result['resolved']:
                    resolution_results['resolved_conflicts'].append(conflict)
                    resolution_results['actions_taken'].extend(resolution_result['actions'])
                else:
                    resolution_results['unresolved_conflicts'].append(conflict)
                    resolution_results['manual_review_required'].append({
                        'conflict': conflict,
                        'reason': resolution_result['reason']
                    })
                
                # Store in history
                self.conflict_history.append(conflict)
            
            logger.info(f"Resolved {len(resolution_results['resolved_conflicts'])}/{len(conflicts)} conflicts")
            
        except Exception as e:
            logger.error(f"Error resolving conflicts: {e}")
        
        return resolution_results
    
    def get_conflict_report(self, conflicts: List[RuleConflict]) -> Dict:
        """Generate a comprehensive conflict report"""
        report = {
            'summary': {
                'total_conflicts': len(conflicts),
                'by_severity': {},
                'by_type': {},
                'auto_resolvable': 0
            },
            'critical_conflicts': [],
            'recommendations': [],
            'impact_analysis': {}
        }
        
        # Analyze conflicts
        for conflict in conflicts:
            # Severity distribution
            severity = conflict.severity.value
            report['summary']['by_severity'][severity] = report['summary']['by_severity'].get(severity, 0) + 1
            
            # Type distribution
            conflict_type = conflict.conflict_type.value
            report['summary']['by_type'][conflict_type] = report['summary']['by_type'].get(conflict_type, 0) + 1
            
            # Auto-resolvable count
            if conflict.auto_resolvable:
                report['summary']['auto_resolvable'] += 1
            
            # Critical conflicts
            if conflict.severity == ConflictSeverity.CRITICAL:
                report['critical_conflicts'].append({
                    'id': conflict.conflict_id,
                    'description': conflict.description,
                    'rules': [conflict.rule1_id, conflict.rule2_id],
                    'impact': conflict.impact_assessment
                })
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(conflicts)
        
        # Impact analysis
        report['impact_analysis'] = self._analyze_impact(conflicts)
        
        return report
    
    def _analyze_rule_pair(self, rule1: Dict, rule2: Dict) -> List[RuleConflict]:
        """Analyze a pair of rules for conflicts"""
        conflicts = []
        
        # Pattern overlap detection
        pattern_conflict = self._check_pattern_overlap(rule1, rule2)
        if pattern_conflict:
            conflicts.append(pattern_conflict)
        
        # Regex conflict detection
        regex_conflict = self._check_regex_conflicts(rule1, rule2)
        if regex_conflict:
            conflicts.append(regex_conflict)
        
        # Replacement ambiguity
        replacement_conflict = self._check_replacement_ambiguity(rule1, rule2)
        if replacement_conflict:
            conflicts.append(replacement_conflict)
        
        # Priority conflicts
        priority_conflict = self._check_priority_conflicts(rule1, rule2)
        if priority_conflict:
            conflicts.append(priority_conflict)
        
        return conflicts
    
    def _check_pattern_overlap(self, rule1: Dict, rule2: Dict) -> Optional[RuleConflict]:
        """Check if two rules have overlapping patterns"""
        pattern1 = rule1.get('pattern', '')
        pattern2 = rule2.get('pattern', '')
        
        if not pattern1 or not pattern2:
            return None
        
        try:
            # Test for overlapping matches
            test_strings = [
                "APPLE COMPANY",
                "BETA CORP",
                "TEST 123 KG",
                "SAMPLE CORPORATION",
                "DEMO CO."
            ]
            
            overlap_count = 0
            total_tests = len(test_strings)
            
            for test_str in test_strings:
                matches1 = re.findall(pattern1, test_str, re.IGNORECASE)
                matches2 = re.findall(pattern2, test_str, re.IGNORECASE)
                
                if matches1 and matches2:
                    overlap_count += 1
            
            overlap_ratio = overlap_count / total_tests
            
            if overlap_ratio > 0.3:  # 30% overlap threshold
                severity = ConflictSeverity.HIGH if overlap_ratio > 0.7 else ConflictSeverity.MEDIUM
                
                return RuleConflict(
                    conflict_id=f"pattern_overlap_{rule1.get('id', 'unknown')}_{rule2.get('id', 'unknown')}",
                    conflict_type=ConflictType.PATTERN_OVERLAP,
                    severity=severity,
                    rule1_id=rule1.get('id', 'unknown'),
                    rule2_id=rule2.get('id', 'unknown'),
                    rule1_data=rule1,
                    rule2_data=rule2,
                    description=f"Patterns overlap in {overlap_ratio:.1%} of test cases",
                    suggested_resolution="Keep more specific pattern or merge rules",
                    impact_assessment=f"May cause inconsistent replacements in {overlap_ratio:.1%} of cases",
                    auto_resolvable=overlap_ratio < 0.5
                )
        
        except re.error as e:
            logger.warning(f"Regex error checking pattern overlap: {e}")
        
        return None
    
    def _check_regex_conflicts(self, rule1: Dict, rule2: Dict) -> Optional[RuleConflict]:
        """Check for regex syntax conflicts"""
        pattern1 = rule1.get('pattern', '')
        pattern2 = rule2.get('pattern', '')
        
        try:
            # Compile patterns to check validity
            re.compile(pattern1)
            re.compile(pattern2)
            
            # Check for problematic regex constructs
            problematic_constructs = [
                r'\*\*',  # Double asterisk
                r'\+\+',  # Double plus
                r'\?\?',  # Double question mark
                r'.*.*',  # Multiple greedy quantifiers
            ]
            
            for construct in problematic_constructs:
                if re.search(construct, pattern1) or re.search(construct, pattern2):
                    return RuleConflict(
                        conflict_id=f"regex_conflict_{rule1.get('id', 'unknown')}_{rule2.get('id', 'unknown')}",
                        conflict_type=ConflictType.REGEX_CONFLICT,
                        severity=ConflictSeverity.MEDIUM,
                        rule1_id=rule1.get('id', 'unknown'),
                        rule2_id=rule2.get('id', 'unknown'),
                        rule1_data=rule1,
                        rule2_data=rule2,
                        description=f"Potentially problematic regex construct detected: {construct}",
                        suggested_resolution="Review and optimize regex patterns",
                        impact_assessment="May cause performance issues or unexpected behavior",
                        auto_resolvable=False
                    )
        
        except re.error as e:
            return RuleConflict(
                conflict_id=f"regex_error_{rule1.get('id', 'unknown')}_{rule2.get('id', 'unknown')}",
                conflict_type=ConflictType.REGEX_CONFLICT,
                severity=ConflictSeverity.CRITICAL,
                rule1_id=rule1.get('id', 'unknown'),
                rule2_id=rule2.get('id', 'unknown'),
                rule1_data=rule1,
                rule2_data=rule2,
                description=f"Invalid regex pattern: {e}",
                suggested_resolution="Fix regex syntax errors",
                impact_assessment="Rule will fail to execute",
                auto_resolvable=False
            )
        
        return None
    
    def _check_replacement_ambiguity(self, rule1: Dict, rule2: Dict) -> Optional[RuleConflict]:
        """Check for replacement ambiguities"""
        if (rule1.get('pattern') == rule2.get('pattern') and 
            rule1.get('replacement') != rule2.get('replacement')):
            
            return RuleConflict(
                conflict_id=f"replacement_conflict_{rule1.get('id', 'unknown')}_{rule2.get('id', 'unknown')}",
                conflict_type=ConflictType.REPLACEMENT_AMBIGUITY,
                severity=ConflictSeverity.HIGH,
                rule1_id=rule1.get('id', 'unknown'),
                rule2_id=rule2.get('id', 'unknown'),
                rule1_data=rule1,
                rule2_data=rule2,
                description="Same pattern with different replacements",
                suggested_resolution="Choose one replacement or merge into single rule",
                impact_assessment="Unpredictable replacement behavior",
                auto_resolvable=True
            )
        
        return None
    
    def _check_priority_conflicts(self, rule1: Dict, rule2: Dict) -> Optional[RuleConflict]:
        """Check for priority-related conflicts"""
        priority1 = rule1.get('priority', 0)
        priority2 = rule2.get('priority', 0)
        
        # Check if similar patterns have very different priorities
        pattern1 = rule1.get('pattern', '')
        pattern2 = rule2.get('pattern', '')
        
        if pattern1 and pattern2:
            # Simple similarity check
            similarity = self._calculate_pattern_similarity(pattern1, pattern2)
            priority_diff = abs(priority1 - priority2)
            
            if similarity > 0.7 and priority_diff > 3:
                return RuleConflict(
                    conflict_id=f"priority_conflict_{rule1.get('id', 'unknown')}_{rule2.get('id', 'unknown')}",
                    conflict_type=ConflictType.PRIORITY_CONFLICT,
                    severity=ConflictSeverity.MEDIUM,
                    rule1_id=rule1.get('id', 'unknown'),
                    rule2_id=rule2.get('id', 'unknown'),
                    rule1_data=rule1,
                    rule2_data=rule2,
                    description=f"Similar patterns with very different priorities ({priority1} vs {priority2})",
                    suggested_resolution="Review and align priorities",
                    impact_assessment="May cause inconsistent rule application order",
                    auto_resolvable=True
                )
        
        return None
    
    def _detect_multi_rule_conflicts(self, new_rule: Dict, existing_rules: List[Dict]) -> List[RuleConflict]:
        """Detect conflicts involving multiple rules"""
        conflicts = []
        
        # Check for circular dependencies
        circular_conflicts = self._detect_circular_dependencies(new_rule, existing_rules)
        conflicts.extend(circular_conflicts)
        
        # Check for performance impacts
        performance_conflicts = self._detect_performance_impacts(new_rule, existing_rules)
        conflicts.extend(performance_conflicts)
        
        return conflicts
    
    def _detect_circular_dependencies(self, new_rule: Dict, existing_rules: List[Dict]) -> List[RuleConflict]:
        """Detect circular dependencies between rules"""
        # Simplified circular dependency detection
        # In a real implementation, this would be more sophisticated
        conflicts = []
        
        new_pattern = new_rule.get('pattern', '')
        new_replacement = new_rule.get('replacement', '')
        
        for rule in existing_rules:
            rule_pattern = rule.get('pattern', '')
            rule_replacement = rule.get('replacement', '')
            
            # Check if new rule's replacement could trigger existing rule's pattern
            if (new_replacement and rule_pattern and 
                re.search(rule_pattern, new_replacement, re.IGNORECASE)):
                
                # Check if existing rule's replacement could trigger new rule's pattern
                if (rule_replacement and new_pattern and 
                    re.search(new_pattern, rule_replacement, re.IGNORECASE)):
                    
                    conflicts.append(RuleConflict(
                        conflict_id=f"circular_{new_rule.get('id', 'unknown')}_{rule.get('id', 'unknown')}",
                        conflict_type=ConflictType.CIRCULAR_DEPENDENCY,
                        severity=ConflictSeverity.CRITICAL,
                        rule1_id=new_rule.get('id', 'unknown'),
                        rule2_id=rule.get('id', 'unknown'),
                        rule1_data=new_rule,
                        rule2_data=rule,
                        description="Potential circular dependency detected",
                        suggested_resolution="Modify patterns or replacements to break cycle",
                        impact_assessment="Could cause infinite replacement loops",
                        auto_resolvable=False
                    ))
        
        return conflicts
    
    def _detect_performance_impacts(self, new_rule: Dict, existing_rules: List[Dict]) -> List[RuleConflict]:
        """Detect potential performance impacts"""
        conflicts = []
        
        # Check for overly complex patterns
        new_pattern = new_rule.get('pattern', '')
        if len(existing_rules) > 50 and len(new_pattern) > 100:  # Arbitrary thresholds
            conflicts.append(RuleConflict(
                conflict_id=f"performance_{new_rule.get('id', 'unknown')}",
                conflict_type=ConflictType.PERFORMANCE_IMPACT,
                severity=ConflictSeverity.MEDIUM,
                rule1_id=new_rule.get('id', 'unknown'),
                rule2_id="system",
                rule1_data=new_rule,
                rule2_data={},
                description=f"Complex pattern with {len(existing_rules)} existing rules may impact performance",
                suggested_resolution="Optimize pattern or consider rule prioritization",
                impact_assessment="May slow down processing with large datasets",
                auto_resolvable=False
            ))
        
        return conflicts
    
    def _resolve_single_conflict(self, conflict: RuleConflict, strategy: ResolutionStrategy) -> Dict:
        """Resolve a single conflict using the specified strategy"""
        result = {
            'resolved': False,
            'actions': [],
            'reason': ''
        }
        
        try:
            if strategy == ResolutionStrategy.KEEP_HIGHER_PRIORITY:
                result = self._resolve_by_priority(conflict)
            elif strategy == ResolutionStrategy.KEEP_MORE_SPECIFIC:
                result = self._resolve_by_specificity(conflict)
            elif strategy == ResolutionStrategy.KEEP_NEWER:
                result = self._resolve_by_age(conflict)
            elif strategy == ResolutionStrategy.MERGE_RULES:
                result = self._resolve_by_merging(conflict)
            elif strategy == ResolutionStrategy.DISABLE_CONFLICTING:
                result = self._resolve_by_disabling(conflict)
            else:
                result['reason'] = f"Manual review required for {conflict.conflict_type.value}"
        
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict.conflict_id}: {e}")
            result['reason'] = f"Error during resolution: {e}"
        
        return result
    
    def _resolve_by_priority(self, conflict: RuleConflict) -> Dict:
        """Resolve conflict by keeping higher priority rule"""
        rule1_priority = conflict.rule1_data.get('priority', 0)
        rule2_priority = conflict.rule2_data.get('priority', 0)
        
        if rule1_priority != rule2_priority:
            keep_rule = conflict.rule1_id if rule1_priority > rule2_priority else conflict.rule2_id
            remove_rule = conflict.rule2_id if rule1_priority > rule2_priority else conflict.rule1_id
            
            return {
                'resolved': True,
                'actions': [f"Keep rule {keep_rule} (higher priority)", f"Remove rule {remove_rule}"],
                'reason': 'Resolved by priority'
            }
        
        return {'resolved': False, 'actions': [], 'reason': 'Equal priorities'}
    
    def _resolve_by_specificity(self, conflict: RuleConflict) -> Dict:
        """Resolve conflict by keeping more specific rule"""
        pattern1 = conflict.rule1_data.get('pattern', '')
        pattern2 = conflict.rule2_data.get('pattern', '')
        
        # Simple specificity measure: length and character classes
        specificity1 = len(pattern1) + pattern1.count('\\')
        specificity2 = len(pattern2) + pattern2.count('\\')
        
        if specificity1 != specificity2:
            keep_rule = conflict.rule1_id if specificity1 > specificity2 else conflict.rule2_id
            remove_rule = conflict.rule2_id if specificity1 > specificity2 else conflict.rule1_id
            
            return {
                'resolved': True,
                'actions': [f"Keep rule {keep_rule} (more specific)", f"Remove rule {remove_rule}"],
                'reason': 'Resolved by specificity'
            }
        
        return {'resolved': False, 'actions': [], 'reason': 'Equal specificity'}
    
    def _resolve_by_age(self, conflict: RuleConflict) -> Dict:
        """Resolve conflict by keeping newer rule"""
        # This would need timestamp comparison in a real implementation
        return {
            'resolved': True,
            'actions': [f"Keep newer rule {conflict.rule1_id}", f"Archive older rule {conflict.rule2_id}"],
            'reason': 'Resolved by age (keeping newer)'
        }
    
    def _resolve_by_merging(self, conflict: RuleConflict) -> Dict:
        """Attempt to merge conflicting rules"""
        return {
            'resolved': False,
            'actions': [],
            'reason': 'Rule merging requires manual intervention'
        }
    
    def _resolve_by_disabling(self, conflict: RuleConflict) -> Dict:
        """Resolve by disabling conflicting rules"""
        return {
            'resolved': True,
            'actions': [f"Disable rule {conflict.rule1_id}", f"Disable rule {conflict.rule2_id}"],
            'reason': 'Disabled conflicting rules for safety'
        }
    
    def _calculate_pattern_similarity(self, pattern1: str, pattern2: str) -> float:
        """Calculate similarity between two patterns"""
        if not pattern1 or not pattern2:
            return 0.0
        
        # Simple character-based similarity
        longer = max(len(pattern1), len(pattern2))
        shorter = min(len(pattern1), len(pattern2))
        
        if longer == 0:
            return 1.0
        
        # Count common characters
        common = sum(1 for c1, c2 in zip(pattern1, pattern2) if c1 == c2)
        return common / longer
    
    def _generate_recommendations(self, conflicts: List[RuleConflict]) -> List[str]:
        """Generate recommendations based on conflict analysis"""
        recommendations = []
        
        if any(c.severity == ConflictSeverity.CRITICAL for c in conflicts):
            recommendations.append("CRITICAL: Address critical conflicts before proceeding")
        
        pattern_overlaps = sum(1 for c in conflicts if c.conflict_type == ConflictType.PATTERN_OVERLAP)
        if pattern_overlaps > 3:
            recommendations.append("Consider consolidating overlapping patterns into more general rules")
        
        if any(c.conflict_type == ConflictType.CIRCULAR_DEPENDENCY for c in conflicts):
            recommendations.append("Review rule dependencies to prevent infinite loops")
        
        auto_resolvable = sum(1 for c in conflicts if c.auto_resolvable)
        if auto_resolvable > 0:
            recommendations.append(f"{auto_resolvable} conflicts can be auto-resolved")
        
        return recommendations
    
    def _analyze_impact(self, conflicts: List[RuleConflict]) -> Dict:
        """Analyze the overall impact of conflicts"""
        return {
            'risk_level': 'HIGH' if any(c.severity == ConflictSeverity.CRITICAL for c in conflicts) else 'MEDIUM',
            'affected_rules': len(set(c.rule1_id for c in conflicts) | set(c.rule2_id for c in conflicts)),
            'resolution_complexity': 'HIGH' if any(not c.auto_resolvable for c in conflicts) else 'LOW'
        }
