# src/rule_editor/interface.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class RuleSuggestion:
    """AI-suggested rule for review"""
    id: str
    rule_type: str
    pattern: str
    replacement: str
    confidence: float
    reasoning: str
    examples: List[str]
    priority: int
    suggested_by: str = "AI"
    timestamp: datetime = None

@dataclass
class RuleDecision:
    """Human decision on a rule suggestion"""
    rule_id: str
    decision: str  # 'approve', 'reject', 'modify'
    modified_rule: Optional[Dict] = None
    reasoning: str = ""
    reviewer: str = ""
    timestamp: datetime = None

class RuleReviewInterface:
    """Interface for reviewing AI-suggested rules"""
    
    def __init__(self):
        self.pending_suggestions = []
        self.decisions = []
    
    def add_suggestion(self, suggestion: RuleSuggestion):
        """Add a new rule suggestion for review"""
        suggestion.timestamp = datetime.now()
        self.pending_suggestions.append(suggestion)
    
    def get_pending_suggestions(self, priority_threshold: int = 0) -> List[RuleSuggestion]:
        """Get pending suggestions above priority threshold"""
        return [s for s in self.pending_suggestions if s.priority >= priority_threshold]
    
    def make_decision(self, rule_id: str, decision: str, 
                     modified_rule: Dict = None, reasoning: str = "", 
                     reviewer: str = "user") -> RuleDecision:
        """Make a decision on a rule suggestion"""
        rule_decision = RuleDecision(
            rule_id=rule_id,
            decision=decision,
            modified_rule=modified_rule,
            reasoning=reasoning,
            reviewer=reviewer,
            timestamp=datetime.now()
        )
        
        self.decisions.append(rule_decision)
        
        # Remove from pending if decision made
        self.pending_suggestions = [s for s in self.pending_suggestions if s.id != rule_id]
        
        return rule_decision
    
    def get_decision_history(self) -> List[RuleDecision]:
        """Get history of all decisions"""
        return self.decisions
    
    def display_suggestion(self, suggestion: RuleSuggestion) -> str:
        """Format a suggestion for display"""
        return f"""
Rule Suggestion #{suggestion.id}
Type: {suggestion.rule_type}
Pattern: {suggestion.pattern}
Replacement: {suggestion.replacement}
Confidence: {suggestion.confidence:.2f}
Priority: {suggestion.priority}
Reasoning: {suggestion.reasoning}
Examples: {', '.join(suggestion.examples)}
Suggested by: {suggestion.suggested_by}
Timestamp: {suggestion.timestamp}
"""
    
    def get_suggestion_by_id(self, rule_id: str) -> Optional[RuleSuggestion]:
        """Get a suggestion by its ID"""
        for suggestion in self.pending_suggestions:
            if suggestion.id == rule_id:
                return suggestion
        return None
    
    def get_suggestions_by_type(self, rule_type: str) -> List[RuleSuggestion]:
        """Get all pending suggestions of a specific type"""
        return [s for s in self.pending_suggestions if s.rule_type == rule_type]
    
    def get_high_priority_suggestions(self) -> List[RuleSuggestion]:
        """Get high priority suggestions (priority >= 3)"""
        return [s for s in self.pending_suggestions if s.priority >= 3]
    
    def export_decisions(self, filepath: str):
        """Export decision history to JSON file"""
        decisions_data = []
        for decision in self.decisions:
            decisions_data.append({
                'rule_id': decision.rule_id,
                'decision': decision.decision,
                'modified_rule': decision.modified_rule,
                'reasoning': decision.reasoning,
                'reviewer': decision.reviewer,
                'timestamp': decision.timestamp.isoformat() if decision.timestamp else None
            })
        
        with open(filepath, 'w') as f:
            json.dump(decisions_data, f, indent=2)
    
    def import_decisions(self, filepath: str):
        """Import decision history from JSON file"""
        with open(filepath, 'r') as f:
            decisions_data = json.load(f)
        
        for decision_data in decisions_data:
            decision = RuleDecision(
                rule_id=decision_data['rule_id'],
                decision=decision_data['decision'],
                modified_rule=decision_data.get('modified_rule'),
                reasoning=decision_data.get('reasoning', ''),
                reviewer=decision_data.get('reviewer', ''),
                timestamp=datetime.fromisoformat(decision_data['timestamp']) if decision_data.get('timestamp') else None
            )
            self.decisions.append(decision)
