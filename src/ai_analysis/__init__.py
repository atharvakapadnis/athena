# src/ai_analysis/__init__.py
"""
AI Analysis Engine for Smart Description Iterative Improvement System

This module provides AI-powered analysis for failure pattern recognition and rule suggestion
to improve the smart description system iteratively.
"""

from .ai_client import AIClient
from .pattern_analyzer import PatternAnalyzer
from .rule_suggester import RuleSuggester, RuleSuggestion
from .analysis_aggregator import AnalysisAggregator
from .notes_manager import NotesManager, AINote, HumanFeedback
from .notes_pattern_analyzer import NotesPatternAnalyzer
from .notes_exporter import NotesExporter
# NotesIntegration functionality merged into NotesManager

__all__ = [
    'AIClient',
    'PatternAnalyzer', 
    'RuleSuggester',
    'RuleSuggestion',
    'AnalysisAggregator',
    'NotesManager',
    'AINote',
    'HumanFeedback',
    'NotesPatternAnalyzer',
    'NotesExporter',
    # 'NotesIntegration' - merged into NotesManager
]

# Version information
__version__ = "1.0.0"
__author__ = "Smart Description Iterative Improvement System"
