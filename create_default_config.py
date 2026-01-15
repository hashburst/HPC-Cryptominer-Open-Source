#!/usr/bin/env python3
"""
Create Default Configuration
Generates default mining configuration with hardware detection
"""

import json
import os
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mining_engine.hardware import HardwareManager

async def create_default_config():
    """Create default configuration based on detected hardware"""
    
    # Initialize hardware manager for detection
    hw_manager = HardwareManager()
    await hw_manager.initialize()
    hw_info = hw_manager.get_hardware_info()
    
    # Base configuration
    config = {
        "mining": {
            "algorithms": ["SHA256", "RandomX", "Ethash", "Scrypt", "Yescrypt", "Kawpow", "X11"],
            "auto_start": True,
            "auto_switch": True,
            "target_rejection_rate": 0.01,
            "preferred_algorithm": "auto"
        },
        "pools": {
            "nicehash_sha256": {
                "name": "NiceHash SHA256",
                "url": "stratum+tcp://sha256.nicehash.com:3334",
                "username": "<MINING-WALLET-NICEHASH-ACCOUNT>",
                "password": "x",
                "algorithm": "SHA256",
                "priority": 1
            },
            "nicehash_randomx": {
                "name": "NiceHash RandomX",
                "url": "stratum+tcp://randomx.nicehash.com:3380",
                "username": "<MINING-WALLET-NICEHASH-ACCOUNT>",
                "password": "x",
                "algorithm": "RandomX",
                "priority": 2
            },
            "nicehash_ethash": {
                "name": "NiceHash Ethash",
                "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353",
                "username": "<MINING-WALLET-NICEHASH-ACCOUNT>",
                "password": "x",
                "algorithm": "Ethash",
                "priority": 3
            }
        },
        "hardware": {
            "detected_cpu_cores": hw_info.get("cpu", {}).get("cores", 1),
            "detected_cpu_threads": hw_info.get("cpu", {}).get("threads", 1),
            "detected_gpus": len(hw_info.get("gpus", [])),
            "cpu_threads": 0,  # 0 = auto-detect (use detected_cpu_threads - 1)
            "gpu_intensity": 80,
            "temperature_limit": 85,
            "power_limit": 0,  # 0 = no limit
            "memory_allocation": "auto"
        },
        "optimization": {
            "enable_ai": True,
            "learning_rate": 0.1,
            "optimization_interval": 300,  # 5 minutes
            "work_segmentation": True,
            "auto_pool_switch": True,
            "rejection_threshold": 0.05,
            "performance_monitoring": True
        },
        "cluster": {
            "enable": False,
            "mode": "standalone",  # standalone, master, node
            "master_url": "",
            "node_port": 8080,
            "heartbeat_interval": 30,
            "auto_discovery": False
        },
        "monitoring": {
            "enable_web_dashboard": True,
            "dashboard_port": 8081,
            "metrics_port": 8082,
            "log_level": "INFO",
            "log_file": "/app/logs/hpc_miner.log",
            "enable_prometheus": True,
            "stats_interval": 30
        },
        "integration": {
            "hashburst_ai": True,
            "nicehash_compatibility": True,
            "prometheus_metrics": True,
            "api_enabled": True,
            "webhook_notifications": False
        },
        "security": {
            "api_key": "",
            "ssl_enabled": False,
            "ssl_cert_path": "",
            "ssl_key_path": "",
            "allowed_ips": ["127.0.0.1", "localhost"]
        },
        "advanced": {
            "thread_affinity": False,
            "cpu_priority": "normal",  # low, normal, high
            "gpu_compute_mode": "auto",  # auto, cuda, opencl, rocm
            "memory_pool_size": "auto",
            "work_queue_size": 100,
            "connection_timeout": 30,
            "retry_attempts": 3
        }
    }
    
    # Hardware-specific optimizations
    cpu_info = hw_info.get("cpu", {})
    gpu_info = hw_info.get("gpus", [])
    
    # CPU optimizations
    if cpu_info.get("vendor") == "AMD":
        if "Ryzen" in cpu_info.get("family", ""):
            config["mining"]["preferred_algorithm"] = "RandomX"
            config["hardware"]["cpu_threads"] = min(cpu_info.get("cores", 1), 16)
        elif "EPYC" in cpu_info.get("family", ""):
            config["mining"]["preferred_algorithm"] = "RandomX"
            config["cluster"]["enable"] = True  # EPYC is good for cluster master
    
    elif cpu_info.get("vendor") == "Intel":
        if "Xeon" in cpu_info.get("family", ""):
            config["mining"]["preferred_algorithm"] = "SHA256"
            config["cluster"]["enable"] = True  # Xeon is good for cluster master
        elif "Core i9" in cpu_info.get("family", ""):
            config["mining"]["preferred_algorithm"] = "RandomX"
    
    # GPU optimizations
    if gpu_info:
        nvidia_gpus = [gpu for gpu in gpu_info if gpu.get("vendor") == "NVIDIA"]
        amd_gpus = [gpu for gpu in gpu_info if gpu.get("vendor") == "AMD"]
        
        if nvidia_gpus:
            # Check for high-end NVIDIA GPUs
            high_end_nvidia = any("H100" in gpu.get("name", "") or "H200" in gpu.get("name", "") 
                                for gpu in nvidia_gpus)
            if high_end_nvidia:
                config["mining"]["preferred_algorithm"] = "Ethash"
                config["hardware"]["gpu_intensity"] = 95
                config["cluster"]["enable"] = True
            else:
                config["mining"]["preferred_algorithm"] = "Ethash"
                config["hardware"]["gpu_intensity"] = 85
        
        if amd_gpus:
            # Check for high-end AMD GPUs
            high_end_amd = any("MI300" in gpu.get("name", "") for gpu in amd_gpus)
            if high_end_amd:
                config["mining"]["preferred_algorithm"] = "Ethash"
                config["hardware"]["gpu_intensity"] = 90
                config["cluster"]["enable"] = True
    
    # Memory-based optimizations
    memory_gb = hw_info.get("memory", {}).get("total", 0) / (1024**3)
    
    if memory_gb > 64:  # High memory system
        config["optimization"]["work_segmentation"] = True
        config["advanced"]["memory_pool_size"] = "large"
        config["cluster"]["enable"] = True
    elif memory_gb > 32:  # Medium memory system
        config["advanced"]["memory_pool_size"] = "medium"
    else:  # Low memory system
        config["optimization"]["work_segmentation"] = False
        config["advanced"]["memory_pool_size"] = "small"
        config["hardware"]["cpu_threads"] = min(cpu_info.get("cores", 1), 4)
    
    # Create config directory
    config_dir = Path("/app/config")
    config_dir.mkdir(exist_ok=True)
    
    # Save configuration
    config_file = config_dir / "mining_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"** Default configuration created: {config_file}")
    print(f"** Detected Hardware:")
    print(f"   CPU: {cpu_info.get('vendor', 'Unknown')} {cpu_info.get('family', 'Unknown')} ({cpu_info.get('cores', 0)} cores)")
    print(f"   GPUs: {len(gpu_info)} detected")
    for i, gpu in enumerate(gpu_info):
        memory_gb = gpu.get('memory_total', 0) / (1024**3)
        print(f"     GPU {i}: {gpu.get('vendor', 'Unknown')} {gpu.get('name', 'Unknown')} ({memory_gb:.1f}GB)")
    print(f"   Memory: {memory_gb:.1f}GB")
    print(f"   ** Recommended Algorithm: {config['mining']['preferred_algorithm']}")
    
    if config["cluster"]["enable"]:
        print("** Cluster mode recommended for this hardware")
    
    return config

if __name__ == "__main__":
    asyncio.run(create_default_config())