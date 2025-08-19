# src/progress_tracking/__init__.py
"""
Progress Tracking Module for Smart Description Iterative Improvement

This module provides comprehensive progress tracking, metrics collection, 
performance analysis, and dashboard functionality for the iterative improvement system.
"""

from .quality_monitor import QualityMonitor, QualityMetrics, TrendAnalysis
from .metrics_collector import MetricsCollector, ProcessingMetrics, RuleMetrics
from .performance_analyzer import PerformanceAnalyzer
from .dashboard import ProgressDashboard

__all__ = [
    'QualityMonitor',
    'QualityMetrics', 
    'TrendAnalysis',
    'MetricsCollector',
    'ProcessingMetrics',
    'RuleMetrics',
    'PerformanceAnalyzer',
    'ProgressDashboard'
]

