# src/rule_versioning/__init__.py
"""
Rule Versioning System

This module provides comprehensive rule versioning, storage, and conflict resolution
capabilities for the Athena Smart Description Iterative Improvement System.

Components:
- RuleVersionManager: Manages rule versions, creation, and rollback
- RuleStorage: Handles efficient storage and retrieval of rule versions
- RuleConflictResolver: Detects and resolves conflicts between rules
"""

from rule_versioning.version_manager import RuleVersionManager, RuleVersion
from rule_versioning.storage import RuleStorage
from rule_versioning.conflict_resolver import RuleConflictResolver

__all__ = [
    'RuleVersionManager',
    'RuleVersion', 
    'RuleStorage',
    'RuleConflictResolver'
]
