#!/usr/bin/env python3
"""
HPC Cryptominer Main Application
Advanced multi-algorithm mining with AI optimization and distributed orchestration
"""

import asyncio
import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mining_engine import MiningEngine, HardwareManager, AIOptimizer
from orchestrator.cluster_manager import ClusterManager
from dashboard import DashboardServer
from node import NodeAgent
from monitoring import PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/hpc_miner.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

class HPCMiner:
    """Main HPC Cryptominer application"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/app/config/mining_config.json"
        self.config = self._load_config()
        
        # Core components
        self.mining_engine: Optional[MiningEngine] = None
        self.cluster_manager: Optional[ClusterManager] = None
        self.dashboard_server: Optional[DashboardServer] = None
        self.node_agent: Optional[NodeAgent] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        
        # Runtime state
        self.running = False
        self.mode = "standalone"
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        logger.info("HPC Cryptominer initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load mining configuration"""
        default_config = {
            "mining": {
                "algorithms": ["SHA256", "RandomX", "Ethash", "Scrypt", "Yescrypt", "Kawpow", "X11"],
                "auto_start": True,
                "auto_switch": True,
                "target_rejection_rate": 0.01
            },
            "pools": {
                "nicehash_sha256": {
                    "name": "NiceHash SHA256",
                    "url": "stratum+tcp://sha256.nicehash.com:3334",
                    "username": "your_wallet_address",
                    "password": "x",
                    "algorithm": "SHA256"
                },
                "nicehash_randomx": {
                    "name": "NiceHash RandomX",  
                    "url": "stratum+tcp://randomx.nicehash.com:3380",
                    "username": "your_wallet_address",
                    "password": "x",
                    "algorithm": "RandomX"
                },
                "nicehash_ethash": {
                    "name": "NiceHash Ethash",
                    "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353", 
                    "username": "your_wallet_address",
                    "password": "x",
                    "algorithm": "Ethash"
                }
            },
            "hardware": {
                "cpu_threads": 0,  # 0 = auto-detect
                "gpu_intensity": 80,
                "temperature_limit": 85,
                "power_limit": 0  # 0 = no limit
            },
            "optimization": {
                "enable_ai": True,
                "learning_rate": 0.1,
                "optimization_interval": 300,
                "work_segmentation": True,
                "auto_pool_switch": True
            },
            "cluster": {
                "enable": False,
                "master_url": "",
                "node_port": 8080,
                "heartbeat_interval": 30
            },
            "monitoring": {
                "enable_web_dashboard": True,
                "dashboard_port": 8081,
                "metrics_port": 8082,
                "log_level": "INFO"
            },
            "integration": {
                "hashburst_ai": True,
                "nicehash_compatibility": True,
                "prometheus_metrics": True
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge configs (loaded overrides default)
                    self._deep_merge(default_config, loaded_config)
        except Exception as e:
            logger.warning(f"Could not load config from {self.config_path}: {e}")
            logger.info("Using default configuration")
        
        # Create config directory and save default config
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _deep_merge(self, dict1: Dict, dict2: Dict):
        """Deep merge dictionary dict2 into dict1"""
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                self._deep_merge(dict1[key], value)
            else:
                dict1[key] = value
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.stop())
    
    async def start_standalone_mode(self):
        """Start in standalone mining mode"""
        logger.info("Starting HPC Miner in standalone mode...")
        self.mode = "standalone"
        
        # Initialize mining engine
        self.mining_engine = MiningEngine(self.config_path)
        
        # Start performance monitoring
        if self.config["monitoring"]["enable_web_dashboard"]:
            self.performance_monitor = PerformanceMonitor(
                port=self.config["monitoring"]["metrics_port"]
            )
            await self.performance_monitor.start()
        
        # Start web dashboard
        if self.config["monitoring"]["enable_web_dashboard"]:
            self.dashboard_server = DashboardServer(
                mining_engine=self.mining_engine,
                port=self.config["monitoring"]["dashboard_port"]
            )
            await self.dashboard_server.start()
        
        # Start mining
        if self.config["mining"]["auto_start"]:
            await self.mining_engine.start()
        
        self.running = True
        logger.info("Standalone mode started successfully")
    
    async def start_cluster_mode(self):
        """Start in cluster master mode"""
        logger.info("Starting HPC Miner in cluster master mode...")
        self.mode = "cluster"
        
        # Initialize cluster manager
        self.cluster_manager = ClusterManager()
        await self.cluster_manager.start()
        
        # Initialize mining engine for local mining
        self.mining_engine = MiningEngine(self.config_path)
        
        # Start performance monitoring
        self.performance_monitor = PerformanceMonitor(
            cluster_manager=self.cluster_manager,
            port=self.config["monitoring"]["metrics_port"]
        )
        await self.performance_monitor.start()
        
        # Start web dashboard
        self.dashboard_server = DashboardServer(
            mining_engine=self.mining_engine,
            cluster_manager=self.cluster_manager,
            port=self.config["monitoring"]["dashboard_port"]
        )
        await self.dashboard_server.start()
        
        # Start local mining if configured
        if self.config["mining"]["auto_start"]:
            await self.mining_engine.start()
        
        self.running = True
        logger.info("Cluster master mode started successfully")
    
    async def start_node_mode(self, cluster_master: str):
        """Start in cluster node mode"""
        logger.info(f"Starting HPC Miner as cluster node (master: {cluster_master})...")
        self.mode = "node"
        
        # Initialize node agent
        self.node_agent = NodeAgent(
            cluster_master_url=cluster_master,
            node_port=self.config["cluster"]["node_port"],
            config=self.config
        )
        await self.node_agent.start()
        
        # Initialize mining engine for local mining
        self.mining_engine = MiningEngine(self.config_path)
        
        # Connect node agent to mining engine
        self.node_agent.set_mining_engine(self.mining_engine)
        
        self.running = True
        logger.info("Node mode started successfully")
    
    async def start_orchestrator_mode(self):
        """Start in orchestrator-only mode"""
        logger.info("Starting HPC Miner in orchestrator mode...")
        self.mode = "orchestrator"
        
        # Initialize cluster manager
        self.cluster_manager = ClusterManager()
        await self.cluster_manager.start()
        
        # Start performance monitoring
        self.performance_monitor = PerformanceMonitor(
            cluster_manager=self.cluster_manager,
            port=self.config["monitoring"]["metrics_port"]
        )
        await self.performance_monitor.start()
        
        # Start web dashboard
        self.dashboard_server = DashboardServer(
            cluster_manager=self.cluster_manager,
            port=self.config["monitoring"]["dashboard_port"]
        )
        await self.dashboard_server.start()
        
        self.running = True
        logger.info("Orchestrator mode started successfully")
    
    async def start_dashboard_mode(self):
        """Start in dashboard-only mode"""
        logger.info("Starting HPC Miner in dashboard mode...")
        self.mode = "dashboard"
        
        # Start web dashboard
        self.dashboard_server = DashboardServer(
            port=self.config["monitoring"]["dashboard_port"]
        )
        await self.dashboard_server.start()
        
        self.running = True
        logger.info("Dashboard mode started successfully")
    
    async def start_monitor_mode(self):
        """Start in monitoring-only mode"""
        logger.info("Starting HPC Miner in monitor mode...")
        self.mode = "monitor"
        
        # Start performance monitoring
        self.performance_monitor = PerformanceMonitor(
            port=self.config["monitoring"]["metrics_port"]
        )
        await self.performance_monitor.start()
        
        self.running = True
        logger.info("Monitor mode started successfully")
    
    async def run_main_loop(self):
        """Main application loop"""
        logger.info("HPC Miner main loop started")
        
        while self.running:
            try:
                # Health checks and status updates
                if self.mining_engine:
                    stats = self.mining_engine.get_stats()
                    logger.debug(
                        f"Mining Stats - Hashrate: {stats.hashrate:.2f} H/s, "
                        f"Accepted: {stats.accepted_shares}, "
                        f"Rejected: {stats.rejected_shares}"
                    )
                
                if self.cluster_manager:
                    cluster_status = self.cluster_manager.get_cluster_status()
                    logger.debug(
                        f"Cluster Stats - Nodes: {cluster_status['stats']['active_nodes']}, "
                        f"Total Hashrate: {cluster_status['stats']['total_hashrate']:.2f} H/s"
                    )
                
                # Sleep for a short interval
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)
    
    async def stop(self):
        """Stop all components"""
        if not self.running:
            return
        
        logger.info("Stopping HPC Miner...")
        self.running = False
        
        # Stop components in reverse order
        if self.dashboard_server:
            await self.dashboard_server.stop()
        
        if self.performance_monitor:
            await self.performance_monitor.stop()
        
        if self.node_agent:
            await self.node_agent.stop()
        
        if self.cluster_manager:
            await self.cluster_manager.stop()
        
        if self.mining_engine:
            await self.mining_engine.stop()
        
        logger.info("HPC Miner stopped successfully")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive application status"""
        status = {
            "running": self.running,
            "mode": self.mode,
            "uptime": time.time(),
            "config_path": self.config_path
        }
        
        if self.mining_engine:
            status["mining"] = self.mining_engine.get_status()
        
        if self.cluster_manager:
            status["cluster"] = self.cluster_manager.get_cluster_status()
        
        if self.node_agent:
            status["node"] = self.node_agent.get_status()
        
        return status

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="HPC Cryptominer with AI Optimization")
    parser.add_argument("--mode", 
                       choices=["standalone", "cluster", "node", "orchestrator", "dashboard", "monitor"],
                       default="standalone",
                       help="Operating mode")
    parser.add_argument("--config", 
                       default="/app/config/mining_config.json",
                       help="Configuration file path")
    parser.add_argument("--cluster-master",
                       help="Cluster master URL (for node mode)")
    parser.add_argument("--log-level",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       default="INFO",
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Print banner
    print("""
    ██╗  ██╗██████╗  ██████╗    ███╗   ███╗██╗███╗   ██╗███████╗██████╗ 
    ██║  ██║██╔══██╗██╔════╝    ████╗ ████║██║████╗  ██║██╔════╝██╔══██╗
    ███████║██████╔╝██║         ██╔████╔██║██║██╔██╗ ██║█████╗  ██████╔╝
    ██╔══██║██╔═══╝ ██║         ██║╚██╔╝██║██║██║╚██╗██║██╔══╝  ██╔══██╗
    ██║  ██║██║     ╚██████╗    ██║ ╚═╝ ██║██║██║ ╚████║███████╗██║  ██║
    ╚═╝  ╚═╝╚═╝      ╚═════╝    ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
    
    Advanced HPC Cryptominer with AI Optimization v1.0.0
    Algorithms: SHA-256, RandomX, Ethash, Scrypt, Yescrypt, Kawpow, X11
    Features: Multi-pool, AI optimization, Distributed mining, Container support
    Author: Gabriele Pegoraro
    System: HashBurst by Neurallity SA
    """)
    
    try:
        # Initialize application
        miner = HPCMiner(args.config)
        
        # Start based on mode
        if args.mode == "standalone":
            await miner.start_standalone_mode()
        elif args.mode == "cluster":
            await miner.start_cluster_mode()
        elif args.mode == "node":
            if not args.cluster_master:
                logger.error("--cluster-master required for node mode")
                return 1
            await miner.start_node_mode(args.cluster_master)
        elif args.mode == "orchestrator":
            await miner.start_orchestrator_mode()
        elif args.mode == "dashboard":
            await miner.start_dashboard_mode()
        elif args.mode == "monitor":
            await miner.start_monitor_mode()
        
        # Run main loop
        await miner.run_main_loop()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        if 'miner' in locals():
            await miner.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
