# src/progress_tracking/__init__.py
"""
Progress Tracking Module for Smart Description Iterative Improvement

This module provides quality monitoring and progress tracking functionality
for the iterative improvement system.
"""

from .quality_monitor import QualityMonitor, QualityMetrics, TrendAnalysis

__all__ = [
    'QualityMonitor',
    'QualityMetrics', 
    'TrendAnalysis'
]

