"""
Advanced Monitoring and Analytics
Phase 9 Implementation for HPC Cryptominer

This package contains comprehensive monitoring and analytics systems for:
- High-verbose performance analytics
- Benchmarking and performance regression detection  
- Profitability tracking and ROI analysis
- Alert generation and health monitoring
"""

from .advanced_analytics import AdvancedAnalytics, PerformanceMetrics, BenchmarkResult, PerformanceAlert

__all__ = [
    'AdvancedAnalytics',
    'PerformanceMetrics',
    'BenchmarkResult', 
    'PerformanceAlert'
]

__version__ = "1.0.0"
__author__ = "HPC Cryptominer Team"