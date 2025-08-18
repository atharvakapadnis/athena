# src/rule_editor/__init__.py
"""
Interactive Rule Editor Module

Provides human-in-the-loop rule management interface for reviewing,
approving, modifying, and rejecting AI-suggested rules.

Components:
- RuleReviewInterface: Displays AI suggestions for human review
- RuleValidator: Validates rule syntax and potential conflicts  
- RuleManager: Manages rule storage, versioning, and application
- ApprovalWorkflow: Handles human approval/rejection process
"""

from .interface import RuleReviewInterface, RuleSuggestion, RuleDecision
from .validator import RuleValidator, ValidationResult
from .manager import RuleManager
from .workflow import ApprovalWorkflow, ApprovalRequest

__all__ = [
    'RuleReviewInterface',
    'RuleSuggestion', 
    'RuleDecision',
    'RuleValidator',
    'ValidationResult',
    'RuleManager',
    'ApprovalWorkflow',
    'ApprovalRequest'
]
