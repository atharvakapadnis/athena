# src/integration_testing/__init__.py
"""
Integration Testing System for Smart Description Iterative Improvement System

This module provides comprehensive integration testing capabilities for all system components
working together, ensuring the entire iterative improvement system functions correctly as a cohesive unit.
"""

from .system_tester import SystemIntegrationTester, TestResult, IntegrationTest
from .component_tester import ComponentInteractionTester
from .performance_tester import PerformanceIntegrationTester
from .test_runner import IntegrationTestRunner
from .test_data_generator import TestDataGenerator

__all__ = [
    'SystemIntegrationTester',
    'ComponentInteractionTester', 
    'PerformanceIntegrationTester',
    'IntegrationTestRunner',
    'TestDataGenerator',
    'TestResult',
    'IntegrationTest'
]

# Version information
__version__ = "1.0.0"
__author__ = "Smart Description Iterative Improvement System"
