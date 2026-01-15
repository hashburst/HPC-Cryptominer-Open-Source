"""
Cluster Management System
Manages distributed mining clusters with intelligent orchestration
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import aiohttp
import psutil

logger = logging.getLogger(__name__)

@dataclass
class MiningNode:
    """Represents a mining node in the cluster"""
    node_id: str
    hostname: str
    ip_address: str
    port: int
    status: str = "inactive"  # inactive, active, mining, error
    last_seen: float = 0
    
    # Hardware specs
    cpu_cores: int = 0
    cpu_threads: int = 0
    gpu_count: int = 0
    gpu_memory: int = 0
    total_memory: int = 0
    
    # Performance metrics
    hashrate: float = 0.0
    temperature: Dict[str, float] = None
    power_usage: float = 0.0
    uptime: float = 0.0
    
    # Work assignment
    assigned_algorithm: str = ""
    assigned_pool: str = ""
    work_segments: List[str] = None
    
    def __post_init__(self):
        if self.temperature is None:
            self.temperature = {}
        if self.work_segments is None:
            self.work_segments = []

@dataclass
class ClusterStats:
    """Cluster-wide statistics"""
    total_nodes: int = 0
    active_nodes: int = 0
    total_hashrate: float = 0.0
    total_power: float = 0.0
    algorithms_running: Set[str] = None
    pools_connected: Set[str] = None
    efficiency_score: float = 0.0
    
    def __post_init__(self):
        if self.algorithms_running is None:
            self.algorithms_running = set()
        if self.pools_connected is None:
            self.pools_connected = set()

class ClusterManager:
    """Manages distributed mining clusters"""
    
    def __init__(self, cluster_id: str = None):
        self.cluster_id = cluster_id or str(uuid.uuid4())
        self.nodes: Dict[str, MiningNode] = {}
        self.cluster_stats = ClusterStats()
        
        # Configuration
        self.node_timeout = 300  # 5 minutes
        self.health_check_interval = 30  # 30 seconds
        self.rebalance_interval = 600  # 10 minutes
        
        # AI optimization
        self.optimization_history = []
        self.load_balancing_weights = defaultdict(float)
        
        # Tasks
        self.health_check_task: Optional[asyncio.Task] = None
        self.rebalance_task: Optional[asyncio.Task] = None
        self.running = False
        
        logger.info(f"Cluster Manager initialized with ID: {self.cluster_id}")
    
    async def start(self):
        """Start cluster management"""
        if self.running:
            return
        
        self.running = True
        
        # Start background tasks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.rebalance_task = asyncio.create_task(self._rebalance_loop())
        
        logger.info("Cluster Manager started")
    
    async def stop(self):
        """Stop cluster management"""
        self.running = False
        
        # Cancel tasks
        if self.health_check_task:
            self.health_check_task.cancel()
        if self.rebalance_task:
            self.rebalance_task.cancel()
        
        # Stop all nodes
        await self._stop_all_nodes()
        
        logger.info("Cluster Manager stopped")
    
    async def register_node(self, node_info: Dict[str, Any]) -> str:
        """Register a new mining node"""
        node_id = node_info.get("node_id") or str(uuid.uuid4())
        
        node = MiningNode(
            node_id=node_id,
            hostname=node_info.get("hostname", "unknown"),
            ip_address=node_info.get("ip_address", "127.0.0.1"),
            port=node_info.get("port", 8080),
            cpu_cores=node_info.get("cpu_cores", 1),
            cpu_threads=node_info.get("cpu_threads", 1),
            gpu_count=node_info.get("gpu_count", 0),
            gpu_memory=node_info.get("gpu_memory", 0),
            total_memory=node_info.get("total_memory", 0),
            last_seen=time.time(),
            status="active"
        )
        
        self.nodes[node_id] = node
        self._update_cluster_stats()
        
        logger.info(f"Registered node: {node_id} ({node.hostname})")
        
        # Trigger rebalancing
        await self._trigger_rebalancing()
        
        return node_id
    
    async def unregister_node(self, node_id: str):
        """Unregister a mining node"""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            
            # Stop node mining
            await self._stop_node_mining(node)
            
            # Remove from cluster
            del self.nodes[node_id]
            self._update_cluster_stats()
            
            logger.info(f"Unregistered node: {node_id}")
            
            # Redistribute work
            await self._redistribute_work(node_id)
    
    async def update_node_status(self, node_id: str, status_data: Dict[str, Any]):
        """Update node status and metrics"""
        if node_id not in self.nodes:
            logger.warning(f"Unknown node status update: {node_id}")
            return
        
        node = self.nodes[node_id]
        node.last_seen = time.time()
        node.hashrate = status_data.get("hashrate", 0.0)
        node.temperature = status_data.get("temperature", {})
        node.power_usage = status_data.get("power_usage", 0.0)
        node.uptime = status_data.get("uptime", 0.0)
        node.status = status_data.get("status", "active")
        
        # Update algorithm and pool if provided
        if "algorithm" in status_data:
            node.assigned_algorithm = status_data["algorithm"]
        if "pool" in status_data:
            node.assigned_pool = status_data["pool"]
        
        self._update_cluster_stats()
    
    async def assign_work(self, node_id: str, algorithm: str, pool: str, work_segments: List[str]) -> bool:
        """Assign work to a specific node"""
        if node_id not in self.nodes:
            return False
        
        node = self.nodes[node_id]
        
        try:
            # Send work assignment to node
            assignment = {
                "algorithm": algorithm,
                "pool": pool,
                "work_segments": work_segments,
                "timestamp": time.time()
            }
            
            success = await self._send_node_command(node, "assign_work", assignment)
            
            if success:
                node.assigned_algorithm = algorithm
                node.assigned_pool = pool
                node.work_segments = work_segments
                node.status = "mining"
                
                logger.info(f"Assigned work to node {node_id}: {algorithm} on {pool}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error assigning work to node {node_id}: {e}")
            return False
    
    async def _health_check_loop(self):
        """Periodic health check of all nodes"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check each node
                nodes_to_remove = []
                for node_id, node in self.nodes.items():
                    # Check if node is responsive
                    if current_time - node.last_seen > self.node_timeout:
                        logger.warning(f"Node {node_id} is unresponsive")
                        node.status = "error"
                        nodes_to_remove.append(node_id)
                    else:
                        # Ping node for health check
                        await self._ping_node(node)
                
                # Remove unresponsive nodes
                for node_id in nodes_to_remove:
                    await self.unregister_node(node_id)
                
                # Update cluster stats
                self._update_cluster_stats()
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(30)
    
    async def _rebalance_loop(self):
        """Periodic load balancing and optimization"""
        while self.running:
            try:
                await asyncio.sleep(self.rebalance_interval)
                
                if len(self.nodes) < 2:
                    continue
                
                logger.info("Running cluster rebalancing...")
                
                # Analyze current performance
                performance_analysis = await self._analyze_cluster_performance()
                
                # Generate optimization recommendations
                recommendations = await self._generate_optimization_recommendations(performance_analysis)
                
                # Apply optimizations
                if recommendations:
                    await self._apply_optimizations(recommendations)
                
            except Exception as e:
                logger.error(f"Error in rebalance loop: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_cluster_performance(self) -> Dict[str, Any]:
        """Analyze cluster performance for optimization"""
        analysis = {
            "total_hashrate": 0.0,
            "algorithm_distribution": defaultdict(list),
            "pool_distribution": defaultdict(list),
            "hardware_utilization": {},
            "efficiency_metrics": {},
            "bottlenecks": []
        }
        
        for node_id, node in self.nodes.items():
            if node.status == "mining":
                analysis["total_hashrate"] += node.hashrate
                
                # Algorithm distribution
                if node.assigned_algorithm:
                    analysis["algorithm_distribution"][node.assigned_algorithm].append({
                        "node_id": node_id,
                        "hashrate": node.hashrate,
                        "hardware_score": self._calculate_hardware_score(node)
                    })
                
                # Pool distribution
                if node.assigned_pool:
                    analysis["pool_distribution"][node.assigned_pool].append(node_id)
                
                # Hardware utilization
                cpu_utilization = (node.hashrate / max(1, node.cpu_threads)) if node.cpu_threads > 0 else 0
                analysis["hardware_utilization"][node_id] = {
                    "cpu_efficiency": cpu_utilization,
                    "gpu_count": node.gpu_count,
                    "temperature_max": max(node.temperature.values()) if node.temperature else 0,
                    "power_efficiency": node.hashrate / max(1, node.power_usage) if node.power_usage > 0 else 0
                }
                
                # Identify bottlenecks
                if max(node.temperature.values(), default=0) > 85:
                    analysis["bottlenecks"].append(f"High temperature on node {node_id}")
                
                if node.hashrate < self._expected_hashrate(node) * 0.7:
                    analysis["bottlenecks"].append(f"Low performance on node {node_id}")
        
        return analysis
    
    def _calculate_hardware_score(self, node: MiningNode) -> float:
        """Calculate hardware performance score for a node"""
        cpu_score = node.cpu_cores * 10 + node.cpu_threads * 5
        gpu_score = node.gpu_count * 50 + (node.gpu_memory / (1024**3)) * 20
        memory_score = (node.total_memory / (1024**3)) * 2
        
        return cpu_score + gpu_score + memory_score
    
    def _expected_hashrate(self, node: MiningNode) -> float:
        """Calculate expected hashrate for a node based on hardware"""
        hardware_score = self._calculate_hardware_score(node)
        
        # Algorithm-specific multipliers
        algorithm_multipliers = {
            "SHA256": 1.0,
            "RandomX": 0.8,
            "Ethash": 1.2,
            "Scrypt": 0.6
        }
        
        multiplier = algorithm_multipliers.get(node.assigned_algorithm, 1.0)
        return hardware_score * multiplier * 1000  # Base hashrate estimation
    
    async def _generate_optimization_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered optimization recommendations"""
        recommendations = []
        
        # Check algorithm distribution
        for algorithm, nodes in analysis["algorithm_distribution"].items():
            if len(nodes) > 0:
                avg_hashrate = sum(n["hashrate"] for n in nodes) / len(nodes)
                
                # Find underperforming nodes
                underperforming = [n for n in nodes if n["hashrate"] < avg_hashrate * 0.7]
                
                if underperforming:
                    recommendations.append({
                        "type": "algorithm_switch",
                        "nodes": [n["node_id"] for n in underperforming],
                        "current_algorithm": algorithm,
                        "reason": "Low performance detected",
                        "priority": "medium"
                    })
        
        # Check pool distribution for load balancing
        pool_loads = {pool: len(nodes) for pool, nodes in analysis["pool_distribution"].items()}
        if pool_loads:
            max_load = max(pool_loads.values())
            min_load = min(pool_loads.values())
            
            if max_load > min_load * 2:  # Imbalanced load
                overloaded_pool = max(pool_loads, key=pool_loads.get)
                underloaded_pool = min(pool_loads, key=pool_loads.get)
                
                recommendations.append({
                    "type": "pool_rebalance",
                    "from_pool": overloaded_pool,
                    "to_pool": underloaded_pool,
                    "nodes_to_move": 1,
                    "reason": "Load balancing",
                    "priority": "low"
                })
        
        # Check for temperature issues
        for bottleneck in analysis["bottlenecks"]:
            if "High temperature" in bottleneck:
                node_id = bottleneck.split()[-1]
                recommendations.append({
                    "type": "reduce_intensity",
                    "nodes": [node_id],
                    "reason": "Temperature control",
                    "priority": "high"
                })
        
        return recommendations
    
    async def _apply_optimizations(self, recommendations: List[Dict[str, Any]]):
        """Apply optimization recommendations"""
        for rec in recommendations:
            try:
                if rec["type"] == "algorithm_switch":
                    await self._switch_node_algorithms(rec["nodes"])
                
                elif rec["type"] == "pool_rebalance":
                    await self._rebalance_pools(rec["from_pool"], rec["to_pool"], rec["nodes_to_move"])
                
                elif rec["type"] == "reduce_intensity":
                    await self._reduce_node_intensity(rec["nodes"])
                
                logger.info(f"Applied optimization: {rec['type']} - {rec['reason']}")
                
            except Exception as e:
                logger.error(f"Error applying optimization {rec['type']}: {e}")
    
    async def _switch_node_algorithms(self, node_ids: List[str]):
        """Switch algorithms for underperforming nodes"""
        # Simple implementation - switch to best performing algorithm
        best_algorithm = "RandomX"  # Default fallback
        
        for node_id in node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                
                # Find best algorithm for this node's hardware
                if node.gpu_count > 0:
                    best_algorithm = "Ethash"
                elif node.cpu_threads >= 8:
                    best_algorithm = "RandomX"
                else:
                    best_algorithm = "SHA256"
                
                await self._send_node_command(node, "switch_algorithm", {"algorithm": best_algorithm})
    
    async def _rebalance_pools(self, from_pool: str, to_pool: str, count: int):
        """Rebalance nodes between pools"""
        # Find nodes on the overloaded pool
        candidates = [
            node for node in self.nodes.values()
            if node.assigned_pool == from_pool and node.status == "mining"
        ]
        
        # Move lowest performing nodes
        candidates.sort(key=lambda n: n.hashrate)
        nodes_to_move = candidates[:count]
        
        for node in nodes_to_move:
            await self._send_node_command(node, "switch_pool", {"pool": to_pool})
    
    async def _reduce_node_intensity(self, node_ids: List[str]):
        """Reduce mining intensity for overheating nodes"""
        for node_id in node_ids:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                await self._send_node_command(node, "reduce_intensity", {"intensity": 70})
    
    async def _send_node_command(self, node: MiningNode, command: str, params: Dict[str, Any]) -> bool:
        """Send command to a mining node"""
        try:
            url = f"http://{node.ip_address}:{node.port}/api/command"
            
            payload = {
                "command": command,
                "params": params,
                "cluster_id": self.cluster_id,
                "timestamp": time.time()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("success", False)
                    else:
                        logger.warning(f"Node {node.node_id} returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending command to node {node.node_id}: {e}")
            return False
    
    async def _ping_node(self, node: MiningNode):
        """Ping node for health check"""
        try:
            url = f"http://{node.ip_address}:{node.port}/api/ping"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        node.last_seen = time.time()
                        
                        # Update node metrics if provided
                        if "metrics" in data:
                            await self.update_node_status(node.node_id, data["metrics"])
                        
        except Exception as e:
            logger.debug(f"Ping failed for node {node.node_id}: {e}")
    
    async def _stop_node_mining(self, node: MiningNode):
        """Stop mining on a specific node"""
        await self._send_node_command(node, "stop_mining", {})
        node.status = "inactive"
        node.assigned_algorithm = ""
        node.assigned_pool = ""
        node.work_segments.clear()
    
    async def _stop_all_nodes(self):
        """Stop mining on all nodes"""
        for node in self.nodes.values():
            await self._stop_node_mining(node)
    
    async def _redistribute_work(self, removed_node_id: str):
        """Redistribute work after node removal"""
        # This would typically involve reassigning work segments
        # that were assigned to the removed node
        logger.info(f"Redistributing work after node {removed_node_id} removal")
        await self._trigger_rebalancing()
    
    async def _trigger_rebalancing(self):
        """Trigger immediate rebalancing"""
        if self.rebalance_task and not self.rebalance_task.done():
            # Create a new task for immediate rebalancing
            asyncio.create_task(self._perform_immediate_rebalancing())
    
    async def _perform_immediate_rebalancing(self):
        """Perform immediate rebalancing"""
        try:
            performance_analysis = await self._analyze_cluster_performance()
            recommendations = await self._generate_optimization_recommendations(performance_analysis)
            
            if recommendations:
                await self._apply_optimizations(recommendations)
                
        except Exception as e:
            logger.error(f"Error in immediate rebalancing: {e}")
    
    def _update_cluster_stats(self):
        """Update cluster-wide statistics"""
        active_nodes = [n for n in self.nodes.values() if n.status in ["active", "mining"]]
        mining_nodes = [n for n in self.nodes.values() if n.status == "mining"]
        
        self.cluster_stats = ClusterStats(
            total_nodes=len(self.nodes),
            active_nodes=len(active_nodes),
            total_hashrate=sum(n.hashrate for n in mining_nodes),
            total_power=sum(n.power_usage for n in mining_nodes),
            algorithms_running=set(n.assigned_algorithm for n in mining_nodes if n.assigned_algorithm),
            pools_connected=set(n.assigned_pool for n in mining_nodes if n.assigned_pool),
            efficiency_score=self._calculate_cluster_efficiency()
        )
    
    def _calculate_cluster_efficiency(self) -> float:
        """Calculate overall cluster efficiency score"""
        if not self.nodes:
            return 0.0
        
        mining_nodes = [n for n in self.nodes.values() if n.status == "mining"]
        if not mining_nodes:
            return 0.0
        
        total_expected = sum(self._expected_hashrate(n) for n in mining_nodes)
        total_actual = sum(n.hashrate for n in mining_nodes)
        
        return (total_actual / max(1, total_expected)) * 100
    
    def get_cluster_status(self) -> Dict[str, Any]:
        """Get comprehensive cluster status"""
        return {
            "cluster_id": self.cluster_id,
            "stats": asdict(self.cluster_stats),
            "nodes": {
                node_id: asdict(node)
                for node_id, node in self.nodes.items()
            },
            "optimization_history": self.optimization_history[-10:],  # Last 10 optimizations
            "timestamp": time.time()
        }
    
    async def get_optimal_node_assignment(self, algorithm: str) -> Optional[str]:
        """Get optimal node for a specific algorithm"""
        available_nodes = [
            n for n in self.nodes.values()
            if n.status == "active" or (n.status == "mining" and n.assigned_algorithm == algorithm)
        ]
        
        if not available_nodes:
            return None
        
        # Score nodes based on hardware suitability for algorithm
        best_node = None
        best_score = 0
        
        for node in available_nodes:
            score = self._calculate_algorithm_suitability(node, algorithm)
            
            if score > best_score:
                best_score = score
                best_node = node
        
        return best_node.node_id if best_node else None
    
    def _calculate_algorithm_suitability(self, node: MiningNode, algorithm: str) -> float:
        """Calculate how suitable a node is for a specific algorithm"""
        base_score = self._calculate_hardware_score(node)
        
        # Algorithm-specific adjustments
        if algorithm == "RandomX":
            # Favors CPU and memory
            cpu_bonus = node.cpu_threads * 5
            memory_bonus = (node.total_memory / (1024**3)) * 10
            return base_score + cpu_bonus + memory_bonus
        
        elif algorithm == "Ethash":
            # Favors GPU memory
            gpu_bonus = node.gpu_count * 30 + (node.gpu_memory / (1024**3)) * 20
            return base_score + gpu_bonus
        
        elif algorithm == "SHA256":
            # Can use both CPU and GPU
            return base_score
        
        else:
            return base_score