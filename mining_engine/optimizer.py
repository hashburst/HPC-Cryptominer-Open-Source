"""
AI-Powered Mining Optimizer
Advanced optimization using machine learning for pool selection, work segmentation, and performance tuning
"""

import asyncio
import json
import logging
import time
import random
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    timestamp: float
    hashrate: float
    rejection_rate: float
    temperature: Dict[str, float]
    power_usage: float
    algorithm: str
    pool: str
    worker_id: str = ""

@dataclass
class OptimizationRecommendation:
    """AI optimization recommendation"""
    action: str
    confidence: float
    expected_improvement: float
    parameters: Dict[str, Any]
    reasoning: str

class WorkSegment:
    """Represents a work segment for distributed mining"""
    
    def __init__(self, segment_id: str, work_data: Dict[str, Any], nonce_range: Tuple[int, int]):
        self.segment_id = segment_id
        self.work_data = work_data
        self.nonce_start, self.nonce_end = nonce_range
        self.assigned_worker = ""
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.result: Optional[Dict[str, Any]] = None
        self.hash_count = 0

class AIOptimizer:
    """AI-powered mining optimizer with Hashburst-style intelligence"""
    
    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.performance_history = deque(maxlen=1000)
        self.rejection_history = deque(maxlen=500)
        self.pool_performance = defaultdict(list)
        self.worker_performance = defaultdict(list)
        self.algorithm_performance = defaultdict(list)
        
        # Work segmentation data
        self.active_segments: Dict[str, WorkSegment] = {}
        self.completed_segments = deque(maxlen=100)
        self.worker_efficiency = defaultdict(float)
        
        # AI model parameters (neural network weights)
        self.pool_selection_weights = np.random.random((10, 5))
        self.segmentation_weights = np.random.random((8, 4))
        
        logger.info("AI Optimizer initialized")
    
    async def optimize_mining_setup(self, hardware_info: Dict[str, Any], available_algorithms: List[str]) -> Dict[str, Any]:
        """Optimize initial mining setup using AI analysis"""
        logger.info("Running AI optimization for mining setup...")
        
        # Analyze hardware capabilities
        cpu_score = self._calculate_cpu_score(hardware_info.get("cpu", {}))
        gpu_score = self._calculate_gpu_score(hardware_info.get("gpus", []))
        memory_score = self._calculate_memory_score(hardware_info.get("memory", {}))
        
        # Select optimal algorithm based on hardware
        optimal_algorithm = await self._select_optimal_algorithm(
            available_algorithms, cpu_score, gpu_score, memory_score
        )
        
        # Select optimal pool
        optimal_pool = await self._select_optimal_pool(optimal_algorithm)
        
        # Calculate optimal worker configuration
        worker_config = await self._optimize_worker_configuration(hardware_info, optimal_algorithm)
        
        config = {
            "algorithm": optimal_algorithm,
            "pool_url": optimal_pool["url"],
            "wallet_address": optimal_pool.get("wallet", "your_wallet_address"),
            "cpu_threads": worker_config["cpu_threads"],
            "gpu_intensity": worker_config["gpu_intensity"],
            "optimization_confidence": 0.85
        }
        
        logger.info(f"AI selected configuration: {config}")
        return config
    
    def _calculate_cpu_score(self, cpu_info: Dict[str, Any]) -> float:
        """Calculate CPU mining performance score"""
        cores = cpu_info.get("cores", 1)
        threads = cpu_info.get("threads", 1)
        frequency = cpu_info.get("frequency", {}).get("max", 2000)
        features = cpu_info.get("features", [])
        
        base_score = cores * 10 + threads * 5 + (frequency / 1000) * 2
        
        # Bonus for mining-relevant features
        if "AES" in features:
            base_score *= 1.2
        if "AVX2" in features:
            base_score *= 1.1
        
        return min(base_score, 100.0)
    
    def _calculate_gpu_score(self, gpu_info: List[Dict[str, Any]]) -> float:
        """Calculate GPU mining performance score"""
        if not gpu_info:
            return 0.0
        
        total_score = 0.0
        for gpu in gpu_info:
            memory_gb = gpu.get("memory_total", 0) / (1024**3)
            gpu_name = gpu.get("name", "").upper()
            
            base_score = memory_gb * 10
            
            # High-end GPU bonuses
            if "H100" in gpu_name:
                base_score *= 3.0
            elif "H200" in gpu_name:
                base_score *= 3.5
            elif "MI300" in gpu_name:
                base_score *= 2.8
            elif "RTX" in gpu_name:
                base_score *= 1.5
            
            total_score += base_score
        
        return min(total_score, 100.0)
    
    def _calculate_memory_score(self, memory_info: Dict[str, Any]) -> float:
        """Calculate memory performance score"""
        total_gb = memory_info.get("total", 0) / (1024**3)
        available_percent = 100 - memory_info.get("percentage", 0)
        
        score = (total_gb * 2) + (available_percent * 0.5)
        return min(score, 100.0)
    
    async def _select_optimal_algorithm(self, algorithms: List[str], cpu_score: float, gpu_score: float, memory_score: float) -> str:
        """AI-powered algorithm selection"""
        algorithm_scores = {}
        
        for algorithm in algorithms:
            score = 0.0
            
            if algorithm == "RandomX":
                # RandomX favors CPU and memory
                score = cpu_score * 0.7 + memory_score * 0.3
            elif algorithm == "Ethash":
                # Ethash favors GPU memory
                score = gpu_score * 0.8 + memory_score * 0.2
            elif algorithm == "SHA256":
                # SHA256 can use both CPU and GPU effectively
                score = max(cpu_score, gpu_score) * 0.6 + min(cpu_score, gpu_score) * 0.4
            elif algorithm in ["Scrypt", "Yescrypt"]:
                # Memory-hard algorithms
                score = memory_score * 0.5 + cpu_score * 0.3 + gpu_score * 0.2
            elif algorithm in ["Kawpow", "X11"]:
                # GPU-optimized algorithms
                score = gpu_score * 0.7 + cpu_score * 0.3
            
            # Apply historical performance if available
            if algorithm in self.algorithm_performance:
                historical_avg = statistics.mean(self.algorithm_performance[algorithm][-10:])
                score = score * 0.7 + historical_avg * 0.3
            
            algorithm_scores[algorithm] = score
        
        # Select best algorithm
        best_algorithm = max(algorithm_scores, key=algorithm_scores.get)
        logger.info(f"AI algorithm selection scores: {algorithm_scores}")
        logger.info(f"Selected algorithm: {best_algorithm}")
        
        return best_algorithm
    
    async def _select_optimal_pool(self, algorithm: str) -> Dict[str, Any]:
        """AI-powered pool selection"""
        # Simulated pool database - in production, this would query real pool APIs
        pools = {
            "SHA256": [
                {"name": "NiceHash", "url": "stratum+tcp://sha256.nicehash.com:3334", "fee": 0.02, "latency": 50},
                {"name": "Slush Pool", "url": "stratum+tcp://stratum.slushpool.com:4444", "fee": 0.02, "latency": 60},
            ],
            "RandomX": [
                {"name": "NiceHash", "url": "stratum+tcp://randomx.nicehash.com:3380", "fee": 0.02, "latency": 55},
                {"name": "MineXMR", "url": "stratum+tcp://pool.minexmr.com:4444", "fee": 0.01, "latency": 70},
            ],
            "Ethash": [
                {"name": "NiceHash", "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353", "fee": 0.02, "latency": 45},
                {"name": "Ethermine", "url": "stratum+tcp://eth-us-east1.nanopool.org:9999", "fee": 0.01, "latency": 65},
            ]
        }
        
        available_pools = pools.get(algorithm, pools["SHA256"])
        
        # Calculate pool scores
        pool_scores = {}
        for pool in available_pools:
            # Base score calculation
            latency_score = max(0, 100 - pool["latency"])
            fee_score = (1 - pool["fee"]) * 100
            
            # Historical performance
            historical_score = 50  # Default
            if pool["name"] in self.pool_performance:
                recent_performance = self.pool_performance[pool["name"]][-5:]
                if recent_performance:
                    historical_score = statistics.mean(recent_performance)
            
            total_score = (latency_score * 0.3 + fee_score * 0.4 + historical_score * 0.3)
            pool_scores[pool["name"]] = {"score": total_score, "pool": pool}
        
        # Select best pool
        best_pool_name = max(pool_scores, key=lambda x: pool_scores[x]["score"])
        best_pool = pool_scores[best_pool_name]["pool"]
        
        logger.info(f"AI pool selection scores: {[(name, data['score']) for name, data in pool_scores.items()]}")
        logger.info(f"Selected pool: {best_pool_name}")
        
        return best_pool
    
    async def _optimize_worker_configuration(self, hardware_info: Dict[str, Any], algorithm: str) -> Dict[str, Any]:
        """Optimize worker thread and GPU configuration"""
        cpu_info = hardware_info.get("cpu", {})
        gpu_info = hardware_info.get("gpus", [])
        memory_info = hardware_info.get("memory", {})
        
        # Base configuration
        config = {
            "cpu_threads": max(1, cpu_info.get("cores", 1) - 1),
            "gpu_intensity": 80
        }
        
        # Algorithm-specific optimizations
        if algorithm == "RandomX":
            # RandomX needs about 2GB RAM per thread
            available_memory_gb = memory_info.get("available", 0) / (1024**3)
            max_threads_by_memory = int(available_memory_gb // 2)
            config["cpu_threads"] = min(config["cpu_threads"], max_threads_by_memory)
            config["gpu_intensity"] = 0  # RandomX is CPU-only
            
        elif algorithm == "Ethash":
            # Ethash is GPU-intensive
            config["cpu_threads"] = 1  # Minimal CPU usage
            config["gpu_intensity"] = 100
            
        elif algorithm == "SHA256":
            # SHA256 can use both effectively
            if gpu_info:
                config["gpu_intensity"] = 90
                config["cpu_threads"] = max(1, cpu_info.get("cores", 1) // 2)
        
        return config
    
    def segment_work(self, work: Dict[str, Any], worker_id: str) -> List[Dict[str, Any]]:
        """AI-powered work segmentation for optimal distribution"""
        algorithm = work.get("algorithm", "SHA256")
        difficulty = work.get("target", 0x00000000FFFF0000000000000000000000000000000000000000000000000000)
        
        # Calculate optimal segment size based on worker performance
        worker_efficiency = self.worker_efficiency.get(worker_id, 1.0)
        base_segment_size = self._calculate_base_segment_size(algorithm, difficulty)
        
        # Adjust segment size based on worker efficiency
        adjusted_segment_size = int(base_segment_size * worker_efficiency)
        
        # Create work segments
        segments = []
        nonce_start = work.get("nonce_start", 0)
        nonce_end = work.get("nonce_end", 0xFFFFFFFF)
        
        current_nonce = nonce_start
        segment_id = 0
        
        while current_nonce < nonce_end:
            segment_end = min(current_nonce + adjusted_segment_size, nonce_end)
            
            segment_work = work.copy()
            segment_work.update({
                "nonce_start": current_nonce,
                "nonce_end": segment_end,
                "segment_id": f"{worker_id}_{segment_id}",
                "original_work_id": work.get("job_id", "unknown")
            })
            
            segments.append(segment_work)
            
            # Create and track work segment
            work_segment = WorkSegment(
                segment_work["segment_id"],
                segment_work,
                (current_nonce, segment_end)
            )
            work_segment.assigned_worker = worker_id
            self.active_segments[work_segment.segment_id] = work_segment
            
            current_nonce = segment_end + 1
            segment_id += 1
        
        logger.debug(f"Created {len(segments)} work segments for worker {worker_id}")
        return segments
    
    def _calculate_base_segment_size(self, algorithm: str, difficulty: int) -> int:
        """Calculate base segment size based on algorithm and difficulty"""
        # Base segment sizes for different algorithms
        base_sizes = {
            "SHA256": 1000000,
            "RandomX": 100000,
            "Ethash": 500000,
            "Scrypt": 200000,
            "Yescrypt": 150000,
            "Kawpow": 300000,
            "X11": 400000
        }
        
        base_size = base_sizes.get(algorithm, 500000)
        
        # Adjust based on difficulty
        difficulty_factor = min(2.0, max(0.1, difficulty / 0x00000000FFFF0000000000000000000000000000000000000000000000000000))
        
        return int(base_size * difficulty_factor)
    
    def record_rejection(self, result: Dict[str, Any], worker_id: str):
        """Record share rejection for AI learning"""
        rejection_data = {
            "timestamp": time.time(),
            "worker_id": worker_id,
            "algorithm": result.get("algorithm", ""),
            "hash": result.get("hash", ""),
            "nonce": result.get("nonce", 0),
            "reason": result.get("rejection_reason", "unknown")
        }
        
        self.rejection_history.append(rejection_data)
        
        # Update worker efficiency (penalty for rejection)
        current_efficiency = self.worker_efficiency.get(worker_id, 1.0)
        self.worker_efficiency[worker_id] = max(0.1, current_efficiency * 0.98)
        
        logger.debug(f"Recorded rejection from worker {worker_id}, new efficiency: {self.worker_efficiency[worker_id]:.3f}")
    
    def record_performance(self, metrics: Dict[str, Any]):
        """Record performance metrics for AI learning"""
        performance_point = PerformanceMetric(
            timestamp=time.time(),
            hashrate=metrics.get("hashrate", 0.0),
            rejection_rate=metrics.get("rejection_rate", 0.0),
            temperature=metrics.get("temperature", {}),
            power_usage=metrics.get("power_usage", 0.0),
            algorithm=metrics.get("algorithm", ""),
            pool=metrics.get("pool", ""),
            worker_id=metrics.get("worker_id", "")
        )
        
        self.performance_history.append(performance_point)
        
        # Update algorithm performance tracking
        if performance_point.algorithm:
            self.algorithm_performance[performance_point.algorithm].append(performance_point.hashrate)
        
        # Update pool performance tracking
        if performance_point.pool:
            pool_score = performance_point.hashrate * (1 - performance_point.rejection_rate)
            self.pool_performance[performance_point.pool].append(pool_score)
        
        # Update worker efficiency (reward for good performance)
        if performance_point.worker_id and performance_point.rejection_rate < 0.02:
            current_efficiency = self.worker_efficiency.get(performance_point.worker_id, 1.0)
            self.worker_efficiency[performance_point.worker_id] = min(2.0, current_efficiency * 1.01)
    
    async def get_recommendations(self, current_metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get AI-powered optimization recommendations"""
        if len(self.performance_history) < 10:
            return None
        
        recommendations = {}
        
        # Analyze recent performance trends
        recent_metrics = list(self.performance_history)[-10:]
        current_hashrate = current_metrics.get("hashrate", 0)
        recent_avg_hashrate = statistics.mean([m.hashrate for m in recent_metrics])
        
        # Check if performance is declining
        if current_hashrate < recent_avg_hashrate * 0.9:
            recommendations["performance_declining"] = True
            
            # Suggest pool switch if rejection rate is high
            if current_metrics.get("rejection_rate", 0) > 0.05:
                recommendations["switch_pool"] = await self._recommend_pool_switch(current_metrics)
            
            # Suggest algorithm switch if hashrate is consistently low
            if len([m for m in recent_metrics if m.hashrate < recent_avg_hashrate * 0.8]) > 5:
                recommendations["switch_algorithm"] = await self._recommend_algorithm_switch(current_metrics)
        
        # Worker redistribution recommendations
        redistribution = await self._recommend_worker_redistribution()
        if redistribution:
            recommendations["redistribute_workers"] = redistribution
        
        # Temperature-based recommendations
        max_temp = max(current_metrics.get("temperature", {}).values(), default=0)
        if max_temp > 85:
            recommendations["reduce_intensity"] = True
            recommendations["temperature_warning"] = max_temp
        
        return recommendations if recommendations else None
    
    async def _recommend_pool_switch(self, current_metrics: Dict[str, Any]) -> Optional[str]:
        """Recommend pool switch based on performance analysis"""
        current_algorithm = current_metrics.get("algorithm", "SHA256")
        current_pool = current_metrics.get("pool", "")
        
        # Find better performing pools for the same algorithm
        best_pool = None
        best_score = 0
        
        for pool_name, scores in self.pool_performance.items():
            if pool_name != current_pool and scores:
                avg_score = statistics.mean(scores[-5:])
                if avg_score > best_score:
                    best_score = avg_score
                    best_pool = pool_name
        
        return best_pool
    
    async def _recommend_algorithm_switch(self, current_metrics: Dict[str, Any]) -> Optional[str]:
        """Recommend algorithm switch based on performance analysis"""
        current_algorithm = current_metrics.get("algorithm", "")
        
        # Find better performing algorithms
        best_algorithm = None
        best_performance = 0
        
        for algorithm, performances in self.algorithm_performance.items():
            if algorithm != current_algorithm and performances:
                avg_performance = statistics.mean(performances[-5:])
                if avg_performance > best_performance:
                    best_performance = avg_performance
                    best_algorithm = algorithm
        
        return best_algorithm
    
    async def _recommend_worker_redistribution(self) -> Optional[Dict[str, Any]]:
        """Recommend worker redistribution based on efficiency analysis"""
        if not self.worker_efficiency:
            return None
        
        # Find underperforming workers
        avg_efficiency = statistics.mean(self.worker_efficiency.values())
        underperforming = {
            worker_id: efficiency 
            for worker_id, efficiency in self.worker_efficiency.items() 
            if efficiency < avg_efficiency * 0.8
        }
        
        if underperforming:
            return {
                "underperforming_workers": list(underperforming.keys()),
                "suggested_action": "reduce_workload",
                "efficiency_threshold": avg_efficiency * 0.8
            }
        
        return None
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics and insights"""
        stats = {
            "total_performance_points": len(self.performance_history),
            "total_rejections": len(self.rejection_history),
            "active_segments": len(self.active_segments),
            "completed_segments": len(self.completed_segments),
            "worker_efficiency": dict(self.worker_efficiency),
            "algorithm_performance": {
                alg: statistics.mean(perfs[-10:]) if perfs else 0
                for alg, perfs in self.algorithm_performance.items()
            },
            "pool_performance": {
                pool: statistics.mean(scores[-10:]) if scores else 0
                for pool, scores in self.pool_performance.items()
            }
        }
        
        return stats