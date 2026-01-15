"""
Performance Monitor
Collects and exposes mining performance metrics
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import psutil

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self, mining_engine=None, cluster_manager=None, port: int = 8082):
        self.mining_engine = mining_engine
        self.cluster_manager = cluster_manager
        self.port = port
        self.running = False
        
        # Prometheus metrics
        self._setup_metrics()
        
        # Monitoring tasks
        self.metrics_task: Optional[asyncio.Task] = None
        self.system_task: Optional[asyncio.Task] = None
        
        logger.info(f"Performance Monitor initialized on port {port}")
    
    def _setup_metrics(self):
        """Setup Prometheus metrics"""
        # Mining metrics
        self.hashrate_gauge = Gauge('mining_hashrate_hash_per_second', 'Current mining hashrate')
        self.accepted_shares_counter = Counter('mining_accepted_shares_total', 'Total accepted shares')
        self.rejected_shares_counter = Counter('mining_rejected_shares_total', 'Total rejected shares')
        self.active_workers_gauge = Gauge('mining_active_workers', 'Number of active mining workers')
        
        # Hardware metrics
        self.cpu_usage_gauge = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage_gauge = Gauge('system_memory_usage_percent', 'Memory usage percentage')
        self.temperature_gauge = Gauge('hardware_temperature_celsius', 'Hardware temperature', ['component'])
        self.power_gauge = Gauge('hardware_power_watts', 'Power consumption in watts')
        
        # Cluster metrics (if applicable)
        self.cluster_nodes_gauge = Gauge('cluster_total_nodes', 'Total nodes in cluster')
        self.cluster_active_nodes_gauge = Gauge('cluster_active_nodes', 'Active nodes in cluster')
        self.cluster_hashrate_gauge = Gauge('cluster_total_hashrate_hash_per_second', 'Cluster total hashrate')
        
        # Performance metrics
        self.mining_uptime_gauge = Gauge('mining_uptime_seconds', 'Mining uptime in seconds')
        self.efficiency_gauge = Gauge('mining_efficiency_percent', 'Mining efficiency percentage')
        
        # AI optimization metrics
        self.optimization_events_counter = Counter('ai_optimization_events_total', 'Total AI optimization events')
        self.pool_switches_counter = Counter('pool_switches_total', 'Total pool switches')
        self.algorithm_switches_counter = Counter('algorithm_switches_total', 'Total algorithm switches')
    
    async def start(self):
        """Start performance monitoring"""
        if self.running:
            return
        
        logger.info("Starting Performance Monitor...")
        self.running = True
        
        # Start Prometheus HTTP server
        start_http_server(self.port)
        logger.info(f"Prometheus metrics server started on port {self.port}")
        
        # Start monitoring tasks
        self.metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self.system_task = asyncio.create_task(self._system_monitoring_loop())
        
        logger.info("Performance Monitor started successfully")
    
    async def stop(self):
        """Stop performance monitoring"""
        if not self.running:
            return
        
        logger.info("Stopping Performance Monitor...")
        self.running = False
        
        # Cancel tasks
        if self.metrics_task:
            self.metrics_task.cancel()
        if self.system_task:
            self.system_task.cancel()
        
        logger.info("Performance Monitor stopped")
    
    async def _metrics_collection_loop(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                # Collect mining metrics
                if self.mining_engine:
                    await self._collect_mining_metrics()
                
                # Collect cluster metrics
                if self.cluster_manager:
                    await self._collect_cluster_metrics()
                
                # Collect AI optimization metrics
                await self._collect_optimization_metrics()
                
                await asyncio.sleep(5)  # Collect metrics every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(30)
    
    async def _system_monitoring_loop(self):
        """System monitoring loop"""
        while self.running:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect hardware metrics
                await self._collect_hardware_metrics()
                
                await asyncio.sleep(10)  # Collect system metrics every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_mining_metrics(self):
        """Collect mining-specific metrics"""
        try:
            stats = self.mining_engine.get_stats()
            
            # Update Prometheus metrics
            self.hashrate_gauge.set(stats.hashrate)
            self.accepted_shares_counter._value._value = stats.accepted_shares
            self.rejected_shares_counter._value._value = stats.rejected_shares
            self.active_workers_gauge.set(stats.workers_active)
            self.mining_uptime_gauge.set(stats.uptime)
            
            # Calculate efficiency
            total_shares = stats.accepted_shares + stats.rejected_shares
            if total_shares > 0:
                efficiency = (stats.accepted_shares / total_shares) * 100
                self.efficiency_gauge.set(efficiency)
            
            # Log metrics periodically
            if int(time.time()) % 60 == 0:  # Every minute
                logger.info(
                    f"Mining Metrics - Hashrate: {stats.hashrate:.2f} H/s, "
                    f"Shares: {stats.accepted_shares}/{stats.rejected_shares}, "
                    f"Workers: {stats.workers_active}, "
                    f"Uptime: {stats.uptime:.1f}s"
                )
                
        except Exception as e:
            logger.error(f"Error collecting mining metrics: {e}")
    
    async def _collect_cluster_metrics(self):
        """Collect cluster-specific metrics"""
        try:
            cluster_status = self.cluster_manager.get_cluster_status()
            stats = cluster_status.get("stats", {})
            
            # Update cluster metrics
            self.cluster_nodes_gauge.set(stats.get("total_nodes", 0))
            self.cluster_active_nodes_gauge.set(stats.get("active_nodes", 0))
            self.cluster_hashrate_gauge.set(stats.get("total_hashrate", 0))
            
            # Log cluster metrics periodically
            if int(time.time()) % 120 == 0:  # Every 2 minutes
                logger.info(
                    f"Cluster Metrics - Nodes: {stats.get('active_nodes', 0)}/{stats.get('total_nodes', 0)}, "
                    f"Total Hashrate: {stats.get('total_hashrate', 0):.2f} H/s, "
                    f"Efficiency: {stats.get('efficiency_score', 0):.1f}%"
                )
                
        except Exception as e:
            logger.error(f"Error collecting cluster metrics: {e}")
    
    async def _collect_optimization_metrics(self):
        """Collect AI optimization metrics"""
        try:
            # This would track optimization events from the AI optimizer
            # For now, this is a placeholder
            pass
            
        except Exception as e:
            logger.error(f"Error collecting optimization metrics: {e}")
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.cpu_usage_gauge.set(cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.memory_usage_gauge.set(memory.percent)
            
            # Disk metrics (if needed)
            disk = psutil.disk_usage('/')
            
            logger.debug(f"System Metrics - CPU: {cpu_percent}%, Memory: {memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_hardware_metrics(self):
        """Collect hardware-specific metrics"""
        try:
            # Temperature metrics
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                for sensor_name, sensor_list in temps.items():
                    for sensor in sensor_list:
                        self.temperature_gauge.labels(component=f"{sensor_name}_{sensor.label}").set(sensor.current)
            
            # Power metrics (if available)
            # This would require specific hardware monitoring tools
            
        except Exception as e:
            logger.debug(f"Hardware metrics collection skipped: {e}")
    
    def record_optimization_event(self, event_type: str, details: Dict[str, Any]):
        """Record an AI optimization event"""
        self.optimization_events_counter.inc()
        
        if event_type == "pool_switch":
            self.pool_switches_counter.inc()
        elif event_type == "algorithm_switch":
            self.algorithm_switches_counter.inc()
        
        logger.info(f"Optimization event recorded: {event_type} - {details}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        metrics = {
            "timestamp": time.time(),
            "mining": {},
            "system": {},
            "cluster": {}
        }
        
        # Mining metrics
        if self.mining_engine:
            stats = self.mining_engine.get_stats()
            metrics["mining"] = {
                "hashrate": stats.hashrate,
                "accepted_shares": stats.accepted_shares,
                "rejected_shares": stats.rejected_shares,
                "active_workers": stats.workers_active,
                "uptime": stats.uptime,
                "algorithm": stats.algorithm
            }
        
        # System metrics
        try:
            metrics["system"] = {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            logger.warning(f"Could not get system metrics: {e}")
        
        # Cluster metrics
        if self.cluster_manager:
            cluster_status = self.cluster_manager.get_cluster_status()
            metrics["cluster"] = cluster_status.get("stats", {})
        
        return metrics
    
    def get_metrics_summary(self) -> str:
        """Get formatted metrics summary"""
        metrics = self.get_current_metrics()
        
        summary_lines = [
            "=== HPC Miner Performance Summary ===",
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metrics['timestamp']))}"
        ]
        
        # Mining summary
        mining = metrics.get("mining", {})
        if mining:
            efficiency = 0
            total_shares = mining.get("accepted_shares", 0) + mining.get("rejected_shares", 0)
            if total_shares > 0:
                efficiency = (mining.get("accepted_shares", 0) / total_shares) * 100
            
            summary_lines.extend([
                "",
                "Mining Performance:",
                f"  Hashrate: {mining.get('hashrate', 0):.2f} H/s",
                f"  Algorithm: {mining.get('algorithm', 'N/A')}",
                f"  Accepted Shares: {mining.get('accepted_shares', 0)}",
                f"  Rejected Shares: {mining.get('rejected_shares', 0)}",
                f"  Efficiency: {efficiency:.2f}%",
                f"  Active Workers: {mining.get('active_workers', 0)}",
                f"  Uptime: {mining.get('uptime', 0):.1f}s"
            ])
        
        # System summary
        system = metrics.get("system", {})
        if system:
            summary_lines.extend([
                "",
                "System Performance:",
                f"  CPU Usage: {system.get('cpu_usage', 0):.1f}%",
                f"  Memory Usage: {system.get('memory_usage', 0):.1f}%",
                f"  Load Average: {system.get('load_average', [0, 0, 0])}"
            ])
        
        # Cluster summary
        cluster = metrics.get("cluster", {})
        if cluster:
            summary_lines.extend([
                "",
                "Cluster Performance:",
                f"  Active Nodes: {cluster.get('active_nodes', 0)}/{cluster.get('total_nodes', 0)}",
                f"  Total Hashrate: {cluster.get('total_hashrate', 0):.2f} H/s",
                f"  Efficiency Score: {cluster.get('efficiency_score', 0):.1f}%"
            ])
        
        summary_lines.append("=" * 37)
        
        return "\n".join(summary_lines)