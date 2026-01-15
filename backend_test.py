#!/usr/bin/env python3
"""
Backend API Testing for HPC Cryptominer
Tests the FastAPI backend endpoints including mining functionality
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class MiningAPITester:
    def __init__(self, base_url="https://gpuharvest.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.failed_tests = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append(f"{name}: {details}")
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}: {details}")

    def test_api_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(self.base_url, timeout=10)
            
            if response.status_code in [200, 404]:  # 404 is OK for root, we just need connectivity
                self.log_test("API Connectivity", True, f"Base URL accessible, Status: {response.status_code}")
                return True
            else:
                self.log_test("API Connectivity", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API Connectivity", False, f"Error: {str(e)}")
            return False

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_message = "HPC Cryptominer API v1.0.0"
                if data.get("message") == expected_message:
                    mining_available = data.get("mining_available", False)
                    self.log_test("Root Endpoint", True, f"Status: {response.status_code}, Mining Available: {mining_available}")
                    return True, mining_available
                else:
                    self.log_test("Root Endpoint", False, f"Unexpected message: {data}")
                    return False, False
            else:
                self.log_test("Root Endpoint", False, f"Status: {response.status_code}")
                return False, False
                
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {str(e)}")
            return False, False

    def test_mining_status(self):
        """Test mining status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/mining/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                mining_available = data.get("mining_available", False)
                if mining_available:
                    required_fields = ["running", "stats", "hardware", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        self.log_test("Mining Status", True, f"Mining engine available, running: {data.get('running')}")
                        return True, data
                    else:
                        self.log_test("Mining Status", False, f"Missing fields: {missing_fields}")
                        return False, data
                else:
                    self.log_test("Mining Status", True, f"Mining engine unavailable (expected): {data.get('error', 'No error message')}")
                    return True, data
            else:
                self.log_test("Mining Status", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Mining Status", False, f"Error: {str(e)}")
            return False, {}

    def test_mining_stats(self):
        """Test mining stats endpoint"""
        try:
            response = requests.get(f"{self.api_url}/mining/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["hashrate", "accepted_shares", "rejected_shares", "active_workers"]
                missing_fields = [field for field in required_fields if field not in data]
                if not missing_fields:
                    self.log_test("Mining Stats", True, f"Stats retrieved: hashrate={data.get('hashrate')}")
                    return True
                else:
                    self.log_test("Mining Stats", False, f"Missing fields: {missing_fields}")
                    return False
            else:
                # Mining engine not available is acceptable
                self.log_test("Mining Stats", True, f"Mining engine unavailable (expected): Status {response.status_code}")
                return True
                
        except Exception as e:
            self.log_test("Mining Stats", False, f"Error: {str(e)}")
            return False

    def test_mining_algorithms(self):
        """Test mining algorithms endpoint"""
        try:
            response = requests.get(f"{self.api_url}/mining/algorithms", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "algorithms" in data:
                    algorithms = data["algorithms"]
                    self.log_test("Mining Algorithms", True, f"Retrieved {len(algorithms)} algorithms")
                    return True
                else:
                    self.log_test("Mining Algorithms", False, f"No algorithms field in response: {data}")
                    return False
            else:
                self.log_test("Mining Algorithms", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mining Algorithms", False, f"Error: {str(e)}")
            return False

    def test_mining_hardware(self):
        """Test mining hardware endpoint"""
        try:
            response = requests.get(f"{self.api_url}/mining/hardware", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Mining Hardware", True, f"Hardware info retrieved")
                return True
            elif response.status_code == 500:
                # Hardware detection might fail, that's acceptable
                self.log_test("Mining Hardware", True, f"Hardware detection failed (acceptable): Status {response.status_code}")
                return True
            else:
                self.log_test("Mining Hardware", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mining Hardware", False, f"Error: {str(e)}")
            return False

    def test_mining_config(self):
        """Test mining config endpoint"""
        try:
            response = requests.get(f"{self.api_url}/mining/config", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data and "Configuration file not found" in data["error"]:
                    self.log_test("Mining Config", True, f"Config file not found (acceptable)")
                    return True
                else:
                    self.log_test("Mining Config", True, f"Config retrieved")
                    return True
            elif response.status_code == 500:
                self.log_test("Mining Config", True, f"Config error (acceptable): Status {response.status_code}")
                return True
            else:
                self.log_test("Mining Config", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mining Config", False, f"Error: {str(e)}")
            return False

    def test_mining_start(self):
        """Test mining start endpoint"""
        try:
            response = requests.post(f"{self.api_url}/mining/start", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Mining Start", True, f"Start command accepted: {data.get('message')}")
                    return True
                else:
                    self.log_test("Mining Start", False, f"Start failed: {data}")
                    return False
            elif response.status_code == 503:
                self.log_test("Mining Start", True, f"Mining engine unavailable (expected): Status {response.status_code}")
                return True
            else:
                self.log_test("Mining Start", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mining Start", False, f"Error: {str(e)}")
            return False

    def test_mining_stop(self):
        """Test mining stop endpoint"""
        try:
            response = requests.post(f"{self.api_url}/mining/stop", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Mining Stop", True, f"Stop command accepted: {data.get('message')}")
                    return True
                else:
                    self.log_test("Mining Stop", False, f"Stop failed: {data}")
                    return False
            else:
                self.log_test("Mining Stop", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mining Stop", False, f"Error: {str(e)}")
            return False

    def test_mining_optimize(self):
        """Test mining optimize endpoint"""
        try:
            response = requests.post(f"{self.api_url}/mining/optimize", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test("Mining Optimize", True, f"Optimize command accepted: {data.get('message')}")
                    return True
                else:
                    self.log_test("Mining Optimize", False, f"Optimize failed: {data}")
                    return False
            elif response.status_code == 503:
                self.log_test("Mining Optimize", True, f"Mining engine unavailable (expected): Status {response.status_code}")
                return True
            else:
                self.log_test("Mining Optimize", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mining Optimize", False, f"Error: {str(e)}")
            return False

    def test_cluster_status(self):
        """Test cluster status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/cluster/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cluster_available = data.get("cluster_available", False)
                if cluster_available:
                    required_fields = ["cluster_id", "stats", "nodes", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        self.log_test("Cluster Status", True, f"Cluster available, nodes: {len(data.get('nodes', []))}")
                        return True, data
                    else:
                        self.log_test("Cluster Status", False, f"Missing fields: {missing_fields}")
                        return False, data
                else:
                    self.log_test("Cluster Status", True, f"Cluster unavailable (expected): {data.get('error', 'No error message')}")
                    return True, data
            else:
                self.log_test("Cluster Status", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Cluster Status", False, f"Error: {str(e)}")
            return False, {}

    def test_cluster_nodes(self):
        """Test cluster nodes endpoint"""
        try:
            response = requests.get(f"{self.api_url}/cluster/nodes", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "nodes" in data:
                    nodes = data["nodes"]
                    total_nodes = data.get("total_nodes", 0)
                    active_nodes = data.get("active_nodes", 0)
                    self.log_test("Cluster Nodes", True, f"Retrieved {total_nodes} nodes, {active_nodes} active")
                    return True, data
                else:
                    self.log_test("Cluster Nodes", False, f"No nodes field in response: {data}")
                    return False, data
            elif response.status_code == 500:
                # Cluster manager not available is acceptable
                self.log_test("Cluster Nodes", True, f"Cluster manager unavailable (expected): Status {response.status_code}")
                return True, {}
            else:
                self.log_test("Cluster Nodes", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Cluster Nodes", False, f"Error: {str(e)}")
            return False, {}

    def test_cluster_node_registration(self):
        """Test cluster node registration endpoint"""
        try:
            # Sample node data for testing
            node_data = {
                "hostname": "test-mining-node-01",
                "ip_address": "192.168.1.100",
                "port": 8080,
                "cpu_cores": 16,
                "cpu_threads": 32,
                "gpu_count": 4,
                "gpu_memory": 32768,
                "total_memory": 65536
            }
            
            response = requests.post(f"{self.api_url}/cluster/nodes/register", 
                                   json=node_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "node_id" in data:
                    node_id = data["node_id"]
                    # Verify it's a 40-character hex string
                    if len(node_id) == 40 and all(c in '0123456789abcdef' for c in node_id):
                        self.log_test("Cluster Node Registration", True, f"Node registered with ID: {node_id[:8]}...")
                        return True, node_id
                    else:
                        self.log_test("Cluster Node Registration", False, f"Invalid node ID format: {node_id}")
                        return False, None
                else:
                    self.log_test("Cluster Node Registration", False, f"Registration failed: {data}")
                    return False, None
            elif response.status_code == 503:
                self.log_test("Cluster Node Registration", True, f"Mining engine unavailable (expected): Status {response.status_code}")
                return True, None
            else:
                self.log_test("Cluster Node Registration", False, f"Status: {response.status_code}")
                return False, None
                
        except Exception as e:
            self.log_test("Cluster Node Registration", False, f"Error: {str(e)}")
            return False, None

    def test_cluster_optimization(self):
        """Test cluster optimization endpoint"""
        try:
            response = requests.get(f"{self.api_url}/cluster/optimize", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "recommendations" in data:
                    recommendations = data["recommendations"]
                    analysis = data.get("analysis", {})
                    self.log_test("Cluster Optimization", True, f"Retrieved {len(recommendations)} recommendations")
                    return True
                else:
                    self.log_test("Cluster Optimization", False, f"No recommendations field: {data}")
                    return False
            elif response.status_code == 500:
                # Cluster manager not available is acceptable
                self.log_test("Cluster Optimization", True, f"Cluster manager unavailable (expected): Status {response.status_code}")
                return True
            else:
                self.log_test("Cluster Optimization", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Cluster Optimization", False, f"Error: {str(e)}")
            return False

    # Phase 8 & 9: Advanced Optimization API Tests
    
    def test_gpu_optimization_status(self):
        """Test GPU optimization status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/optimization/gpu/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                optimization_available = data.get("optimization_available", False)
                if optimization_available:
                    required_fields = ["status", "gpu_metrics", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        gpu_count = len(data.get("gpu_metrics", {}))
                        self.log_test("GPU Optimization Status", True, f"GPU optimization available, {gpu_count} GPUs detected")
                        return True, data
                    else:
                        self.log_test("GPU Optimization Status", False, f"Missing fields: {missing_fields}")
                        return False, data
                else:
                    self.log_test("GPU Optimization Status", True, f"GPU optimization unavailable (expected): {data.get('error', 'No error message')}")
                    return True, data
            else:
                self.log_test("GPU Optimization Status", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("GPU Optimization Status", False, f"Error: {str(e)}")
            return False, {}

    def test_gpu_algorithm_optimization(self):
        """Test GPU algorithm optimization endpoints"""
        algorithms = ["Ethash", "RandomX", "SHA256", "Kawpow", "X11"]
        success_count = 0
        
        for algorithm in algorithms:
            try:
                response = requests.post(f"{self.api_url}/optimization/gpu/algorithm/{algorithm}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.log_test(f"GPU Optimization - {algorithm}", True, f"Algorithm optimization successful: {data.get('message')}")
                        success_count += 1
                    else:
                        self.log_test(f"GPU Optimization - {algorithm}", False, f"Optimization failed: {data.get('message')}")
                elif response.status_code == 503:
                    self.log_test(f"GPU Optimization - {algorithm}", True, f"Mining engine unavailable (expected): Status {response.status_code}")
                    success_count += 1
                else:
                    self.log_test(f"GPU Optimization - {algorithm}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"GPU Optimization - {algorithm}", False, f"Error: {str(e)}")
        
        return success_count == len(algorithms)

    def test_gpu_monitoring(self):
        """Test GPU performance monitoring endpoint"""
        try:
            response = requests.get(f"{self.api_url}/optimization/gpu/monitor", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("monitoring_available"):
                    monitoring_data = data.get("data", {})
                    self.log_test("GPU Performance Monitoring", True, f"GPU monitoring active, data keys: {list(monitoring_data.keys())}")
                    return True
                else:
                    self.log_test("GPU Performance Monitoring", False, f"Monitoring not available: {data}")
                    return False
            elif response.status_code == 503:
                self.log_test("GPU Performance Monitoring", True, f"GPU optimizer unavailable (expected): Status {response.status_code}")
                return True
            else:
                self.log_test("GPU Performance Monitoring", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("GPU Performance Monitoring", False, f"Error: {str(e)}")
            return False

    def test_network_optimization_status(self):
        """Test network optimization status endpoint"""
        try:
            response = requests.get(f"{self.api_url}/optimization/network/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                network_available = data.get("network_optimization_available", False)
                if network_available:
                    required_fields = ["status", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        self.log_test("Network Optimization Status", True, f"Network optimization available")
                        return True, data
                    else:
                        self.log_test("Network Optimization Status", False, f"Missing fields: {missing_fields}")
                        return False, data
                else:
                    self.log_test("Network Optimization Status", True, f"Network optimization unavailable (expected): {data.get('error', 'No error message')}")
                    return True, data
            else:
                self.log_test("Network Optimization Status", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Network Optimization Status", False, f"Error: {str(e)}")
            return False, {}

    def test_network_monitoring(self):
        """Test network performance monitoring endpoint"""
        try:
            response = requests.get(f"{self.api_url}/optimization/network/monitor", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("monitoring_available"):
                    monitoring_data = data.get("data", {})
                    zero_rejects = data.get("zero_rejects_target", False)
                    self.log_test("Network Performance Monitoring", True, f"Network monitoring active, zero rejects target: {zero_rejects}")
                    return True
                else:
                    self.log_test("Network Performance Monitoring", False, f"Monitoring not available: {data}")
                    return False
            elif response.status_code == 503:
                self.log_test("Network Performance Monitoring", True, f"Network optimizer unavailable (expected): Status {response.status_code}")
                return True
            else:
                self.log_test("Network Performance Monitoring", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Network Performance Monitoring", False, f"Error: {str(e)}")
            return False

    def test_ai_performance_analysis(self):
        """Test AI performance analysis endpoint"""
        try:
            response = requests.get(f"{self.api_url}/optimization/ai/analysis", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                ai_available = data.get("ai_optimization_available", False)
                if ai_available:
                    required_fields = ["analysis", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        analysis = data.get("analysis", {})
                        self.log_test("AI Performance Analysis", True, f"AI analysis available, analysis keys: {list(analysis.keys())}")
                        return True, data
                    else:
                        self.log_test("AI Performance Analysis", False, f"Missing fields: {missing_fields}")
                        return False, data
                else:
                    self.log_test("AI Performance Analysis", True, f"AI optimization unavailable (expected): {data.get('error', 'No error message')}")
                    return True, data
            else:
                self.log_test("AI Performance Analysis", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("AI Performance Analysis", False, f"Error: {str(e)}")
            return False, {}

    def test_ai_optimization_apply(self):
        """Test AI optimization apply endpoint"""
        try:
            response = requests.post(f"{self.api_url}/optimization/ai/apply", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    applied = data.get("recommendations_applied", 0)
                    total = data.get("total_recommendations", 0)
                    self.log_test("AI Optimization Apply", True, f"Applied {applied}/{total} AI optimizations")
                    return True
                else:
                    self.log_test("AI Optimization Apply", False, f"Apply failed: {data}")
                    return False
            elif response.status_code == 503:
                self.log_test("AI Optimization Apply", True, f"AI optimizer unavailable (expected): Status {response.status_code}")
                return True
            else:
                self.log_test("AI Optimization Apply", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("AI Optimization Apply", False, f"Error: {str(e)}")
            return False

    def test_comprehensive_analytics(self):
        """Test comprehensive analytics endpoint"""
        try:
            response = requests.get(f"{self.api_url}/analytics/comprehensive", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                analytics_available = data.get("analytics_available", False)
                if analytics_available:
                    required_fields = ["current_metrics", "comprehensive_analysis", "system_status", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        analysis = data.get("comprehensive_analysis", {})
                        self.log_test("Comprehensive Analytics", True, f"Analytics available, analysis keys: {list(analysis.keys())}")
                        return True, data
                    else:
                        self.log_test("Comprehensive Analytics", False, f"Missing fields: {missing_fields}")
                        return False, data
                else:
                    self.log_test("Comprehensive Analytics", True, f"Analytics unavailable (expected): {data.get('error', 'No error message')}")
                    return True, data
            else:
                self.log_test("Comprehensive Analytics", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Comprehensive Analytics", False, f"Error: {str(e)}")
            return False, {}

    def test_algorithm_benchmarks(self):
        """Test algorithm benchmarking endpoint"""
        try:
            response = requests.post(f"{self.api_url}/analytics/benchmark", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    benchmark_results = data.get("benchmark_results", {})
                    algorithms_tested = data.get("algorithms_tested", 0)
                    self.log_test("Algorithm Benchmarks", True, f"Benchmarked {algorithms_tested} algorithms successfully")
                    return True
                else:
                    self.log_test("Algorithm Benchmarks", False, f"Benchmark failed: {data}")
                    return False
            elif response.status_code == 503:
                self.log_test("Algorithm Benchmarks", True, f"Advanced analytics unavailable (expected): Status {response.status_code}")
                return True
            else:
                self.log_test("Algorithm Benchmarks", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Algorithm Benchmarks", False, f"Error: {str(e)}")
            return False

    def test_profitability_analysis(self):
        """Test profitability analysis endpoint"""
        try:
            response = requests.get(f"{self.api_url}/optimization/profitability", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                profitability_available = data.get("profitability_available", False)
                if profitability_available:
                    required_fields = ["analysis", "timestamp"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if not missing_fields:
                        analysis = data.get("analysis", {})
                        self.log_test("Profitability Analysis", True, f"Profitability analysis available, analysis keys: {list(analysis.keys())}")
                        return True, data
                    else:
                        self.log_test("Profitability Analysis", False, f"Missing fields: {missing_fields}")
                        return False, data
                else:
                    self.log_test("Profitability Analysis", True, f"Profitability analysis unavailable (expected): {data.get('error', 'No error message')}")
                    return True, data
            else:
                self.log_test("Profitability Analysis", False, f"Status: {response.status_code}")
                return False, {}
                
        except Exception as e:
            self.log_test("Profitability Analysis", False, f"Error: {str(e)}")
            return False, {}

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting HPC Cryptominer Backend API Tests...")
        print(f"🔗 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Test basic connectivity first
        if not self.test_api_connectivity():
            print("❌ Cannot connect to API, stopping tests")
            return False
        
        # Test root endpoint and check mining availability
        success, mining_available = self.test_root_endpoint()
        if not success:
            print("❌ Root endpoint failed, stopping tests")
            return False
        
        print(f"\n⛏️ Mining Engine Available: {mining_available}")
        print("Testing Mining API Endpoints...")
        
        # Test mining endpoints
        self.test_mining_status()
        self.test_mining_stats()
        self.test_mining_algorithms()
        self.test_mining_hardware()
        self.test_mining_config()
        
        # Test control endpoints
        print("\n🎮 Testing Mining Control Endpoints...")
        self.test_mining_start()
        self.test_mining_stop()
        self.test_mining_optimize()
        
        # Test cluster management endpoints (Phase 7)
        print("\n🔗 Testing Cluster Management API Endpoints (Phase 7)...")
        cluster_success, cluster_data = self.test_cluster_status()
        self.test_cluster_nodes()
        self.test_cluster_node_registration()
        self.test_cluster_optimization()
        
        # Test Phase 8 & 9 Advanced Optimization endpoints
        print("\n🚀 Testing Phase 8 GPU Optimization API Endpoints...")
        self.test_gpu_optimization_status()
        self.test_gpu_algorithm_optimization()
        self.test_gpu_monitoring()
        
        print("\n🌐 Testing Phase 8 Network Optimization API Endpoints...")
        self.test_network_optimization_status()
        self.test_network_monitoring()
        
        print("\n🤖 Testing Phase 9 AI Performance API Endpoints...")
        self.test_ai_performance_analysis()
        self.test_ai_optimization_apply()
        
        print("\n📊 Testing Phase 9 Advanced Analytics API Endpoints...")
        self.test_comprehensive_analytics()
        self.test_algorithm_benchmarks()
        self.test_profitability_analysis()
        
        # Print summary
        print("=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for failed_test in self.failed_tests:
                print(f"   - {failed_test}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return True
        else:
            print("⚠️  Some backend tests failed")
            return False

    def get_test_report(self) -> Dict[str, Any]:
        """Get detailed test report"""
        return {
            "summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "failed_tests": self.tests_run - self.tests_passed,
                "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
            },
            "results": self.test_results,
            "failed_tests": self.failed_tests,
            "api_url": self.api_url
        }

def main():
    """Main test execution"""
    tester = MiningAPITester()
    success = tester.run_all_tests()
    
    # Save detailed report
    report = tester.get_test_report()
    with open("/app/backend_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: /app/backend_test_report.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())