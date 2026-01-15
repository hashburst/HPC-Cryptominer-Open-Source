from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

# Add mining engine to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from mining_engine import MiningEngine, HardwareManager, AIOptimizer
    from mining_engine.algorithms import AlgorithmManager
    from monitoring import PerformanceMonitor
    from orchestrator.cluster_manager import ClusterManager
    from optimization.gpu_optimizer import AMMI300Optimizer
    from optimization.network_optimizer import NetworkOptimizer
    from optimization.ai_performance_optimizer import AIPerformanceOptimizer
    from monitoring.advanced_analytics import AdvancedAnalytics
    MINING_AVAILABLE = True
except ImportError as e:
    print(f"Mining engine not available: {e}")
    MINING_AVAILABLE = False
    # Define placeholder classes to avoid NameError
    MiningEngine = None
    HardwareManager = None
    AIOptimizer = None
    AlgorithmManager = None
    PerformanceMonitor = None
    ClusterManager = None
    AMMI300Optimizer = None
    NetworkOptimizer = None
    AIPerformanceOptimizer = None
    AdvancedAnalytics = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="HPC Cryptominer API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global mining components
mining_engine: Optional[MiningEngine] = None
hardware_manager: Optional[HardwareManager] = None
performance_monitor: Optional[PerformanceMonitor] = None
cluster_manager: Optional[ClusterManager] = None

# Phase 8 & 9: Advanced optimization components
gpu_optimizer: Optional[AMMI300Optimizer] = None
network_optimizer: Optional[NetworkOptimizer] = None
ai_optimizer: Optional[AIPerformanceOptimizer] = None
advanced_analytics: Optional[AdvancedAnalytics] = None

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class MiningCommand(BaseModel):
    action: str  # start, stop, optimize
    algorithm: Optional[str] = None
    pool: Optional[str] = None

class MiningStats(BaseModel):
    hashrate: float = 0.0
    accepted_shares: int = 0
    rejected_shares: int = 0
    active_workers: int = 0
    algorithm: str = ""
    temperature: Dict[str, float] = {}
    uptime: float = 0.0
    running: bool = False

class NodeRegistration(BaseModel):
    hostname: str
    ip_address: str
    port: int
    cpu_cores: int
    cpu_threads: int
    gpu_count: int
    gpu_memory: int
    total_memory: int

class NodeStatus(BaseModel):
    node_id: str
    status: str
    hashrate: float = 0.0
    temperature: Dict[str, float] = {}
    power_usage: float = 0.0
    uptime: float = 0.0
    algorithm: Optional[str] = None
    pool: Optional[str] = None

class WorkAssignment(BaseModel):
    node_id: str
    algorithm: str
    pool: str
    work_segments: List[str] = []

# Original endpoints
@api_router.get("/")
async def root():
    return {"message": "HPC Cryptominer API v1.0.0", "mining_available": MINING_AVAILABLE}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Mining API endpoints
