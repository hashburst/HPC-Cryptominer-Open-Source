"""
Hardware Detection and Management
Optimized for Intel/AMD CPUs and NVIDIA/AMD GPUs
"""

import psutil
import platform
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional
import asyncio
import os

logger = logging.getLogger(__name__)

class HardwareManager:
    """Manages hardware detection and optimization"""
    
    def __init__(self):
        self.hardware_info = {}
        self.cpu_info = {}
        self.gpu_info = []
        self.initialized = False
    
    async def initialize(self):
        """Initialize hardware detection"""
        if self.initialized:
            return
        
        logger.info("Initializing hardware detection...")
        
        # Detect CPU
        self.cpu_info = await self._detect_cpu()
        
        # Detect GPUs
        self.gpu_info = await self._detect_gpus()
        
        # Build comprehensive hardware info
        self.hardware_info = {
            "cpu": self.cpu_info,
            "gpus": self.gpu_info,
            "memory": self._get_memory_info(),
            "system": self._get_system_info()
        }
        
        self.initialized = True
        logger.info("Hardware detection completed")
        self._log_hardware_summary()
    
    async def _detect_cpu(self) -> Dict[str, Any]:
        """Detect CPU information and capabilities"""
        try:
            cpu_info = {
                "brand": platform.processor(),
                "architecture": platform.machine(),
                "cores": psutil.cpu_count(logical=False),
                "threads": psutil.cpu_count(logical=True),
                "frequency": {
                    "current": 0,
                    "min": 0,
                    "max": 0
                },
                "cache": {},
                "features": [],
                "vendor": "unknown",
                "family": "unknown"
            }
            
            # Get CPU frequency
            try:
                freq = psutil.cpu_freq()
                if freq:
                    cpu_info["frequency"] = {
                        "current": freq.current,
                        "min": freq.min,
                        "max": freq.max
                    }
            except Exception as e:
                logger.warning(f"Could not get CPU frequency: {e}")
            
            # Detect CPU vendor and family
            if "Intel" in cpu_info["brand"]:
                cpu_info["vendor"] = "Intel"
                cpu_info["family"] = self._detect_intel_family(cpu_info["brand"])
            elif "AMD" in cpu_info["brand"]:
                cpu_info["vendor"] = "AMD"
                cpu_info["family"] = self._detect_amd_family(cpu_info["brand"])
            
            # Detect CPU features for optimization
            cpu_info["features"] = await self._detect_cpu_features()
            
            # Get cache information
            cpu_info["cache"] = await self._get_cpu_cache_info()
            
            return cpu_info
            
        except Exception as e:
            logger.error(f"Error detecting CPU: {e}")
            return {"cores": 1, "threads": 1, "vendor": "unknown"}
    
    def _detect_intel_family(self, brand: str) -> str:
        """Detect Intel CPU family"""
        brand = brand.upper()
        if "XEON" in brand:
            return "Xeon"
        elif "CORE" in brand:
            if "I9" in brand:
                return "Core i9"
            elif "I7" in brand:
                return "Core i7"
            elif "I5" in brand:
                return "Core i5"
            elif "I3" in brand:
                return "Core i3"
        return "Intel"
    
    def _detect_amd_family(self, brand: str) -> str:
        """Detect AMD CPU family"""
        brand = brand.upper()
        if "EPYC" in brand:
            return "EPYC"
        elif "RYZEN" in brand:
            if "THREADRIPPER" in brand:
                return "Ryzen Threadripper"
            elif "9" in brand:
                return "Ryzen 9"
            elif "7" in brand:
                return "Ryzen 7"
            elif "5" in brand:
                return "Ryzen 5"
            elif "3" in brand:
                return "Ryzen 3"
        return "AMD"
    
    async def _detect_cpu_features(self) -> List[str]:
        """Detect CPU features for optimization"""
        features = []
        try:
            if platform.system() == "Linux":
                # Read CPU features from /proc/cpuinfo
                with open("/proc/cpuinfo", "r") as f:
                    content = f.read()
                    if "aes" in content:
                        features.append("AES")
                    if "avx" in content:
                        features.append("AVX")
                    if "avx2" in content:
                        features.append("AVX2")
                    if "sse4_1" in content:
                        features.append("SSE4.1")
                    if "sse4_2" in content:
                        features.append("SSE4.2")
        except Exception as e:
            logger.warning(f"Could not detect CPU features: {e}")
        
        return features
    
    async def _get_cpu_cache_info(self) -> Dict[str, Any]:
        """Get CPU cache information"""
        cache_info = {"L1": 0, "L2": 0, "L3": 0}
        
        try:
            if platform.system() == "Linux":
                # Try to read cache info from sysfs
                cache_paths = [
                    "/sys/devices/system/cpu/cpu0/cache/index0/size",  # L1 data
                    "/sys/devices/system/cpu/cpu0/cache/index2/size",  # L2
                    "/sys/devices/system/cpu/cpu0/cache/index3/size"   # L3
                ]
                
                cache_levels = ["L1", "L2", "L3"]
                for i, path in enumerate(cache_paths):
                    try:
                        if os.path.exists(path):
                            with open(path, "r") as f:
                                size_str = f.read().strip()
                                # Convert KB to bytes
                                if size_str.endswith("K"):
                                    cache_info[cache_levels[i]] = int(size_str[:-1]) * 1024
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Could not get CPU cache info: {e}")
        
        return cache_info
    
    async def _detect_gpus(self) -> List[Dict[str, Any]]:
        """Detect GPU information"""
        gpus = []
        
        # Try NVIDIA GPUs first
        nvidia_gpus = await self._detect_nvidia_gpus()
        gpus.extend(nvidia_gpus)
        
        # Try AMD GPUs
        amd_gpus = await self._detect_amd_gpus()
        gpus.extend(amd_gpus)
        
        return gpus
    
    async def _detect_nvidia_gpus(self) -> List[Dict[str, Any]]:
        """Detect NVIDIA GPUs using nvidia-smi"""
        gpus = []
        
        try:
            # Try to run nvidia-smi
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=index,name,memory.total,memory.free,temperature.gpu,power.draw", 
                 "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 6:
                            gpu_info = {
                                "id": int(parts[0]),
                                "name": parts[1],
                                "vendor": "NVIDIA",
                                "memory_total": int(parts[2]) * 1024 * 1024,  # Convert MB to bytes
                                "memory_free": int(parts[3]) * 1024 * 1024,
                                "temperature": float(parts[4]) if parts[4] != "[Not Supported]" else 0,
                                "power_draw": float(parts[5]) if parts[5] != "[Not Supported]" else 0,
                                "available": True,
                                "compute_capability": self._get_nvidia_compute_capability(parts[1])
                            }
                            gpus.append(gpu_info)
                            
                logger.info(f"Detected {len(gpus)} NVIDIA GPU(s)")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.info("NVIDIA drivers not found or nvidia-smi not available")
        except Exception as e:
            logger.warning(f"Error detecting NVIDIA GPUs: {e}")
        
        return gpus
    
    def _get_nvidia_compute_capability(self, gpu_name: str) -> str:
        """Get NVIDIA GPU compute capability"""
        gpu_name = gpu_name.upper()
        
        # H100 series
        if "H100" in gpu_name:
            return "9.0"
        # H200 series  
        elif "H200" in gpu_name:
            return "9.0"
        # RTX 40 series
        elif "RTX 40" in gpu_name or "4090" in gpu_name or "4080" in gpu_name:
            return "8.9"
        # RTX 30 series
        elif "RTX 30" in gpu_name or "3090" in gpu_name or "3080" in gpu_name:
            return "8.6"
        # Default
        else:
            return "6.0"
    
    async def _detect_amd_gpus(self) -> List[Dict[str, Any]]:
        """Detect AMD GPUs using rocm-smi"""
        gpus = []
        
        try:
            # Try to run rocm-smi
            result = subprocess.run(
                ["rocm-smi", "--showid", "--showproductname", "--showmeminfo", "--showtemp", "--showpower"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                current_gpu = {}
                
                for line in lines:
                    line = line.strip()
                    if "GPU[" in line and "]:" in line:
                        # Start of new GPU info
                        if current_gpu:
                            gpus.append(current_gpu)
                        
                        gpu_id = int(line.split('[')[1].split(']')[0])
                        current_gpu = {
                            "id": gpu_id,
                            "vendor": "AMD",
                            "available": True
                        }
                    elif "Card series:" in line:
                        current_gpu["name"] = line.split(":")[1].strip()
                    elif "Memory Total:" in line:
                        mem_str = line.split(":")[1].strip()
                        if "MB" in mem_str:
                            current_gpu["memory_total"] = int(mem_str.replace("MB", "")) * 1024 * 1024
                
                if current_gpu:
                    gpus.append(current_gpu)
                    
                # Special detection for MI300 series
                for gpu in gpus:
                    if "MI300" in gpu.get("name", ""):
                        gpu["compute_capability"] = "gfx942"
                        
                logger.info(f"Detected {len(gpus)} AMD GPU(s)")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.info("AMD ROCm drivers not found or rocm-smi not available")
        except Exception as e:
            logger.warning(f"Error detecting AMD GPUs: {e}")
        
        return gpus
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get system memory information"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percentage": memory.percent
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.architecture(),
            "hostname": platform.node(),
            "python_version": platform.python_version()
        }
    
    def _log_hardware_summary(self):
        """Log hardware detection summary"""
        logger.info("=== Hardware Detection Summary ===")
        logger.info(f"CPU: {self.cpu_info.get('vendor', 'Unknown')} {self.cpu_info.get('family', 'Unknown')}")
        logger.info(f"CPU Cores: {self.cpu_info.get('cores', 0)}, Threads: {self.cpu_info.get('threads', 0)}")
        logger.info(f"CPU Features: {', '.join(self.cpu_info.get('features', []))}")
        
        for i, gpu in enumerate(self.gpu_info):
            memory_gb = gpu.get('memory_total', 0) / (1024**3)
            logger.info(f"GPU {i}: {gpu.get('vendor', 'Unknown')} {gpu.get('name', 'Unknown')} ({memory_gb:.1f}GB)")
        
        memory_gb = self.hardware_info['memory']['total'] / (1024**3)
        logger.info(f"System Memory: {memory_gb:.1f}GB")
        logger.info("=== End Hardware Summary ===")
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get complete hardware information"""
        return self.hardware_info
    
    def get_optimal_thread_count(self) -> int:
        """Get optimal thread count for mining"""
        cpu_threads = self.cpu_info.get('threads', 1)
        # Reserve 1-2 threads for system operations
        optimal = max(1, cpu_threads - 2)
        return optimal
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current hardware metrics"""
        metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "temperature": {},
            "power": 0.0
        }
        
        # Try to get temperature readings
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                for sensor_name, sensor_list in temps.items():
                    for sensor in sensor_list:
                        metrics["temperature"][f"{sensor_name}_{sensor.label}"] = sensor.current
        except Exception as e:
            logger.debug(f"Could not get temperature readings: {e}")
        
        return metrics
    
    async def optimize_for_algorithm(self, algorithm: str) -> Dict[str, Any]:
        """Get hardware optimization settings for specific algorithm"""
        optimizations = {
            "cpu_threads": self.get_optimal_thread_count(),
            "gpu_intensity": 80,
            "memory_allocation": "auto"
        }
        
        # Algorithm-specific optimizations
        if algorithm == "RandomX":
            # RandomX is memory-intensive
            optimizations["cpu_threads"] = min(self.cpu_info.get('cores', 1), 16)
            optimizations["memory_allocation"] = "2GB_per_thread"
        elif algorithm == "Ethash":
            # Ethash is GPU-memory intensive
            optimizations["gpu_intensity"] = 100
            optimizations["cpu_threads"] = 1  # Minimal CPU usage
        elif algorithm == "SHA256":
            # SHA256 can utilize all available cores
            optimizations["cpu_threads"] = self.cpu_info.get('threads', 1)
            
        return optimizations