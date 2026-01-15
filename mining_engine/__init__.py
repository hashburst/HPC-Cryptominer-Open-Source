"""
HPC Cryptominer Engine
Advanced multi-algorithm mining engine with AI optimization
"""

__version__ = "1.0.0"
__author__ = "HPC Mining Team"

from .core import MiningEngine
from .algorithms import AlgorithmManager
from .hardware import HardwareManager
from .optimizer import AIOptimizer

__all__ = [
    'MiningEngine',
    'AlgorithmManager', 
    'HardwareManager',
    'AIOptimizer'
]