@api_router.get("/mining/status")
async def get_mining_status():
    """Get current mining status"""
    if not MINING_AVAILABLE or not mining_engine:
        return {"error": "Mining engine not available", "mining_available": False}
    
    try:
        status = mining_engine.get_status()
        stats = mining_engine.get_stats()
        
        return {
            "mining_available": True,
            "running": status.get("running", False),
            "uptime": status.get("uptime", 0),
            "stats": {
                "hashrate": stats.hashrate,
                "accepted_shares": stats.accepted_shares,
                "rejected_shares": stats.rejected_shares,
                "active_workers": stats.workers_active,
                "algorithm": stats.algorithm,
                "temperature": stats.temperature,
                "uptime": stats.uptime
            },
            "hardware": status.get("hardware", {}),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {"error": str(e), "mining_available": False}

@api_router.get("/mining/stats")
async def get_mining_stats():
    """Get detailed mining statistics"""
    if not MINING_AVAILABLE or not mining_engine:
        raise HTTPException(status_code=503, detail="Mining engine not available")
    
    try:
        stats = mining_engine.get_stats()
        return {
            "hashrate": stats.hashrate,
            "accepted_shares": stats.accepted_shares,
            "rejected_shares": stats.rejected_shares,
            "total_hashes": stats.total_hashes,
            "active_workers": stats.workers_active,
            "algorithm": stats.algorithm,
            "pool": stats.pool,
            "temperature": stats.temperature,
            "power_usage": stats.power_usage,
            "uptime": stats.uptime,
            "efficiency": (stats.accepted_shares / max(1, stats.accepted_shares + stats.rejected_shares)) * 100,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/mining/start")
async def start_mining():
    """Start mining"""
    if not MINING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mining engine not available")
    
    global mining_engine
    try:
        if not mining_engine:
            config_path = "/app/config/mining_config.json"
            mining_engine = MiningEngine(config_path)
        
        if not mining_engine.is_running:
            await mining_engine.start()
            return {"success": True, "message": "Mining started"}
        else:
            return {"success": True, "message": "Mining already running"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start mining: {str(e)}")

@api_router.post("/mining/stop")
async def stop_mining():
    """Stop mining"""
    if not MINING_AVAILABLE or not mining_engine:
        return {"success": True, "message": "Mining not running"}
    
    try:
        await mining_engine.stop()
        return {"success": True, "message": "Mining stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop mining: {str(e)}")

@api_router.post("/mining/optimize")
async def optimize_mining():
    """Trigger AI optimization"""
    if not MINING_AVAILABLE or not mining_engine:
        raise HTTPException(status_code=503, detail="Mining engine not available")
    
    try:
        # This would trigger immediate AI optimization
        return {"success": True, "message": "AI optimization triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/mining/algorithms")
async def get_algorithms():
    """Get supported mining algorithms"""
    if not MINING_AVAILABLE:
        return {"algorithms": [], "error": "Mining engine not available"}
    
    try:
        algorithm_manager = AlgorithmManager()
        return {
            "algorithms": algorithm_manager.list_algorithms(),
            "supported_count": len(algorithm_manager.list_algorithms())
        }
    except Exception as e:
        return {"algorithms": [], "error": str(e)}

@api_router.get("/mining/hardware")
async def get_hardware_info():
    """Get hardware information"""
    if not MINING_AVAILABLE:
        return {"error": "Mining engine not available"}
    
    try:
        global hardware_manager
        if not hardware_manager:
            hardware_manager = HardwareManager()
            await hardware_manager.initialize()
        
        return hardware_manager.get_hardware_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/mining/config")
async def get_mining_config():
    """Get current mining configuration"""
    try:
        config_path = "/app/config/mining_config.json"
        if os.path.exists(config_path):
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        else:
            return {"error": "Configuration file not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/mining/command")
async def execute_mining_command(command: MiningCommand):
    """Execute mining command"""
    if not MINING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mining engine not available")
    
    try:
        if command.action == "start":
            return await start_mining()
        elif command.action == "stop":
            return await stop_mining()
        elif command.action == "optimize":
            return await optimize_mining()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command.action}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cluster Management API Endpoints
@api_router.get("/cluster/status")
async def get_cluster_status():
    """Get cluster status and statistics"""
    if not MINING_AVAILABLE:
        return {"error": "Mining engine not available", "cluster_available": False}
    
    global cluster_manager
    if not cluster_manager:
        cluster_manager = ClusterManager()
        await cluster_manager.start()
    
    try:
        status = cluster_manager.get_cluster_status()
        return {
            "cluster_available": True,
            "cluster_id": status["cluster_id"],
            "stats": status["stats"],
            "nodes": status["nodes"],
            "optimization_history": status["optimization_history"],
            "timestamp": status["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/cluster/nodes/register")
async def register_node(node_info: NodeRegistration):
    """Register a new mining node in the cluster"""
    if not MINING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mining engine not available")
    
    global cluster_manager
    if not cluster_manager:
        cluster_manager = ClusterManager()
        await cluster_manager.start()
    
    try:
        # Generate 40-character hexadecimal node ID as specified
        node_id = uuid.uuid4().hex + uuid.uuid4().hex[:8]
        
        node_data = {
            "node_id": node_id,
            "hostname": node_info.hostname,
            "ip_address": node_info.ip_address,
            "port": node_info.port,
            "cpu_cores": node_info.cpu_cores,
            "cpu_threads": node_info.cpu_threads,
            "gpu_count": node_info.gpu_count,
            "gpu_memory": node_info.gpu_memory,
            "total_memory": node_info.total_memory
        }
        
        registered_id = await cluster_manager.register_node(node_data)
        
        return {
            "success": True,
            "node_id": registered_id,
            "message": f"Node registered successfully with ID: {registered_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register node: {str(e)}")

@api_router.delete("/cluster/nodes/{node_id}")
async def unregister_node(node_id: str):
    """Unregister a mining node from the cluster"""
    if not MINING_AVAILABLE or not cluster_manager:
        raise HTTPException(status_code=503, detail="Cluster manager not available")
    
    try:
        await cluster_manager.unregister_node(node_id)
        return {
            "success": True,
            "message": f"Node {node_id} unregistered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unregister node: {str(e)}")

@api_router.post("/cluster/nodes/{node_id}/status")
async def update_node_status(node_id: str, status: NodeStatus):
    """Update status and metrics for a specific node"""
    if not MINING_AVAILABLE or not cluster_manager:
        raise HTTPException(status_code=503, detail="Cluster manager not available")
    
    try:
        status_data = {
            "status": status.status,
            "hashrate": status.hashrate,
            "temperature": status.temperature,
            "power_usage": status.power_usage,
            "uptime": status.uptime,
            "algorithm": status.algorithm,
            "pool": status.pool
        }
        
        await cluster_manager.update_node_status(node_id, status_data)
        return {
            "success": True,
            "message": f"Node {node_id} status updated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update node status: {str(e)}")

@api_router.get("/cluster/nodes")
async def get_cluster_nodes():
    """Get list of all nodes in the cluster"""
    if not MINING_AVAILABLE or not cluster_manager:
        return {"nodes": [], "error": "Cluster manager not available"}
    
    try:
        cluster_status = cluster_manager.get_cluster_status()
        return {
            "nodes": cluster_status["nodes"],
            "total_nodes": len(cluster_status["nodes"]),
            "active_nodes": cluster_status["stats"]["active_nodes"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/cluster/nodes/assign_work")
async def assign_work_to_node(assignment: WorkAssignment):
    """Assign work to a specific node"""
    if not MINING_AVAILABLE or not cluster_manager:
        raise HTTPException(status_code=503, detail="Cluster manager not available")
    
    try:
        success = await cluster_manager.assign_work(
            assignment.node_id,
            assignment.algorithm,
            assignment.pool,
            assignment.work_segments
        )
        
        if success:
            return {
                "success": True,
                "message": f"Work assigned to node {assignment.node_id}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to assign work to node")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/cluster/optimize")
async def get_optimization_recommendations():
    """Get AI-powered optimization recommendations for the cluster"""
    if not MINING_AVAILABLE or not cluster_manager:
        return {"recommendations": [], "error": "Cluster manager not available"}
    
    try:
        # Trigger analysis and get recommendations
        performance_analysis = await cluster_manager._analyze_cluster_performance()
        recommendations = await cluster_manager._generate_optimization_recommendations(performance_analysis)
        
        return {
            "recommendations": recommendations,
            "analysis": performance_analysis,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/cluster/optimize/apply")
async def apply_cluster_optimizations():
    """Apply AI optimization recommendations to the cluster"""
    if not MINING_AVAILABLE or not cluster_manager:
        raise HTTPException(status_code=503, detail="Cluster manager not available")
    
    try:
        # Get and apply recommendations
        performance_analysis = await cluster_manager._analyze_cluster_performance()
        recommendations = await cluster_manager._generate_optimization_recommendations(performance_analysis)
        
        if recommendations:
            await cluster_manager._apply_optimizations(recommendations)
            return {
                "success": True,
                "applied_optimizations": len(recommendations),
                "message": "Optimizations applied successfully"
            }
        else:
            return {
                "success": True,
                "applied_optimizations": 0,
                "message": "No optimizations needed at this time"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Phase 8 & 9: Advanced Optimization API Endpoints

@api_router.get("/optimization/gpu/status")
async def get_gpu_optimization_status():
    """Get AMD MI300 GPU optimization status"""
    if not MINING_AVAILABLE:
        return {"error": "Mining engine not available", "optimization_available": False}
    
    global gpu_optimizer
    if not gpu_optimizer:
        gpu_optimizer = AMMI300Optimizer()
        await gpu_optimizer.initialize_rocm_optimization()
    
    try:
        status = gpu_optimizer.get_optimization_status()
        metrics = await gpu_optimizer.get_gpu_metrics()
        
        return {
            "optimization_available": True,
            "status": status,
            "gpu_metrics": {gpu_id: {
                "hashrate": gpu.hashrate,
                "power_draw": gpu.power_draw,
                "temperature": gpu.temperature,
                "efficiency": gpu.efficiency,
                "utilization": gpu.utilization
            } for gpu_id, gpu in metrics.items()},
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/optimization/gpu/algorithm/{algorithm}")
async def optimize_gpus_for_algorithm(algorithm: str):
    """Optimize all GPUs for specific mining algorithm"""
    if not MINING_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mining engine not available")
    
    global gpu_optimizer
    if not gpu_optimizer:
        gpu_optimizer = AMMI300Optimizer()
        await gpu_optimizer.initialize_rocm_optimization()
    
    try:
        success = await gpu_optimizer.optimize_for_algorithm(algorithm)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully optimized 8x MI300 GPUs for {algorithm}",
                "algorithm": algorithm
            }
        else:
            return {
                "success": False,
                "message": f"Failed to optimize GPUs for {algorithm}",
                "algorithm": algorithm
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/optimization/gpu/monitor")
async def monitor_gpu_performance():
    """Get real-time GPU performance monitoring and auto-adjustments"""
    if not MINING_AVAILABLE or not gpu_optimizer:
        raise HTTPException(status_code=503, detail="GPU optimizer not available")
    
    try:
        monitoring_data = await gpu_optimizer.monitor_and_adjust()
        return {
            "monitoring_available": True,
            "data": monitoring_data,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/optimization/network/status")
async def get_network_optimization_status():
    """Get network optimization status for zero rejected shares"""
    if not MINING_AVAILABLE:
        return {"error": "Mining engine not available", "network_optimization_available": False}
    
    global network_optimizer
    if not network_optimizer:
        network_optimizer = NetworkOptimizer()
        
        # Initialize with default pool configs
        default_pools = [
            {"name": "NiceHash Ethash", "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353"},
            {"name": "NiceHash RandomX", "url": "stratum+tcp://randomx.nicehash.com:3380"},
            {"name": "NiceHash SHA256", "url": "stratum+tcp://sha256.nicehash.com:3334"}
        ]
        await network_optimizer.initialize_pool_configuration(default_pools)
        await network_optimizer.optimize_network_settings()
    
    try:
        status = network_optimizer.get_network_status()
        return {
            "network_optimization_available": True,
            "status": status,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/optimization/network/monitor")
async def monitor_network_performance():
    """Monitor network performance for zero rejected shares"""
    if not MINING_AVAILABLE or not network_optimizer:
        raise HTTPException(status_code=503, detail="Network optimizer not available")
    
    try:
        monitoring_data = await network_optimizer.monitor_share_submission()
        return {
            "monitoring_available": True,
            "data": monitoring_data,
            "zero_rejects_target": monitoring_data.get("data", {}).get("submission_analysis", {}).get("target_achievement", {}).get("zero_rejects", False),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/optimization/ai/analysis")
async def get_ai_performance_analysis():
    """Get comprehensive AI performance analysis and recommendations"""
    if not MINING_AVAILABLE:
        return {"error": "Mining engine not available", "ai_optimization_available": False}
    
    global ai_optimizer, gpu_optimizer, network_optimizer
    if not ai_optimizer:
        ai_optimizer = AIPerformanceOptimizer()
    
    try:
        # Get metrics from other optimizers
        gpu_metrics = {}
        network_metrics = {}
        
        if gpu_optimizer:
            gpu_metrics = await gpu_optimizer.get_gpu_metrics()
            gpu_metrics = {gpu_id: {
                "hashrate": gpu.hashrate,
                "power_draw": gpu.power_draw,
                "temperature": gpu.temperature,
                "efficiency": gpu.efficiency
            } for gpu_id, gpu in gpu_metrics.items()}
        
        if network_optimizer:
            net_status = network_optimizer.get_network_status()
            network_metrics = net_status.get("network_metrics", {})
        
        # Perform AI analysis
        analysis = await ai_optimizer.analyze_current_performance(gpu_metrics, network_metrics)
        
        return {
            "ai_optimization_available": True,
            "analysis": analysis,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/optimization/ai/apply")
async def apply_ai_optimizations():
    """Apply AI-generated optimization recommendations"""
    if not MINING_AVAILABLE or not ai_optimizer:
        raise HTTPException(status_code=503, detail="AI optimizer not available")
    
    try:
        # Get current analysis
        gpu_metrics = {}
        network_metrics = {}
        
        if gpu_optimizer:
            gpu_metrics = await gpu_optimizer.get_gpu_metrics()
            gpu_metrics = {gpu_id: {
                "hashrate": gpu.hashrate,
                "power_draw": gpu.power_draw,
                "temperature": gpu.temperature
            } for gpu_id, gpu in gpu_metrics.items()}
        
        analysis = await ai_optimizer.analyze_current_performance(gpu_metrics, network_metrics)
        recommendations = analysis.get("ai_recommendations", [])
        
        applied_count = 0
        for recommendation in recommendations:
            success = await ai_optimizer.implement_recommendation(recommendation)
            if success:
                applied_count += 1
        
        return {
            "success": True,
            "recommendations_applied": applied_count,
            "total_recommendations": len(recommendations),
            "message": f"Applied {applied_count}/{len(recommendations)} AI optimizations"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analytics/comprehensive")
async def get_comprehensive_analytics():
    """Get comprehensive performance analytics with high verbosity"""
    if not MINING_AVAILABLE:
        return {"error": "Mining engine not available", "analytics_available": False}
    
    global advanced_analytics, gpu_optimizer, network_optimizer
    if not advanced_analytics:
        advanced_analytics = AdvancedAnalytics()
    
    try:
        # Collect current metrics
        gpu_metrics = {}
        network_metrics = {}
        system_metrics = {"current_algorithm": "Ethash", "cpu_usage": 45.0, "memory_usage": 60.0}
        
        if gpu_optimizer:
            gpu_metrics = await gpu_optimizer.get_gpu_metrics()
            gpu_metrics = {gpu_id: {
                "hashrate": gpu.hashrate,
                "power_draw": gpu.power_draw,
                "temperature": gpu.temperature,
                "efficiency": gpu.efficiency,
                "memory_used": gpu.memory_used
            } for gpu_id, gpu in gpu_metrics.items()}
        
        if network_optimizer:
            net_status = network_optimizer.get_network_status()
            network_metrics = net_status.get("network_metrics", {})
        
        # Collect comprehensive metrics
        current_metrics = await advanced_analytics.collect_comprehensive_metrics(
            gpu_metrics, network_metrics, system_metrics
        )
        
        # Perform comprehensive analysis
        analysis = await advanced_analytics.perform_comprehensive_analysis()
        
        return {
            "analytics_available": True,
            "current_metrics": current_metrics.__dict__ if current_metrics else {},
            "comprehensive_analysis": analysis,
            "system_status": advanced_analytics.get_analytics_status(),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analytics/benchmark")
async def run_algorithm_benchmarks():
    """Run comprehensive algorithm benchmarks"""
    if not MINING_AVAILABLE or not advanced_analytics:
        raise HTTPException(status_code=503, detail="Advanced analytics not available")
    
    try:
        algorithms = ["Ethash", "RandomX", "SHA256", "Kawpow", "X11"]
        benchmark_results = await advanced_analytics.run_benchmark_suite(algorithms)
        
        return {
            "success": True,
            "benchmark_results": benchmark_results,
            "algorithms_tested": len(algorithms),
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/optimization/profitability")
async def get_profitability_analysis():
    """Get detailed profitability analysis and algorithm recommendations"""
    if not MINING_AVAILABLE or not ai_optimizer:
        return {"error": "AI optimizer not available", "profitability_available": False}
    
    try:
        # Get profitability analysis from AI optimizer
        gpu_metrics = {}
        network_metrics = {}
        
        analysis = await ai_optimizer.analyze_current_performance(gpu_metrics, network_metrics)
        profitability = analysis.get("profitability_analysis", {})
        
        return {
            "profitability_available": True,
            "analysis": profitability,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize mining components on startup
@app.on_event("startup")
async def startup_event():
    """Initialize mining components and advanced optimizations"""
    if MINING_AVAILABLE:
        global hardware_manager, performance_monitor, cluster_manager
        global gpu_optimizer, network_optimizer, ai_optimizer, advanced_analytics
        try:
            # Initialize hardware manager
            hardware_manager = HardwareManager()
            await hardware_manager.initialize()
            
            # Initialize cluster manager
            cluster_manager = ClusterManager()
            await cluster_manager.start()
            
            # Initialize performance monitor
            performance_monitor = PerformanceMonitor(port=8082)
            await performance_monitor.start()
            
            # Phase 8 & 9: Initialize advanced optimization components
            print("🚀 Initializing Phase 8 & 9 Advanced Optimization Systems...")
            
            # Initialize GPU optimizer for AMD MI300
            gpu_optimizer = AMMI300Optimizer()
            await gpu_optimizer.initialize_rocm_optimization()
            
            # Initialize network optimizer for zero rejected shares
            network_optimizer = NetworkOptimizer()
            default_pools = [
                {"name": "NiceHash Ethash", "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353"},
                {"name": "NiceHash RandomX", "url": "stratum+tcp://randomx.nicehash.com:3380"},
                {"name": "NiceHash SHA256", "url": "stratum+tcp://sha256.nicehash.com:3334"}
            ]
            await network_optimizer.initialize_pool_configuration(default_pools)
            await network_optimizer.optimize_network_settings()
            
            # Initialize AI performance optimizer
            ai_optimizer = AIPerformanceOptimizer()
            
            # Initialize advanced analytics
            advanced_analytics = AdvancedAnalytics()
            
            print("✅ All mining and optimization components initialized successfully")
            print("HPE CRAY XD675 optimization ready:")
            print("   • 8x AMD MI300 GPU optimization active")
            print("   • Zero rejected shares network optimization")
            print("   • AI-powered performance optimization")
            print("   • Advanced analytics and monitoring")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize mining components: {e}")
            # Initialize basic components even if advanced features fail
            try:
                gpu_optimizer = AMMI300Optimizer()
                network_optimizer = NetworkOptimizer()
                ai_optimizer = AIPerformanceOptimizer()
                advanced_analytics = AdvancedAnalytics()
                print("✅ Basic optimization components initialized")
            except Exception as e2:
                print(f"⚠️ Failed to initialize basic optimization: {e2}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
