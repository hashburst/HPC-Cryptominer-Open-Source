"""
Advanced Performance Analytics and Monitoring - DEFINITIVE PRODUCTION VERSION
Phase 9: Performance Optimization - High Verbose Analytics

This module integrates real-time hardware data, market prices, and advanced
statistical regression to maximize profitability for the HashBurst project.
"""

import asyncio
import json
import logging
import time
import statistics
import subprocess
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import numpy as np
from datetime import datetime
import aiohttp

# --- LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HashBurst.Analytics.Pro")

@dataclass
class PerformanceMetrics:
    timestamp: float
    algorithm: str
    total_hashrate: float
    per_gpu_hashrate: List[float]
    hashrate_stability: float
    effective_hashrate: float
    total_power: float
    per_gpu_power: List[float]
    power_efficiency: float
    power_stability: float
    temperatures: List[float]
    average_temperature: float
    max_temperature: float
    thermal_throttling_detected: bool
    pool_latency: float
    share_acceptance_rate: float
    rejected_shares: int
    accepted_shares: int
    network_errors: int
    cpu_usage: float
    memory_usage: float
    gpu_memory_usage: List[float]
    estimated_hourly_profit: float
    power_cost_hourly: float
    net_profit_hourly: float

@dataclass
class BenchmarkResult:
    algorithm: str
    duration_seconds: int
    average_hashrate: float
    peak_hashrate: float
    min_hashrate: float
    power_consumption: float
    efficiency: float
    temperature_impact: float
    stability_score: float
    profitability_score: float

@dataclass
class PerformanceAlert:
    alert_type: str
    severity: str  # critical, high, medium, low
    message: str
    metrics: Dict[str, Any]
    timestamp: float
    recommendation: str

