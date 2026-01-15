"""
Node Agent for Distributed Mining
Connects to cluster master and executes mining tasks
"""

__version__ = "1.0.0"
__author__ = "HPC Mining Team"

from .agent import NodeAgent

__all__ = ['NodeAgent']