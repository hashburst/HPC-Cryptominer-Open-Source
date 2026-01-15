"""
Node Agent
Manages a mining node in a distributed cluster
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional
import aiohttp
import psutil
from mining_engine import MiningEngine, HardwareManager

logger = logging.getLogger(__name__)

class NodeAgent:
    """Mining node agent for cluster participation"""
    
    def __init__(self, cluster_master_url: str, node_port: int = 8080, config: Dict[str, Any] = None):
        self.cluster_master_url = cluster_master_url.rstrip('/')
        self.node_port = node_port
        self.config = config or {}
        
        # Node identification
        self.node_id = str(uuid.uuid4())
        self.hostname = self._get_hostname()
        self.ip_address = self._get_ip_address()
        
        # Components
        self.hardware_manager = HardwareManager()
        self.mining_engine: Optional[MiningEngine] = None
        
        # State
        self.registered = False
        self.running = False
        self.last_heartbeat = 0
        self.heartbeat_interval = config.get("cluster", {}).get("heartbeat_interval", 30)
        
        # Tasks
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.status_task: Optional[asyncio.Task] = None
        
        logger.info(f"Node Agent initialized: {self.node_id}")
    
    def _get_hostname(self) -> str:
        """Get node hostname"""
        try:
            import socket
            return socket.gethostname()
        except Exception:
            return "unknown"
    
    def _get_ip_address(self) -> str:
        """Get node IP address"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    async def start(self):
        """Start the node agent"""
        if self.running:
            return
        
        logger.info("Starting Node Agent...")
        self.running = True
        
        # Initialize hardware
        await self.hardware_manager.initialize()
        
        # Register with cluster master
        await self._register_with_master()
        
        # Start background tasks
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.status_task = asyncio.create_task(self._status_update_loop())
        
        logger.info("Node Agent started successfully")
    
    async def stop(self):
        """Stop the node agent"""
        if not self.running:
            return
        
        logger.info("Stopping Node Agent...")
        self.running = False
        
        # Cancel tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.status_task:
            self.status_task.cancel()
        
        # Stop mining if active
        if self.mining_engine:
            await self.mining_engine.stop()
        
        # Unregister from cluster
        await self._unregister_from_master()
        
        logger.info("Node Agent stopped")
    
    def set_mining_engine(self, mining_engine: MiningEngine):
        """Set the mining engine instance"""
        self.mining_engine = mining_engine
    
    async def _register_with_master(self):
        """Register this node with the cluster master"""
        hardware_info = self.hardware_manager.get_hardware_info()
        
        registration_data = {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "port": self.node_port,
            "cpu_cores": hardware_info.get("cpu", {}).get("cores", 1),
            "cpu_threads": hardware_info.get("cpu", {}).get("threads", 1),
            "gpu_count": len(hardware_info.get("gpus", [])),
            "gpu_memory": sum(gpu.get("memory_total", 0) for gpu in hardware_info.get("gpus", [])),
            "total_memory": hardware_info.get("memory", {}).get("total", 0),
            "capabilities": self._get_node_capabilities(),
            "timestamp": time.time()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.cluster_master_url}/api/cluster/register"
                async with session.post(url, json=registration_data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.registered = True
                        logger.info(f"Successfully registered with cluster master: {result}")
                    else:
                        logger.error(f"Failed to register with cluster master: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error registering with cluster master: {e}")
    
    async def _unregister_from_master(self):
        """Unregister this node from the cluster master"""
        if not self.registered:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.cluster_master_url}/api/cluster/unregister"
                data = {"node_id": self.node_id}
                async with session.post(url, json=data, timeout=10) as response:
                    if response.status == 200:
                        logger.info("Successfully unregistered from cluster master")
                    else:
                        logger.warning(f"Failed to unregister from cluster master: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Error unregistering from cluster master: {e}")
    
    def _get_node_capabilities(self) -> Dict[str, Any]:
        """Get node capabilities and supported algorithms"""
        hardware_info = self.hardware_manager.get_hardware_info()
        
        capabilities = {
            "algorithms": ["SHA256", "RandomX", "Ethash", "Scrypt"],
            "cpu_mining": True,
            "gpu_mining": len(hardware_info.get("gpus", [])) > 0,
            "memory_intensive": hardware_info.get("memory", {}).get("total", 0) > 8 * 1024**3,  # 8GB+
            "high_performance": hardware_info.get("cpu", {}).get("cores", 0) >= 8
        }
        
        # Add GPU-specific capabilities
        gpus = hardware_info.get("gpus", [])
        if gpus:
            nvidia_gpus = [gpu for gpu in gpus if gpu.get("vendor") == "NVIDIA"]
            amd_gpus = [gpu for gpu in gpus if gpu.get("vendor") == "AMD"]
            
            if nvidia_gpus:
                capabilities["nvidia_compute"] = True
                capabilities["cuda_support"] = True
            
            if amd_gpus:
                capabilities["amd_compute"] = True
                capabilities["rocm_support"] = True
        
        return capabilities
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats to cluster master"""
        while self.running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(30)
    
    async def _send_heartbeat(self):
        """Send heartbeat to cluster master"""
        if not self.registered:
            return
        
        heartbeat_data = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "status": "active"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.cluster_master_url}/api/cluster/heartbeat"
                async with session.post(url, json=heartbeat_data, timeout=10) as response:
                    if response.status == 200:
                        self.last_heartbeat = time.time()
                    else:
                        logger.warning(f"Heartbeat failed: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Error sending heartbeat: {e}")
    
    async def _status_update_loop(self):
        """Send periodic status updates to cluster master"""
        while self.running:
            try:
                await self._send_status_update()
                await asyncio.sleep(60)  # Send status every minute
                
            except Exception as e:
                logger.error(f"Error in status update loop: {e}")
                await asyncio.sleep(60)
    
    async def _send_status_update(self):
        """Send detailed status update to cluster master"""
        if not self.registered:
            return
        
        # Get hardware metrics
        hardware_metrics = self.hardware_manager.get_metrics()
        
        # Get mining stats if available
        mining_stats = {}
        if self.mining_engine:
            stats = self.mining_engine.get_stats()
            mining_stats = {
                "hashrate": stats.hashrate,
                "accepted_shares": stats.accepted_shares,
                "rejected_shares": stats.rejected_shares,
                "algorithm": stats.algorithm,
                "uptime": stats.uptime
            }
        
        status_data = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "hardware_metrics": hardware_metrics,
            "mining_stats": mining_stats,
            "system_stats": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.cluster_master_url}/api/cluster/status"
                async with session.post(url, json=status_data, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"Status update failed: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Error sending status update: {e}")
    
    async def handle_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle command from cluster master"""
        logger.info(f"Received command: {command} with params: {params}")
        
        try:
            if command == "assign_work":
                return await self._handle_assign_work(params)
            
            elif command == "stop_mining":
                return await self._handle_stop_mining(params)
            
            elif command == "switch_algorithm":
                return await self._handle_switch_algorithm(params)
            
            elif command == "switch_pool":
                return await self._handle_switch_pool(params)
            
            elif command == "reduce_intensity":
                return await self._handle_reduce_intensity(params)
            
            elif command == "get_status":
                return await self._handle_get_status(params)
            
            else:
                return {"success": False, "error": f"Unknown command: {command}"}
                
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_assign_work(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle work assignment from cluster master"""
        algorithm = params.get("algorithm")
        pool = params.get("pool")
        work_segments = params.get("work_segments", [])
        
        if not self.mining_engine:
            return {"success": False, "error": "Mining engine not available"}
        
        # Configure mining engine for the assigned work
        # This is a simplified implementation
        logger.info(f"Assigned work: {algorithm} on {pool}")
        
        # Start mining if not already running
        if not self.mining_engine.is_running:
            await self.mining_engine.start()
        
        return {"success": True, "message": f"Work assigned: {algorithm} on {pool}"}
    
    async def _handle_stop_mining(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stop mining command"""
        if self.mining_engine and self.mining_engine.is_running:
            await self.mining_engine.stop()
            return {"success": True, "message": "Mining stopped"}
        
        return {"success": True, "message": "Mining was not running"}
    
    async def _handle_switch_algorithm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle algorithm switch command"""
        algorithm = params.get("algorithm")
        
        if not algorithm:
            return {"success": False, "error": "Algorithm not specified"}
        
        # This would require restarting mining with new algorithm
        logger.info(f"Switching to algorithm: {algorithm}")
        
        return {"success": True, "message": f"Switched to algorithm: {algorithm}"}
    
    async def _handle_switch_pool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pool switch command"""
        pool = params.get("pool")
        
        if not pool:
            return {"success": False, "error": "Pool not specified"}
        
        logger.info(f"Switching to pool: {pool}")
        
        return {"success": True, "message": f"Switched to pool: {pool}"}
    
    async def _handle_reduce_intensity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reduce intensity command"""
        intensity = params.get("intensity", 70)
        
        logger.info(f"Reducing mining intensity to: {intensity}%")
        
        return {"success": True, "message": f"Intensity reduced to {intensity}%"}
    
    async def _handle_get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get status command"""
        return {
            "success": True,
            "status": self.get_status()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive node status"""
        status = {
            "node_id": self.node_id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "port": self.node_port,
            "registered": self.registered,
            "running": self.running,
            "last_heartbeat": self.last_heartbeat,
            "hardware": self.hardware_manager.get_hardware_info(),
            "capabilities": self._get_node_capabilities(),
            "uptime": time.time(),
            "mining_active": self.mining_engine.is_running if self.mining_engine else False
        }
        
        if self.mining_engine:
            mining_stats = self.mining_engine.get_stats()
            status["mining_stats"] = {
                "hashrate": mining_stats.hashrate,
                "accepted_shares": mining_stats.accepted_shares,
                "rejected_shares": mining_stats.rejected_shares,
                "algorithm": mining_stats.algorithm,
                "uptime": mining_stats.uptime
            }
        
        return status