"""
Web Dashboard for HPC Cryptominer
Real-time monitoring and control interface
"""

__version__ = "1.0.0"
__author__ = "HPC Mining Team"

from .web_server import DashboardServer

__all__ = ['DashboardServer']