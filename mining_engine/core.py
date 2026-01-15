"""
Core Mining Engine
Handles multi-threaded mining operations with AI optimization
"""

import asyncio
import threading
import time
import logging
import psutil
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import struct
import random

from .algorithms import AlgorithmManager
from .hardware import HardwareManager
from .optimizer import AIOptimizer
from .pool_manager import PoolManager
from ..miners.miner_integration import RealMinerIntegrator

logger = logging.getLogger(__name__)

@dataclass
class MiningStats:
    """Mining statistics and performance metrics"""
    hashrate: float = 0.0
    accepted_shares: int = 0
    rejected_shares: int = 0
    total_hashes: int = 0
    uptime: float = 0.0
    power_usage: float = 0.0
    temperature: Dict[str, float] = None
    algorithm: str = ""
    pool: str = ""
    workers_active: int = 0
    
    def __post_init__(self):
        if self.temperature is None:
            self.temperature = {}

@dataclass
class WorkerConfig:
    """Configuration for mining worker"""
    worker_id: str
    algorithm: str
    pool_url: str
    wallet_address: str
    threads: int = 0
    gpu_ids: List[int] = None
    intensity: int = 100
    
    def __post_init__(self):
        if self.gpu_ids is None:
            self.gpu_ids = []


class MiningEngine:
    """Advanced multi-algorithm mining engine with AI optimization"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.is_running = False
        self.start_time = 0
        self.stats = MiningStats()
        
        # Initialize core components
        self.hardware_manager = HardwareManager()
        self.algorithm_manager = AlgorithmManager()
        self.ai_optimizer = AIOptimizer()
        self.pool_manager = PoolManager()
        self.miner_integrator = RealMinerIntegrator()
        
        # Worker management
        self.workers: Dict[str, threading.Thread] = {}
        self.work_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        
        # Thread pool for mining operations
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.hardware_manager.get_optimal_thread_count()
        )
        
        logger.info("Mining engine initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load mining configuration"""
        default_config = {
            "algorithms": ["SHA256", "RandomX", "Ethash", "Scrypt", "Yescrypt", "Kawpow", "X11"],
            "pools": {
                "nicehash": {
                    "url": "stratum+tcp://sha256.nicehash.com:3334",
                    "user": "your_wallet_address",
                    "algorithm": "SHA256"
                },
                "mining_pool_hub": {
                    "url": "stratum+tcp://hub.miningpoolhub.com:20536",
                    "user": "your_username",
                    "algorithm": "RandomX"
                }
            },
            "optimization": {
                "enable_ai": True,
                "auto_switch_pools": True,
                "target_rejection_rate": 0.01,
                "work_segmentation": True
            },
            "hardware": {
                "cpu_threads": 0,  # 0 = auto-detect
                "gpu_intensity": 80,
                "temperature_limit": 85
            }
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Could not load config from {config_path}: {e}")
        
        return default_config
    
    async def start(self):
        """Start the mining engine"""
        if self.is_running:
            logger.warning("Mining engine is already running")
            return
        
        logger.info("Starting HPC Mining Engine...")
        self.is_running = True
        self.start_time = time.time()
        
        # Initialize hardware
        await self.hardware_manager.initialize()
        
        # Install real mining binaries
        await self.miner_integrator.install_miners()
        
        # Get AI-optimized mining configuration
        optimal_config = await self.ai_optimizer.optimize_mining_setup(
            self.hardware_manager.get_hardware_info(),
            self.config["algorithms"]
        )
        
        logger.info(f"AI Optimizer selected algorithm: {optimal_config['algorithm']}")
        logger.info(f"AI Optimizer selected pool: {optimal_config.get('pool_url', 'N/A')}")
        
        # Start mining workers
        await self._start_mining_workers(optimal_config)
        
        # Start monitoring and optimization loop
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._optimization_loop())
        
        logger.info("Mining engine started successfully")
    
    async def _start_mining_workers(self, config: Dict[str, Any]):
        """Start mining workers based on optimized configuration"""
        hardware_info = self.hardware_manager.get_hardware_info()
        
        # CPU workers
        if hardware_info["cpu"]["cores"] > 0:
            cpu_threads = config.get("cpu_threads", hardware_info["cpu"]["cores"])
            for i in range(cpu_threads):
                worker_config = WorkerConfig(
                    worker_id=f"cpu_worker_{i}",
                    algorithm=config["algorithm"],
                    pool_url=config["pool_url"],
                    wallet_address=config["wallet_address"],
                    threads=1
                )
                await self._start_worker(worker_config, "cpu")
        
        # GPU workers
        for gpu_id, gpu_info in enumerate(hardware_info["gpus"]):
            if gpu_info["available"]:
                worker_config = WorkerConfig(
                    worker_id=f"gpu_worker_{gpu_id}",
                    algorithm=config["algorithm"],
                    pool_url=config["pool_url"],
                    wallet_address=config["wallet_address"],
                    gpu_ids=[gpu_id],
                    intensity=config.get("gpu_intensity", 80)
                )
                await self._start_worker(worker_config, "gpu")
    
    async def _start_worker(self, config: WorkerConfig, worker_type: str):
        """Start individual mining worker"""
        worker_thread = threading.Thread(
            target=self._mining_worker,
            args=(config, worker_type),
            daemon=True
        )
        worker_thread.start()
        self.workers[config.worker_id] = worker_thread
        
        logger.info(f"Started {worker_type} worker: {config.worker_id}")
    
    def _mining_worker(self, config: WorkerConfig, worker_type: str):
        """Mining worker thread function"""
        logger.info(f"Mining worker {config.worker_id} starting...")
        
        # Get algorithm implementation
        algorithm = self.algorithm_manager.get_algorithm(config.algorithm)
        if not algorithm:
            logger.error(f"Algorithm {config.algorithm} not supported")
            return
        
        while self.is_running:
            try:
                # Get work from pool
                work = self.pool_manager.get_work(config.pool_url)
                if not work:
                    time.sleep(1)
                    continue
                
                # Apply AI-powered work segmentation
                segments = self.ai_optimizer.segment_work(work, config.worker_id)
                
                for segment in segments:
                    if not self.is_running:
                        break
                    
                    # Mine the segment
                    result = algorithm.mine(segment, worker_type, config)
                    
                    if result and result.get("valid"):
                        # Submit result to pool
                        success = self.pool_manager.submit_share(
                            config.pool_url, result
                        )
                        
                        if success:
                            self.stats.accepted_shares += 1
                            logger.debug(f"Share accepted from {config.worker_id}")
                        else:
                            self.stats.rejected_shares += 1
                            # Feed rejection info to AI for optimization
                            self.ai_optimizer.record_rejection(result, config.worker_id)
                
            except Exception as e:
                logger.error(f"Error in mining worker {config.worker_id}: {e}")
                time.sleep(5)
    
    async def _monitoring_loop(self):
        """Monitoring loop for statistics and health"""
        while self.is_running:
            try:
                # Update statistics
                self.stats.uptime = time.time() - self.start_time
                self.stats.workers_active = len([w for w in self.workers.values() if w.is_alive()])
                
                # Get hardware metrics
                hw_metrics = self.hardware_manager.get_metrics()
                self.stats.temperature = hw_metrics.get("temperature", {})
                self.stats.power_usage = hw_metrics.get("power", 0.0)
                
                # Calculate hashrate
                if self.stats.uptime > 0:
                    self.stats.hashrate = self.stats.total_hashes / self.stats.uptime
                
                # Log statistics every 30 seconds
                if int(self.stats.uptime) % 30 == 0:
                    logger.info(
                        f"Stats - Hashrate: {self.stats.hashrate:.2f} H/s, "
                        f"Accepted: {self.stats.accepted_shares}, "
                        f"Rejected: {self.stats.rejected_shares}, "
                        f"Workers: {self.stats.workers_active}"
                    )
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _optimization_loop(self):
        """AI optimization loop"""
        while self.is_running:
            try:
                # Run AI optimization every 5 minutes
                await asyncio.sleep(300)
                
                if not self.config["optimization"]["enable_ai"]:
                    continue
                
                logger.info("Running AI optimization...")
                
                # Get current performance metrics
                current_metrics = {
                    "hashrate": self.stats.hashrate,
                    "rejection_rate": self.stats.rejected_shares / max(1, self.stats.accepted_shares + self.stats.rejected_shares),
                    "temperature": self.stats.temperature,
                    "power_usage": self.stats.power_usage
                }
                
                # Get AI recommendations
                recommendations = await self.ai_optimizer.get_recommendations(current_metrics)
                
                # Apply recommendations
                if recommendations:
                    await self._apply_optimizations(recommendations)
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)
    
    async def _apply_optimizations(self, recommendations: Dict[str, Any]):
        """Apply AI optimization recommendations"""
        logger.info(f"Applying AI optimizations: {recommendations}")
        
        # Pool switching
        if recommendations.get("switch_pool"):
            new_pool = recommendations["switch_pool"]
            logger.info(f"AI recommends switching to pool: {new_pool}")
            # Implementation would restart workers with new pool
        
        # Algorithm switching
        if recommendations.get("switch_algorithm"):
            new_algorithm = recommendations["switch_algorithm"]
            logger.info(f"AI recommends switching to algorithm: {new_algorithm}")
            # Implementation would restart workers with new algorithm
        
        # Worker redistribution
        if recommendations.get("redistribute_workers"):
            redistribution = recommendations["redistribute_workers"]
            logger.info(f"AI recommends worker redistribution: {redistribution}")
            # Implementation would adjust worker configurations
    
    async def stop(self):
        """Stop the mining engine"""
        logger.info("Stopping mining engine...")
        self.is_running = False
        
        # Wait for workers to stop
        for worker_id, worker in self.workers.items():
            worker.join(timeout=5)
            logger.info(f"Stopped worker: {worker_id}")
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("Mining engine stopped")
    
    def get_stats(self) -> MiningStats:
        """Get current mining statistics"""
        return self.stats
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed mining status"""
        return {
            "running": self.is_running,
            "uptime": self.stats.uptime,
            "stats": asdict(self.stats),
            "hardware": self.hardware_manager.get_hardware_info(),
            "workers": list(self.workers.keys())
        }