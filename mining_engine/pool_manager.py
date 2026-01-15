"""
Pool Management System
Handles communication with mining pools and work distribution
"""

import json
import socket as socket_module
import struct
import threading
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
import aiohttp
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class PoolConnection:
    """Represents a connection to a mining pool"""
    name: str
    url: str
    port: int
    username: str
    password: str = "x"
    connected: bool = False
    socket: Optional[socket_module.socket] = None
    last_work: Optional[Dict[str, Any]] = None
    last_ping: float = 0
    share_count: int = 0
    difficulty: float = 1.0

@dataclass
class WorkUnit:
    """Represents a unit of work from a pool"""
    job_id: str
    algorithm: str
    data: str
    target: str
    height: int
    timestamp: float
    pool_name: str
    difficulty: float = 1.0

class PoolManager:
    """Manages connections to multiple mining pools"""
    
    def __init__(self):
        self.pools: Dict[str, PoolConnection] = {}
        self.active_work: Dict[str, WorkUnit] = {}
        self.connection_threads: Dict[str, threading.Thread] = {}
        self.running = False
        
        # Statistics
        self.shares_submitted = 0
        self.shares_accepted = 0
        self.shares_rejected = 0
        
        logger.info("Pool Manager initialized")
    
    async def add_pool(self, name: str, url: str, username: str, password: str = "x"):
        """Add a mining pool configuration"""
        try:
            # Parse pool URL
            if "://" in url:
                protocol, address = url.split("://", 1)
            else:
                protocol = "stratum+tcp"
                address = url
            
            if ":" in address:
                host, port_str = address.rsplit(":", 1)
                port = int(port_str)
            else:
                host = address
                port = 4444  # Default port
            
            pool = PoolConnection(
                name=name,
                url=host,
                port=port,
                username=username,
                password=password
            )
            
            self.pools[name] = pool
            logger.info(f"Added pool: {name} ({host}:{port})")
            
        except Exception as e:
            logger.error(f"Error adding pool {name}: {e}")
    
    async def connect_to_pool(self, pool_name: str) -> bool:
        """Connect to a specific mining pool"""
        if pool_name not in self.pools:
            logger.error(f"Pool {pool_name} not configured")
            return False
        
        pool = self.pools[pool_name]
        
        try:
            # Create socket connection
            sock = socket_module.socket(socket_module.AF_INET, socket_module.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((pool.url, pool.port))
            
            pool.socket = sock
            pool.connected = True
            
            # Start connection thread
            thread = threading.Thread(
                target=self._pool_connection_handler,
                args=(pool,),
                daemon=True
            )
            thread.start()
            self.connection_threads[pool_name] = thread
            
            # Send subscription request
            await self._send_subscribe(pool)
            
            logger.info(f"Connected to pool: {pool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to pool {pool_name}: {e}")
            pool.connected = False
            return False
    
    def _pool_connection_handler(self, pool: PoolConnection):
        """Handle pool connection in separate thread"""
        buffer = b""
        
        while self.running and pool.connected:
            try:
                # Receive data
                data = pool.socket.recv(4096)
                if not data:
                    break
                
                buffer += data
                
                # Process complete messages
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if line.strip():
                        self._process_pool_message(pool, line.decode('utf-8'))
                
            except socket_module.timeout:
                # Send periodic ping
                if time.time() - pool.last_ping > 60:
                    self._send_ping(pool)
                    pool.last_ping = time.time()
                continue
            except Exception as e:
                logger.error(f"Error in pool connection {pool.name}: {e}")
                break
        
        # Cleanup
        pool.connected = False
        if pool.socket:
            pool.socket.close()
            pool.socket = None
        
        logger.info(f"Disconnected from pool: {pool.name}")
    
    def _process_pool_message(self, pool: PoolConnection, message: str):
        """Process message from mining pool"""
        try:
            data = json.loads(message)
            
            # Handle different message types
            if "method" in data:
                method = data["method"]
                
                if method == "mining.notify":
                    self._handle_mining_notify(pool, data["params"])
                elif method == "mining.set_difficulty":
                    self._handle_set_difficulty(pool, data["params"])
                elif method == "mining.set_target":
                    self._handle_set_target(pool, data["params"])
                
            elif "result" in data:
                self._handle_pool_response(pool, data)
            
            elif "error" in data:
                logger.error(f"Pool {pool.name} error: {data['error']}")
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from pool {pool.name}: {message}")
        except Exception as e:
            logger.error(f"Error processing pool message: {e}")
    
    def _handle_mining_notify(self, pool: PoolConnection, params: List[Any]):
        """Handle mining.notify message (new work)"""
        try:
            if len(params) >= 7:
                job_id = params[0]
                prevhash = params[1]
                coinb1 = params[2]
                coinb2 = params[3]
                merkle_branch = params[4]
                version = params[5]
                nbits = params[6]
                ntime = params[7] if len(params) > 7 else hex(int(time.time()))[2:]
                clean_jobs = params[8] if len(params) > 8 else True
                
                # Create work unit
                work = WorkUnit(
                    job_id=job_id,
                    algorithm="SHA256",  # Default, could be detected
                    data=f"{version}{prevhash}{coinb1}{coinb2}{ntime}{nbits}",
                    target=self._difficulty_to_target(pool.difficulty),
                    height=0,  # Would be extracted from coinbase
                    timestamp=time.time(),
                    pool_name=pool.name,
                    difficulty=pool.difficulty
                )
                
                self.active_work[f"{pool.name}:{job_id}"] = work
                pool.last_work = work.__dict__
                
                logger.debug(f"New work from {pool.name}: {job_id}")
                
        except Exception as e:
            logger.error(f"Error handling mining.notify: {e}")
    
    def _handle_set_difficulty(self, pool: PoolConnection, params: List[Any]):
        """Handle mining.set_difficulty message"""
        if params:
            pool.difficulty = float(params[0])
            logger.info(f"Pool {pool.name} set difficulty: {pool.difficulty}")
    
    def _handle_set_target(self, pool: PoolConnection, params: List[Any]):
        """Handle mining.set_target message"""
        if params:
            logger.info(f"Pool {pool.name} set target: {params[0]}")
    
    def _handle_pool_response(self, pool: PoolConnection, response: Dict[str, Any]):
        """Handle pool response to submitted work"""
        if "id" in response:
            if response.get("result"):
                self.shares_accepted += 1
                logger.info(f"Share accepted by {pool.name}")
            else:
                self.shares_rejected += 1
                error = response.get("error", "Unknown error")
                logger.warning(f"Share rejected by {pool.name}: {error}")
    
    async def _send_subscribe(self, pool: PoolConnection):
        """Send mining.subscribe to pool"""
        message = {
            "id": 1,
            "method": "mining.subscribe",
            "params": ["HpcMiner/1.0", None]
        }
        self._send_json_message(pool, message)
        
        # Send authorization
        auth_message = {
            "id": 2,
            "method": "mining.authorize",
            "params": [pool.username, pool.password]
        }
        self._send_json_message(pool, auth_message)
    
    def _send_ping(self, pool: PoolConnection):
        """Send ping to keep connection alive"""
        message = {
            "id": int(time.time()),
            "method": "mining.ping",
            "params": []
        }
        self._send_json_message(pool, message)
    
    def _send_json_message(self, pool: PoolConnection, message: Dict[str, Any]):
        """Send JSON message to pool"""
        try:
            if pool.socket and pool.connected:
                json_str = json.dumps(message) + "\n"
                pool.socket.send(json_str.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending message to pool {pool.name}: {e}")
            pool.connected = False
    
    def _difficulty_to_target(self, difficulty: float) -> str:
        """Convert difficulty to target string"""
        # Bitcoin difficulty 1 target
        diff1_target = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
        target = int(diff1_target / difficulty)
        return hex(target)[2:].zfill(64)
    
    def get_work(self, pool_url: str) -> Optional[Dict[str, Any]]:
        """Get work from specified pool"""
        # Find pool by URL
        target_pool = None
        for pool in self.pools.values():
            if pool.url in pool_url or pool.name in pool_url:
                target_pool = pool
                break
        
        if not target_pool or not target_pool.connected:
            return None
        
        # Return latest work
        if target_pool.last_work:
            work = target_pool.last_work.copy()
            work.update({
                "nonce_start": 0,
                "nonce_end": 0xFFFFFFFF,
                "target": int(work.get("target", "0"), 16) if isinstance(work.get("target"), str) else work.get("target", 0)
            })
            return work
        
        return None
    
    def submit_share(self, pool_url: str, result: Dict[str, Any]) -> bool:
        """Submit mining result to pool"""
        # Find pool
        target_pool = None
        for pool in self.pools.values():
            if pool.url in pool_url or pool.name in pool_url:
                target_pool = pool
                break
        
        if not target_pool or not target_pool.connected:
            return False
        
        try:
            # Format share submission
            message = {
                "id": int(time.time()),
                "method": "mining.submit",
                "params": [
                    target_pool.username,
                    result.get("job_id", ""),
                    result.get("extranonce2", "00000000"),
                    result.get("ntime", hex(int(time.time()))[2:]),
                    result.get("nonce", "00000000")
                ]
            }
            
            self._send_json_message(target_pool, message)
            self.shares_submitted += 1
            target_pool.share_count += 1
            
            logger.debug(f"Submitted share to {target_pool.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting share: {e}")
            return False
    
    async def start(self):
        """Start pool manager"""
        self.running = True
        
        # Connect to all configured pools
        for pool_name in self.pools.keys():
            await self.connect_to_pool(pool_name)
        
        logger.info("Pool Manager started")
    
    async def stop(self):
        """Stop pool manager"""
        self.running = False
        
        # Close all connections
        for pool in self.pools.values():
            if pool.socket:
                pool.socket.close()
                pool.connected = False
        
        # Wait for threads to finish
        for thread in self.connection_threads.values():
            thread.join(timeout=5)
        
        logger.info("Pool Manager stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            "pools_connected": len([p for p in self.pools.values() if p.connected]),
            "total_pools": len(self.pools),
            "shares_submitted": self.shares_submitted,
            "shares_accepted": self.shares_accepted,
            "shares_rejected": self.shares_rejected,
            "acceptance_rate": self.shares_accepted / max(1, self.shares_submitted),
            "pool_details": {
                name: {
                    "connected": pool.connected,
                    "difficulty": pool.difficulty,
                    "shares": pool.share_count,
                    "url": f"{pool.url}:{pool.port}"
                }
                for name, pool in self.pools.items()
            }
        }