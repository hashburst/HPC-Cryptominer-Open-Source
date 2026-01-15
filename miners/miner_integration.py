#!/usr/bin/env python3
"""
Real Miner Integration for HPC Cryptominer
Integrates with actual mining binaries like lolMiner, TeamRedMiner, GMiner
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import psutil
import re

logger = logging.getLogger(__name__)

class MinerBinary:
    """Represents a mining binary configuration"""
    
    def __init__(self, name: str, executable: str, algorithms: List[str], gpu_vendor: str):
        self.name = name
        self.executable = executable
        self.algorithms = algorithms
        self.gpu_vendor = gpu_vendor
        self.process: Optional[subprocess.Popen] = None
        self.config_file = f"/tmp/{name.lower()}_config.json"

class RealMinerIntegrator:
    """Integrates real mining binaries with our HPC framework"""
    
    def __init__(self, miners_dir: str = "/opt/miners"):
        self.miners_dir = Path(miners_dir)
        self.miners_dir.mkdir(exist_ok=True, parents=True)
        
        # Available miners for AMD MI300
        self.available_miners = {
            "lolminer": MinerBinary(
                name="lolMiner",
                executable="lolMiner",
                algorithms=["Ethash", "Kawpow", "Autolykos2", "BeamV3"],
                gpu_vendor="AMD"
            ),
            "teamredminer": MinerBinary(
                name="TeamRedMiner", 
                executable="teamredminer",
                algorithms=["Ethash", "Kawpow", "X11", "Yescrypt"],
                gpu_vendor="AMD"
            ),
            "srbminer": MinerBinary(
                name="SRBMiner-MULTI",
                executable="SRBMiner-MULTI",
                algorithms=["RandomX", "Ethash", "Kawpow", "X11", "Yescrypt"],
                gpu_vendor="AMD"
            ),
            "xmrig": MinerBinary(
                name="XMRig",
                executable="xmrig",
                algorithms=["RandomX"],
                gpu_vendor="CPU"
            )
        }
        
        self.active_processes = {}
        logger.info(f"Miner integrator initialized with {len(self.available_miners)} miners")
    
    async def install_miners(self):
        """Download and install mining binaries"""
        logger.info("Installing mining binaries...")
        
        # lolMiner installation
        await self._install_lolminer()
        
        # TeamRedMiner installation  
        await self._install_teamredminer()
        
        # SRBMiner installation
        await self._install_srbminer()
        
        # XMRig installation
        await self._install_xmrig()
        
        logger.info("All miners installed successfully")
    
    async def _install_lolminer(self):
        """Install lolMiner for AMD GPUs"""
        try:
            logger.info("Installing lolMiner...")
            
            # Download lolMiner
            download_url = "https://github.com/Lolliedieb/lolMiner-releases/releases/download/1.88/lolMiner_v1.88_Lin64.tar.gz"
            
            cmd = f"""
            cd {self.miners_dir} &&
            wget -O lolminer.tar.gz {download_url} &&
            tar -xzf lolminer.tar.gz &&
            mv 1.88 lolminer &&
            chmod +x lolminer/lolMiner &&
            ln -sf {self.miners_dir}/lolminer/lolMiner /usr/local/bin/lolMiner
            """
            
            result = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            logger.info("** lolMiner installed successfully")
            
        except Exception as e:
            logger.error(f"Failed to install lolMiner: {e}")
    
    async def _install_teamredminer(self):
        """Install TeamRedMiner for AMD GPUs"""
        try:
            logger.info("Installing TeamRedMiner...")
            
            download_url = "https://github.com/todxx/teamredminer/releases/download/v0.10.21/teamredminer-v0.10.21-linux.tgz"
            
            cmd = f"""
            cd {self.miners_dir} &&
            wget -O teamredminer.tgz {download_url} &&
            tar -xzf teamredminer.tgz &&
            mv teamredminer-v0.10.21-linux teamredminer &&
            chmod +x teamredminer/teamredminer &&
            ln -sf {self.miners_dir}/teamredminer/teamredminer /usr/local/bin/teamredminer
            """
            
            result = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            logger.info("** TeamRedMiner installed successfully")
            
        except Exception as e:
            logger.error(f"Failed to install TeamRedMiner: {e}")
    
    async def _install_srbminer(self):
        """Install SRBMiner-MULTI for AMD GPUs"""
        try:
            logger.info("Installing SRBMiner-MULTI...")
            
            download_url = "https://github.com/doktor83/SRBMiner-Multi/releases/download/2.4.8/SRBMiner-Multi-2-4-8-Linux.tar.gz"
            
            cmd = f"""
            cd {self.miners_dir} &&
            wget -O srbminer.tar.gz {download_url} &&
            tar -xzf srbminer.tar.gz &&
            mv SRBMiner-Multi-2-4-8 srbminer &&
            chmod +x srbminer/SRBMiner-MULTI &&
            ln -sf {self.miners_dir}/srbminer/SRBMiner-MULTI /usr/local/bin/SRBMiner-MULTI
            """
            
            result = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            logger.info("** SRBMiner-MULTI installed successfully")
            
        except Exception as e:
            logger.error(f"Failed to install SRBMiner-MULTI: {e}")
    
    async def _install_xmrig(self):
        """Install XMRig for RandomX CPU mining"""
        try:
            logger.info("Installing XMRig...")
            
            download_url = "https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-linux-static-x64.tar.gz"
            
            cmd = f"""
            cd {self.miners_dir} &&
            wget -O xmrig.tar.gz {download_url} &&
            tar -xzf xmrig.tar.gz &&
            mv xmrig-6.21.3 xmrig &&
            chmod +x xmrig/xmrig &&
            ln -sf {self.miners_dir}/xmrig/xmrig /usr/local/bin/xmrig
            """
            
            result = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await result.wait()
            
            logger.info("** XMRig installed successfully")
            
        except Exception as e:
            logger.error(f"Failed to install XMRig: {e}")
    
    def get_optimal_miner(self, algorithm: str, gpu_vendor: str = "AMD") -> Optional[MinerBinary]:
        """Get the best miner for given algorithm and GPU vendor"""
        
        # Algorithm to miner mapping for AMD MI300
        algorithm_miners = {
            "Ethash": ["lolminer", "teamredminer"],
            "Kawpow": ["lolminer", "teamredminer"], 
            "RandomX": ["srbminer", "xmrig"],
            "X11": ["teamredminer", "srbminer"],
            "Yescrypt": ["teamredminer", "srbminer"],
            "SHA256": ["srbminer"],
            "Scrypt": ["srbminer"]
        }
        
        preferred_miners = algorithm_miners.get(algorithm, [])
        
        for miner_name in preferred_miners:
            if miner_name in self.available_miners:
                miner = self.available_miners[miner_name]
                if algorithm in miner.algorithms:
                    return miner
        
        return None
    
    async def start_mining(self, algorithm: str, pool_config: Dict[str, Any], gpu_devices: List[int] = None) -> bool:
        """Start mining with optimal miner for algorithm"""
        
        miner = self.get_optimal_miner(algorithm)
        if not miner:
            logger.error(f"No suitable miner found for {algorithm}")
            return False
        
        if gpu_devices is None:
            gpu_devices = list(range(8))  # All 8 MI300 GPUs
        
        try:
            # Generate miner command
            command = self._generate_miner_command(miner, algorithm, pool_config, gpu_devices)
            
            logger.info(f"Starting {miner.name} for {algorithm}: {' '.join(command)}")
            
            # Start miner process
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.miners_dir / miner.name.lower()
            )
            
            self.active_processes[f"{algorithm}_{miner.name}"] = process
            miner.process = process
            
            logger.info(f"** {miner.name} started successfully for {algorithm}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {miner.name} for {algorithm}: {e}")
            return False
    
    def _generate_miner_command(self, miner: MinerBinary, algorithm: str, pool_config: Dict[str, Any], gpu_devices: List[int]) -> List[str]:
        """Generate command line arguments for specific miner"""
        
        pool_url = pool_config["url"].replace("stratum+tcp://", "")
        username = pool_config["username"]
        password = pool_config.get("password", "x")
        worker_name = pool_config.get("worker_name", "HPE_CRAY_XD675")
        
        if miner.name == "lolMiner":
            return self._generate_lolminer_command(algorithm, pool_url, username, password, worker_name, gpu_devices)
        elif miner.name == "TeamRedMiner":
            return self._generate_teamredminer_command(algorithm, pool_url, username, password, worker_name, gpu_devices)
        elif miner.name == "SRBMiner-MULTI":
            return self._generate_srbminer_command(algorithm, pool_url, username, password, worker_name, gpu_devices)
        elif miner.name == "XMRig":
            return self._generate_xmrig_command(pool_url, username, password)
        else:
            raise ValueError(f"Unknown miner: {miner.name}")
    
    def _generate_lolminer_command(self, algorithm: str, pool_url: str, username: str, password: str, worker_name: str, gpu_devices: List[int]) -> List[str]:
        """Generate lolMiner command"""
        
        algo_map = {
            "Ethash": "ETHASH",
            "Kawpow": "KAWPOW"
        }
        
        lol_algorithm = algo_map.get(algorithm, "ETHASH")
        gpu_list = ",".join(map(str, gpu_devices))
        
        return [
            "lolMiner",
            "--algo", lol_algorithm,
            "--pool", pool_url,
            "--user", f"{username}.{worker_name}",
            "--pass", password,
            "--devices", gpu_list,
            "--apiport", "8080",
            "--log", "1",
            "--longstats", "60",
            "--digits", "3"
        ]
    
    def _generate_teamredminer_command(self, algorithm: str, pool_url: str, username: str, password: str, worker_name: str, gpu_devices: List[int]) -> List[str]:
        """Generate TeamRedMiner command"""
        
        algo_map = {
            "Ethash": "ethash", 
            "Kawpow": "kawpow",
            "X11": "x11",
            "Yescrypt": "yescrypt"
        }
        
        trm_algorithm = algo_map.get(algorithm, "ethash")
        gpu_list = ",".join(map(str, gpu_devices))
        
        return [
            "teamredminer",
            "-a", trm_algorithm,
            "-o", f"stratum+tcp://{pool_url}",
            "-u", f"{username}.{worker_name}",
            "-p", password,
            "-d", gpu_list,
            "--api_listen", "127.0.0.1:4028",
            "--log_file", "/var/log/hpc-miner/teamredminer.log"
        ]
    
    def _generate_srbminer_command(self, algorithm: str, pool_url: str, username: str, password: str, worker_name: str, gpu_devices: List[int]) -> List[str]:
        """Generate SRBMiner-MULTI command"""
        
        algo_map = {
            "RandomX": "randomx",
            "Ethash": "ethash", 
            "Kawpow": "kawpow",
            "X11": "x11",
            "Yescrypt": "yescrypt",
            "SHA256": "sha256",
            "Scrypt": "scrypt"
        }
        
        srb_algorithm = algo_map.get(algorithm, "ethash")
        gpu_list = ",".join(map(str, gpu_devices))
        
        command = [
            "SRBMiner-MULTI",
            "--algorithm", srb_algorithm,
            "--pool", pool_url,
            "--wallet", f"{username}.{worker_name}",
            "--password", password,
            "--api-enable", 
            "--api-port", "21555",
            "--log-file", "/var/log/hpc-miner/srbminer.log"
        ]
        
        if algorithm != "RandomX":  # GPU mining
            command.extend(["--gpu-id", gpu_list])
        else:  # CPU mining
            command.extend(["--cpu-threads", "64"])
        
        return command
    
    def _generate_xmrig_command(self, pool_url: str, username: str, password: str) -> List[str]:
        """Generate XMRig command for RandomX"""
        return [
            "xmrig",
            "-o", pool_url,
            "-u", username,
            "-p", password,
            "--threads", "64",
            "--huge-pages",
            "--http-port", "8080",
            "--log-file", "/var/log/hpc-miner/xmrig.log"
        ]
    
    async def stop_mining(self, algorithm: str = None):
        """Stop mining processes"""
        if algorithm:
            # Stop specific algorithm
            processes_to_stop = [k for k in self.active_processes.keys() if algorithm in k]
        else:
            # Stop all processes
            processes_to_stop = list(self.active_processes.keys())
        
        for process_key in processes_to_stop:
            process = self.active_processes[process_key]
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=10)
                logger.info(f"**** Stopped {process_key}")
            except asyncio.TimeoutError:
                process.kill()
                logger.warning(f"**** Force killed {process_key}")
            except Exception as e:
                logger.error(f"Error stopping {process_key}: {e}")
            
            del self.active_processes[process_key]
    
    async def get_mining_stats(self) -> Dict[str, Any]:
        """Get mining statistics from active miners"""
        stats = {
            "total_hashrate": 0,
            "active_miners": len(self.active_processes),
            "gpu_stats": {},
            "algorithms": []
        }
        
        for process_key, process in self.active_processes.items():
            if process.poll() is None:  # Process is running
                algorithm = process_key.split('_')[0]
                stats["algorithms"].append(algorithm)
                
                # Try to get stats from miner API
                try:
                    miner_stats = await self._get_miner_api_stats(process_key)
                    if miner_stats:
                        stats["total_hashrate"] += miner_stats.get("hashrate", 0)
                        stats["gpu_stats"][process_key] = miner_stats
                except Exception as e:
                    logger.debug(f"Could not get stats for {process_key}: {e}")
        
        return stats
    
    async def _get_miner_api_stats(self, process_key: str) -> Optional[Dict[str, Any]]:
        """Get statistics from miner API and system sensors"""
        import aiohttp
        
        # Default mining stats
        mining_stats = {
            "hashrate": 0,
            "accepted_shares": 0,
            "rejected_shares": 0,
            "temperature": 0.0,
            "power": 0.0
        }

        # Identify which miner is associated with the process_key
        miner_name = ""
        for m_id in self.available_miners:
            if self.available_miners[m_id].name in process_key:
                miner_name = self.available_miners[m_id].name
                break

        try:
            async with aiohttp.ClientSession() as session:
                # 1. Fetch data from specific Miner API
                if miner_name == "lolMiner":
                    async with session.get("http://127.0.0.1:8080/summary") as resp:
                        data = await resp.json()
                        mining_stats["hashrate"] = data.get("total_hashrate", 0)
                        mining_stats["accepted_shares"] = data.get("total_accepted", 0)
                        mining_stats["rejected_shares"] = data.get("total_rejected", 0)

                elif miner_name == "TeamRedMiner":
                    async with session.get("http://127.0.0.1:4028/summary") as resp:
                        data = await resp.json() # TRM uses a specific text/json format
                        summary = data.get("SUMMARY", [{}])[0]
                        mining_stats["hashrate"] = summary.get("MHS 30s", 0) * 1e6
                        mining_stats["accepted_shares"] = summary.get("Accepted", 0)
                        mining_stats["rejected_shares"] = summary.get("Rejected", 0)

                elif miner_name == "SRBMiner-MULTI":
                    async with session.get("http://127.0.0.1:21555/api") as resp:
                        data = await resp.json()
                        mining_stats["hashrate"] = data.get("total_hashrate", 0)
                        mining_stats["accepted_shares"] = data.get("total_accepted_shares", 0)
                        mining_stats["rejected_shares"] = data.get("total_rejected_shares", 0)

                elif miner_name == "XMRig":
                    async with session.get("http://127.0.0.1:8080/1/summary") as resp:
                        data = await resp.json()
                        mining_stats["hashrate"] = data.get("hashrate", {}).get("total", [0])[0]
                        mining_stats["accepted_shares"] = data.get("shares", {}).get("accepted", 0)
                        mining_stats["rejected_shares"] = data.get("shares", {}).get("rejected", 0)

            # 2. Fetch Hardware Telemetry (ROCm/SMI for AMD GPUs)
            # Querying rocm-smi for real power and temp if on AMD system
            try:
                smi_output = subprocess.check_output(
                    ["rocm-smi", "--showtemp", "--showpower", "--json"], 
                    stderr=subprocess.DEVNULL, encoding='utf-8'
                )
                hw_data = json.loads(smi_output)
                # Aggregate temperatures and power from all detected cards
                temps = [float(v.get('Temperature (Sensor edge) (C)', 0)) for k, v in hw_data.items() if 'card' in k]
                powers = [float(v.get('Average Graphics Package Power (W)', 0)) for k, v in hw_data.items() if 'card' in k]
                
                if temps: mining_stats["temperature"] = max(temps)
                if powers: mining_stats["power"] = sum(powers)
            except:
                # Fallback to psutil for basic system power/temp if SMI fails
                mining_stats["temperature"] = 0.0 # Requires specific sensors-detect config

            return mining_stats

        except Exception as e:
            logger.debug(f"Production stats collection failed for {process_key}: {e}")
            return mining_stats
        
    def is_mining_active(self) -> bool:
        """Check if any mining process is active"""
        return len(self.active_processes) > 0

# Example usage and testing
async def main():
    """Test miner integration"""
    integrator = RealMinerIntegrator()
    
    print("🔧 Installing mining binaries...")
    await integrator.install_miners()
    
    print("** Installation complete!")
    
    # Test configuration
    pool_config = {
        "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353",
        "username": "bc1qtest...",
        "password": "x",
        "worker_name": "HPE_CRAY_XD675"
    }
    
    print("🚀 Testing miner start...")
    success = await integrator.start_mining("Ethash", pool_config, [0, 1])  # Test with 2 GPUs
    
    if success:
        print("** Mining started successfully!")
        
        # Wait and get stats
        await asyncio.sleep(10)
        stats = await integrator.get_mining_stats()
        print(f"** Mining stats: {stats}")
        
        # Stop mining
        await integrator.stop_mining()
        print("**** Mining stopped")
    else:
        print("**** Failed to start mining")

if __name__ == "__main__":
    asyncio.run(main())