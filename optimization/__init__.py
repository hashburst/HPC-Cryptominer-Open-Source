"""
Advanced Optimization Modules
Phase 8 & 9 Implementation for HPC Cryptominer

This package contains advanced optimization engines for:
- AMD MI300 GPU optimization with power/thermal management
- Network optimization for zero rejected shares
- AI-powered performance optimization and profitability analysis
"""

from .gpu_optimizer import AMMI300Optimizer, GPUMetrics, OptimizationProfile
from .network_optimizer import NetworkOptimizer, PoolMetrics, NetworkMetrics
from .ai_performance_optimizer import AIPerformanceOptimizer, AlgorithmProfitability, PerformancePrediction, OptimizationRecommendation

__all__ = [
    'AMMI300Optimizer',
    'GPUMetrics', 
    'OptimizationProfile',
    'NetworkOptimizer',
    'PoolMetrics',
    'NetworkMetrics',
    'AIPerformanceOptimizer',
    'AlgorithmProfitability',
    'PerformancePrediction',
    'OptimizationRecommendation'
]

__version__ = "1.0.0"
__author__ = "HPC Cryptominer Team"