class AdvancedAnalytics:
    """Advanced monitoring and predictive analytics system for production mining"""
    
    def __init__(self, electricity_rate: float = 0.12, target_coin: str = "BTC"):
        # Data Persistence (24h history at 5s intervals)
        self.metrics_history = deque(maxlen=17280)
        self.performance_alerts = deque(maxlen=1000)
        self.profit_history = deque(maxlen=1440)
        
        # Configuration
        self.electricity_rate = electricity_rate
        self.target_coin = target_coin
        self.market_cache = {"price": 0.0, "difficulty": 1.0, "last_update": 0}
        
        # Thresholds
        self.alert_thresholds = {
            "critical_temperature": 82,
            "high_rejection_rate": 0.02,
            "low_efficiency_mh_w": 0.25
        }
        
        logger.info(f"Analytics System Initialized. Target: {target_coin} | Rate: ${electricity_rate}/kWh")

    # --- MARKET DATA ENGINE ---
    async def _update_market_data(self):
        """Fetch real-time price and network difficulty"""
        now = time.time()
        if now - self.market_cache["last_update"] < 600: # 10 min cache
            return

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={self.target_coin}&tsyms=USD"
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw = data['RAW'][self.target_coin]['USD']
                        self.market_cache.update({
                            "price": raw['PRICE'],
                            "difficulty": raw.get('DIFFICULTY', 1.0),
                            "last_update": now
                        })
                        logger.info(f"Market Update: {self.target_coin} @ ${raw['PRICE']}")
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")

    # --- METRICS COLLECTION ENGINE ---
    async def collect_metrics(self, gpu_data: Dict, net_data: Dict, sys_data: Dict) -> Optional[PerformanceMetrics]:
        """Processes raw hardware/network data into structured analytics"""
        try:
            await self._update_market_data()
            
            # Hardware Stats
            hr_list = [g.get("hashrate", 0) for g in gpu_data.values()]
            pwr_list = [g.get("power_draw", 0) for g in gpu_data.values()]
            temp_list = [g.get("temperature", 0) for g in gpu_data.values()]
            
            total_hr = sum(hr_list)
            total_pwr = sum(pwr_list)
            
            # Profitability calculations
            pwr_cost_h = (total_pwr / 1000) * self.electricity_rate
            # Dynamic formula: proportional to hashrate vs difficulty
            algo_factor = 0.00001 # Adjustable based on specific coin emission
            rev_h = (total_hr * algo_factor / max(self.market_cache["difficulty"], 1)) * self.market_cache["price"]
            
            # Networking
            acc = net_data.get("accepted_shares_total", 0)
            rej = net_data.get("rejected_shares_total", 0)
            acc_rate = acc / max((acc + rej), 1)

            metrics = PerformanceMetrics(
                timestamp=time.time(),
                algorithm=sys_data.get("current_algorithm", "Autolykos2"),
                total_hashrate=total_hr,
                per_gpu_hashrate=hr_list,
                hashrate_stability=self._calculate_stability(hr_list),
                effective_hashrate=total_hr * acc_rate,
                total_power=total_pwr,
                per_gpu_power=pwr_list,
                power_efficiency=total_hr / max(total_pwr, 1),
                power_stability=self._calculate_stability(pwr_list),
                temperatures=temp_list,
                average_temperature=statistics.mean(temp_list) if temp_list else 0,
                max_temperature=max(temp_list) if temp_list else 0,
                thermal_throttling_detected=any(t >= self.alert_thresholds["critical_temperature"] for t in temp_list),
                pool_latency=net_data.get("total_latency", 0),
                share_acceptance_rate=acc_rate,
                rejected_shares=rej,
                accepted_shares=acc,
                network_errors=net_data.get("network_errors", 0),
                cpu_usage=sys_data.get("cpu_usage", 0),
                memory_usage=sys_data.get("memory_usage", 0),
                gpu_memory_usage=[g.get("memory_used", 0) for g in gpu_data.values()],
                estimated_hourly_profit=rev_h,
                power_cost_hourly=pwr_cost_h,
                net_profit_hourly=rev_h - pwr_cost_h
            )
            
            self.metrics_history.append(metrics)
            self._check_and_trigger_alerts(metrics)
            return metrics

        except Exception as e:
            logger.error(f"Comprehensive metrics collection failed: {e}")
            return None

    # --- ANALYTICS & REGRESSION ENGINE ---
    def _calculate_stability(self, values: List[float]) -> float:
        if len(values) < 2 or sum(values) == 0: return 100.0
        return max(0, 100 * (1 - (statistics.stdev(values) / statistics.mean(values))))

    def _calculate_trend(self, values: List[float]) -> str:
        """Uses linear regression to determine performance direction"""
        if len(values) < 10: return "stable"
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        if slope > 0.005: return "improving"
        if slope < -0.005: return "declining"
        return "stable"

    async def analyze_regression(self) -> Dict:
        """Detects if performance is dropping compared to the first hour of mining"""
        if len(self.metrics_history) < 120: return {"status": "warming_up"}
        
        baseline = list(self.metrics_history)[:60] # First 5 mins as baseline
        current = list(self.metrics_history)[-60:] # Last 5 mins
        
        b_hr = statistics.mean([m.total_hashrate for m in baseline])
        c_hr = statistics.mean([m.total_hashrate for m in current])
        
        drop = (b_hr - c_hr) / b_hr if b_hr > 0 else 0
        return {
            "regression_detected": drop > 0.05,
            "drop_percentage": drop * 100,
            "status": "warning" if drop > 0.05 else "healthy"
        }

    # --- ALERT ENGINE ---
    def _check_and_trigger_alerts(self, m: PerformanceMetrics):
        if m.max_temperature > self.alert_thresholds["critical_temperature"]:
            self.performance_alerts.append(PerformanceAlert(
                "THERMAL", "CRITICAL", f"Temp reached {m.max_temperature}C", 
                {"temp": m.max_temperature}, time.time(), "Check fans / Lower Power Limit"
            ))
        
        if (1 - m.share_acceptance_rate) > self.alert_thresholds["high_rejection_rate"]:
            self.performance_alerts.append(PerformanceAlert(
                "NETWORK", "HIGH", "Rejected shares exceeding 2%", 
                {"rate": 1-m.share_acceptance_rate}, time.time(), "Change mining pool"
            ))

    # --- BENCHMARK ENGINE (REAL-TIME) ---
    async def run_live_benchmark(self, algo_name: str, duration_sec: int = 60) -> BenchmarkResult:
        """Monitors actual hardware performance during a live run"""
        logger.info(f"BENCHMARK START: {algo_name} for {duration_sec}s")
        start_ts = time.time()
        samples = []
        
        while time.time() - start_ts < duration_sec:
            if self.metrics_history:
                samples.append(self.metrics_history[-1])
            await asyncio.sleep(2)
            
        if not samples:
            return None

        avg_hr = statistics.mean([s.total_hashrate for s in samples])
        avg_pwr = statistics.mean([s.total_power for s in samples])

        return BenchmarkResult(
            algorithm=algo_name,
            duration_seconds=duration_sec,
            average_hashrate=avg_hr,
            peak_hashrate=max([s.total_hashrate for s in samples]),
            min_hashrate=min([s.total_hashrate for s in samples]),
            power_consumption=avg_pwr,
            efficiency=avg_hr / max(avg_pwr, 1),
            temperature_impact=max([s.max_temperature for s in samples]) - min([s.temperatures[0] for s in samples]),
            stability_score=self._calculate_stability([s.total_hashrate for s in samples]),
            profitability_score=avg_hr * (self.market_cache["price"] / self.market_cache["difficulty"])
        )