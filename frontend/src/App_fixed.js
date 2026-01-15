import { useEffect, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MiningDashboard = () => {
  const [miningStats, setMiningStats] = useState({
    hashrate: 0,
    accepted_shares: 0,
    rejected_shares: 0,
    active_workers: 0,
    algorithm: "N/A",
    running: false,
    temperature: {},
    uptime: 0
  });
  
  const [hardwareInfo, setHardwareInfo] = useState({});
  const [miningAvailable, setMiningAvailable] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Cluster management state
  const [clusterStatus, setClusterStatus] = useState({
    cluster_available: false,
    cluster_id: "",
    stats: {
      total_nodes: 0,
      active_nodes: 0,
      total_hashrate: 0,
      total_power: 0,
      algorithms_running: [],
      efficiency_score: 0
    },
    nodes: {}
  });
  
  const [showClusterView, setShowClusterView] = useState(false);
  
  // Phase 8 & 9: Advanced optimization state
  const [optimizationData, setOptimizationData] = useState({
    gpu_optimization: {
      available: false,
      gpu_metrics: {},
      status: {}
    },
    network_optimization: {
      available: false,
      status: {},
      zero_rejects_achieved: false
    },
    ai_analysis: {
      available: false,
      analysis: {},
      recommendations: []
    },
    analytics: {
      available: false,
      comprehensive_analysis: {},
      current_metrics: {}
    }
  });
  
  const [showAdvancedView, setShowAdvancedView] = useState(false);

  const fetchMiningStatus = async () => {
    try {
      const response = await axios.get(`${API}/mining/status`);
      if (response.data.mining_available) {
        setMiningAvailable(true);
        setMiningStats(response.data.stats || {});
        setHardwareInfo(response.data.hardware || {});
      } else {
        setMiningAvailable(false);
      }
    } catch (error) {
      console.error("Error fetching mining status:", error);
      setMiningAvailable(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchClusterStatus = async () => {
    try {
      const response = await axios.get(`${API}/cluster/status`);
      if (response.data.cluster_available) {
        setClusterStatus(response.data);
      }
    } catch (error) {
      console.error("Error fetching cluster status:", error);
    }
  };

  const fetchAdvancedOptimization = async () => {
    try {
      // Fetch GPU optimization status
      const gpuResponse = await axios.get(`${API}/optimization/gpu/status`);
      
      // Fetch network optimization status
      const networkResponse = await axios.get(`${API}/optimization/network/status`);
      
      // Fetch AI analysis
      const aiResponse = await axios.get(`${API}/optimization/ai/analysis`);
      
      // Fetch comprehensive analytics
      const analyticsResponse = await axios.get(`${API}/analytics/comprehensive`);
      
      setOptimizationData({
        gpu_optimization: gpuResponse.data || { available: false },
        network_optimization: networkResponse.data || { available: false },
        ai_analysis: aiResponse.data || { available: false },
        analytics: analyticsResponse.data || { available: false }
      });
      
    } catch (error) {
      console.error("Error fetching optimization data:", error);
    }
  };

  const startMining = async () => {
    try {
      const response = await axios.post(`${API}/mining/start`);
      console.log("Mining started:", response.data);
      setTimeout(fetchMiningStatus, 2000);
    } catch (error) {
      console.error("Error starting mining:", error);
    }
  };

  const stopMining = async () => {
    try {
      const response = await axios.post(`${API}/mining/stop`);
      console.log("Mining stopped:", response.data);
      setTimeout(fetchMiningStatus, 2000);
    } catch (error) {
      console.error("Error stopping mining:", error);
    }
  };

  const optimizeMining = async () => {
    try {
      const response = await axios.post(`${API}/mining/optimize`);
      console.log("AI optimization triggered:", response.data);
    } catch (error) {
      console.error("Error optimizing mining:", error);
    }
  };

  const applyClusterOptimizations = async () => {
    try {
      const response = await axios.post(`${API}/cluster/optimize/apply`);
      console.log("Cluster optimizations applied:", response.data);
      setTimeout(() => {
        fetchClusterStatus();
        fetchMiningStatus();
      }, 2000);
    } catch (error) {
      console.error("Error applying cluster optimizations:", error);
    }
  };

  const applyAIOptimizations = async () => {
    try {
      const response = await axios.post(`${API}/optimization/ai/apply`);
      console.log("AI optimizations applied:", response.data);
      setTimeout(() => {
        fetchAdvancedOptimization();
        fetchMiningStatus();
      }, 3000);
    } catch (error) {
      console.error("Error applying AI optimizations:", error);
    }
  };

  const optimizeForAlgorithm = async (algorithm) => {
    try {
      const response = await axios.post(`${API}/optimization/gpu/algorithm/${algorithm}`);
      console.log(`Optimized for ${algorithm}:`, response.data);
      setTimeout(fetchAdvancedOptimization, 2000);
    } catch (error) {
      console.error(`Error optimizing for ${algorithm}:`, error);
    }
  };

  const runBenchmarks = async () => {
    try {
      const response = await axios.post(`${API}/analytics/benchmark`);
      console.log("Benchmarks completed:", response.data);
      setTimeout(fetchAdvancedOptimization, 5000);
    } catch (error) {
      console.error("Error running benchmarks:", error);
    }
  };

  useEffect(() => {
    fetchMiningStatus();
    fetchClusterStatus();
    fetchAdvancedOptimization();
    
    // Set up real-time updates
    const interval = setInterval(() => {
      fetchMiningStatus();
      fetchClusterStatus();
      fetchAdvancedOptimization();
    }, 5000); // Update every 5 seconds for real-time monitoring
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading HPC Cryptominer...</p>
      </div>
    );
  }

  // Always show dashboard, even when mining engine is unavailable
  // The cluster management should work independently

  const maxTemp = Math.max(...Object.values(miningStats.temperature || {}), 0);
  const efficiency = miningStats.accepted_shares + miningStats.rejected_shares > 0 
    ? (miningStats.accepted_shares / (miningStats.accepted_shares + miningStats.rejected_shares) * 100)
    : 0;

  // Advanced Optimization View Component
  const AdvancedOptimizationView = () => {
    const gpuOpt = optimizationData.gpu_optimization;
    const netOpt = optimizationData.network_optimization;
    const aiOpt = optimizationData.ai_analysis;
    const analytics = optimizationData.analytics;
    
    return (
      <div className="advanced-optimization-view">
        <div className="optimization-header">
          <h2>🎯 Advanced Performance Optimization</h2>
          <p>Phase 8 & 9: Maximum Efficiency & Profitability for HPE CRAY XD675</p>
        </div>
        
        {/* GPU Optimization Section */}
        <div className="optimization-section">
          <h3>🔧 AMD MI300 GPU Optimization</h3>
          <div className="optimization-cards">
            <div className="opt-card gpu-optimization">
              <h4>8x MI300 Status</h4>
              {gpuOpt.available ? (
                <div>
                  <p><strong>GPUs Active:</strong> {Object.keys(gpuOpt.gpu_metrics || {}).length}</p>
                  <p><strong>Algorithm:</strong> {gpuOpt.status?.current_algorithm || 'N/A'}</p>
                  <p><strong>Target Temp:</strong> {gpuOpt.status?.max_temperature || 75}°C</p>
                  <p><strong>Power Limit:</strong> {gpuOpt.status?.max_power_per_gpu || 300}W per GPU</p>
                </div>
              ) : (
                <p>GPU optimization not available</p>
              )}
            </div>
            
            <div className="opt-card network-optimization">
              <h4>Network Performance</h4>
              {netOpt.available ? (
                <div>
                  <p><strong>Zero Rejects:</strong> 
                    <span className={`status-badge ${netOpt.zero_rejects_achieved ? 'success' : 'warning'}`}>
                      {netOpt.zero_rejects_achieved ? '** Achieved' : '** Working'}
                    </span>
                  </p>
                  <p><strong>Pool Latency:</strong> {netOpt.status?.network_metrics?.total_latency?.toFixed(1) || 'N/A'}ms</p>
                  <p><strong>Optimization Score:</strong> {netOpt.status?.network_metrics?.optimization_score?.toFixed(1) || 'N/A'}/100</p>
                </div>
              ) : (
                <p>Network optimization not available</p>
              )}
            </div>
            
            <div className="opt-card ai-optimization">
              <h4>AI Performance Analysis</h4>
              {aiOpt.available && aiOpt.analysis ? (
                <div>
                  <p><strong>Performance Score:</strong> {aiOpt.analysis.performance_score?.toFixed(1) || 'N/A'}/100</p>
                  <p><strong>Recommendations:</strong> {aiOpt.analysis.ai_recommendations?.length || 0}</p>
                  <p><strong>Best Algorithm:</strong> {aiOpt.analysis.profitability_analysis?.most_profitable || 'N/A'}</p>
                  <p><strong>Profit Improvement:</strong> {aiOpt.analysis.profitability_analysis?.improvement_potential ? 
                    (aiOpt.analysis.profitability_analysis.improvement_potential * 100).toFixed(1) + '%' : 'N/A'}</p>
                </div>
              ) : (
                <p>AI analysis not available</p>
              )}
            </div>
          </div>
        </div>
        
        {/* Real-time Analytics */}
        <div className="optimization-section">
          <h3>High-Verbose Analytics</h3>
          <div className="analytics-grid">
            {analytics.available && analytics.current_metrics ? (
              <>
                <div className="analytics-card">
                  <h4>Power Efficiency</h4>
                  <div className="metric-value">{analytics.current_metrics.power_efficiency?.toFixed(3) || '0.000'} MH/W</div>
                  <div className="metric-label">Target: ≥0.35 MH/W</div>
                </div>
                
                <div className="analytics-card">
                  <h4>Thermal Management</h4>
                  <div className="metric-value">{analytics.current_metrics.max_temperature?.toFixed(1) || '0.0'}°C</div>
                  <div className="metric-label">Target: ≤75°C</div>
                  {analytics.current_metrics.thermal_throttling_detected && (
                    <div className="alert-badge">Throttling Detected</div>
                  )}
                </div>
                
                <div className="analytics-card">
                  <h4>Net Profit/Hour</h4>
                  <div className="metric-value">${analytics.current_metrics.net_profit_hourly?.toFixed(2) || '0.00'}</div>
                  <div className="metric-label">Daily: ${(analytics.current_metrics.net_profit_hourly * 24)?.toFixed(2) || '0.00'}</div>
                </div>
                
                <div className="analytics-card">
                  <h4>Share Performance</h4>
                  <div className="metric-value">{(analytics.current_metrics.share_acceptance_rate * 100)?.toFixed(2) || '0.00'}%</div>
                  <div className="metric-label">Target: ≥99.9%</div>
                </div>
              </>
            ) : (
              <div className="analytics-card">
                <h4>Analytics Loading...</h4>
                <p>Collecting comprehensive metrics</p>
              </div>
            )}
          </div>
        </div>
        
        {/* Optimization Controls */}
        <div className="optimization-controls">
          <div className="control-group">
            <h4>Algorithm Optimization</h4>
            <div className="algorithm-buttons">
              {['Ethash', 'RandomX', 'SHA256', 'Kawpow', 'X11'].map(algo => (
                <button 
                  key={algo}
                  className="btn btn-algorithm"
                  onClick={() => optimizeForAlgorithm(algo)}
                >
                  Optimize for {algo}
                </button>
              ))}
            </div>
          </div>
          
          <div className="control-group">
            <h4>Advanced Actions</h4>
            <div className="advanced-buttons">
              <button className="btn btn-primary" onClick={applyAIOptimizations}>
                Apply AI Optimizations
              </button>
              <button className="btn btn-info" onClick={runBenchmarks}>
                Run Benchmarks
              </button>
              <button className="btn btn-success" onClick={fetchAdvancedOptimization}>
                Refresh Analytics
              </button>
            </div>
          </div>
        </div>
        
        {/* AI Recommendations */}
        {aiOpt.available && aiOpt.analysis?.ai_recommendations?.length > 0 && (
          <div className="recommendations-section">
            <h3>AI Recommendations</h3>
            <div className="recommendations-list">
              {aiOpt.analysis.ai_recommendations.slice(0, 5).map((rec, index) => (
                <div key={index} className={`recommendation-card ${rec.priority}`}>
                  <div className="rec-header">
                    <span className="rec-type">{rec.recommendation_type.replace('_', ' ')}</span>
                    <span className={`priority-badge ${rec.priority}`}>{rec.priority}</span>
                  </div>
                  <div className="rec-improvement">Expected improvement: +{rec.expected_improvement?.toFixed(1)}%</div>
                  <div className="rec-confidence">Confidence: {(rec.confidence * 100)?.toFixed(0)}%</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Cluster View Component
  const ClusterView = () => {
    const nodeEntries = Object.entries(clusterStatus.nodes || {});
    
    return (
      <div className="cluster-view">
        <div className="cluster-header">
          <h2>Cluster Management</h2>
          <div className="cluster-stats-row">
            <div className="cluster-stat">
              <span className="cluster-stat-value">{clusterStatus.stats.total_nodes}</span>
              <span className="cluster-stat-label">Total Nodes</span>
            </div>
            <div className="cluster-stat">
              <span className="cluster-stat-value">{clusterStatus.stats.active_nodes}</span>
              <span className="cluster-stat-label">Active Nodes</span>
            </div>
            <div className="cluster-stat">
              <span className="cluster-stat-value">{(clusterStatus.stats.total_hashrate || 0).toFixed(2)} H/s</span>
              <span className="cluster-stat-label">Cluster Hashrate</span>
            </div>
            <div className="cluster-stat">
              <span className="cluster-stat-value">{(clusterStatus.stats.efficiency_score || 0).toFixed(1)}%</span>
              <span className="cluster-stat-label">Efficiency</span>
            </div>
          </div>
        </div>
        
        <div className="nodes-grid">
          {nodeEntries.length === 0 ? (
            <div className="no-nodes">
              <p>No nodes registered in the cluster</p>
              <small>Nodes will appear here when they connect to the cluster</small>
            </div>
          ) : (
            nodeEntries.map(([nodeId, node]) => (
              <div key={nodeId} className={`node-card ${node.status}`}>
                <div className="node-header">
                  <h4>{node.hostname}</h4>
                  <span className={`node-status ${node.status}`}>{node.status}</span>
                </div>
                <div className="node-info">
                  <p><strong>Node ID:</strong> <code>{nodeId.substring(0, 12)}...</code></p>
                  <p><strong>IP:</strong> {node.ip_address}:{node.port}</p>
                  <p><strong>Hashrate:</strong> {(node.hashrate || 0).toFixed(2)} H/s</p>
                  <p><strong>Algorithm:</strong> {node.assigned_algorithm || 'N/A'}</p>
                  <p><strong>Pool:</strong> {node.assigned_pool || 'N/A'}</p>
                </div>
                <div className="node-hardware">
                  <small>
                    CPU: {node.cpu_cores}C/{node.cpu_threads}T | 
                    GPU: {node.gpu_count} | 
                    RAM: {(node.total_memory / (1024**3)).toFixed(1)}GB
                  </small>
                </div>
                {node.temperature && Object.keys(node.temperature).length > 0 && (
                  <div className="node-temp">
                    Max Temp: {Math.max(...Object.values(node.temperature)).toFixed(1)}°C
                  </div>
                )}
              </div>
            ))
          )}
        </div>
        
        <div className="cluster-actions">
          <button 
            className="btn btn-primary" 
            onClick={applyClusterOptimizations}
          >
            Apply AI Optimizations
          </button>
          <button 
            className="btn btn-info" 
            onClick={fetchClusterStatus}
          >
            Refresh Cluster
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="mining-dashboard">
      <header className="dashboard-header">
        <h1>HPC Cryptominer Dashboard</h1>
        <p>Advanced Multi-Algorithm Mining with AI Optimization</p>
        {!miningAvailable && (
          <div className="mining-unavailable-notice" style={{
            background: 'rgba(255, 193, 7, 0.1)',
            border: '1px solid rgba(255, 193, 7, 0.3)',
            borderRadius: '6px',
            padding: '10px',
            margin: '10px 0',
            color: '#ffc107'
          }}>
            Mining Engine Unavailable - Cluster management and monitoring still available
          </div>
        )}
        <div className="header-controls">
          <div className="status-indicator">
            <span className={`status-dot ${miningStats.running ? 'online' : 'offline'}`}></span>
            {miningStats.running ? 'Mining Active' : 'Mining Stopped'}
          </div>
          <div className="view-toggle">
            <button 
              className={`toggle-btn ${!showClusterView && !showAdvancedView ? 'active' : ''}`}
              onClick={() => {setShowClusterView(false); setShowAdvancedView(false);}}
            >
              Local Mining
            </button>
            <button 
              className={`toggle-btn ${showClusterView && !showAdvancedView ? 'active' : ''}`}
              onClick={() => {setShowClusterView(true); setShowAdvancedView(false);}}
            >
              Cluster View
            </button>
            <button 
              className={`toggle-btn ${showAdvancedView ? 'active' : ''}`}
              onClick={() => {setShowClusterView(false); setShowAdvancedView(true);}}
            >
              Advanced
            </button>
          </div>
        </div>
      </header>

      {showAdvancedView ? (
        <AdvancedOptimizationView />
      ) : showClusterView ? (
        <ClusterView />
      ) : (
        <>
          <div className="stats-grid">
            <div className="stat-card primary">
              <div className="stat-value">{(miningStats.hashrate || 0).toFixed(2)} H/s</div>
              <div className="stat-label">Local Hashrate</div>
            </div>
            
            <div className="stat-card success">
              <div className="stat-value">{miningStats.accepted_shares || 0}</div>
              <div className="stat-label">Accepted Shares</div>
            </div>
            
            <div className="stat-card danger">
              <div className="stat-value">{miningStats.rejected_shares || 0}</div>
              <div className="stat-label">Rejected Shares</div>
            </div>
            
            <div className="stat-card info">
              <div className="stat-value">{miningStats.active_workers || 0}</div>
              <div className="stat-label">Active Workers</div>
            </div>
            
            <div className="stat-card">
              <div className="stat-value">{miningStats.algorithm || 'N/A'}</div>
              <div className="stat-label">Current Algorithm</div>
            </div>
            
            <div className="stat-card warning">
              <div className="stat-value">{maxTemp.toFixed(1)}°C</div>
              <div className="stat-label">Max Temperature</div>
            </div>

            <div className="stat-card success">
              <div className="stat-value">{efficiency.toFixed(1)}%</div>
              <div className="stat-label">Efficiency</div>
            </div>

            <div className="stat-card">
              <div className="stat-value">{Math.floor(miningStats.uptime || 0)}s</div>
              <div className="stat-label">Uptime</div>
            </div>
          </div>

          <div className="controls-section">
            <div className="control-buttons">
              <button 
                className="btn btn-success" 
                onClick={startMining}
                disabled={!miningAvailable || miningStats.running}
              >
                Start Mining
              </button>
              <button 
                className="btn btn-danger" 
                onClick={stopMining}
                disabled={!miningAvailable || !miningStats.running}
              >
                Stop Mining
              </button>
              <button 
                className="btn btn-primary" 
                onClick={optimizeMining}
                disabled={!miningAvailable}
              >
                AI Optimize
              </button>
              <button 
                className="btn btn-info" 
                onClick={fetchMiningStatus}
              >
                Refresh
              </button>
            </div>
          </div>

          {hardwareInfo.cpu && (
            <div className="hardware-section">
              <h3>🔧 Hardware Information</h3>
              <div className="hardware-grid">
                <div className="hardware-card">
                  <h4>CPU</h4>
                  <p><strong>Vendor:</strong> {hardwareInfo.cpu.vendor}</p>
                  <p><strong>Cores:</strong> {hardwareInfo.cpu.cores}</p>
                  <p><strong>Threads:</strong> {hardwareInfo.cpu.threads}</p>
                  <p><strong>Features:</strong> {hardwareInfo.cpu.features?.join(', ') || 'N/A'}</p>
                </div>
                
                {hardwareInfo.gpus && hardwareInfo.gpus.length > 0 && (
                  <div className="hardware-card">
                    <h4>GPUs ({hardwareInfo.gpus.length})</h4>
                    {hardwareInfo.gpus.map((gpu, index) => (
                      <div key={index} className="gpu-info">
                        <p><strong>GPU {index}:</strong> {gpu.vendor} {gpu.name}</p>
                        <p><strong>Memory:</strong> {(gpu.memory_total / (1024**3)).toFixed(1)}GB</p>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="hardware-card">
                  <h4>System Memory</h4>
                  <p><strong>Total:</strong> {(hardwareInfo.memory?.total / (1024**3)).toFixed(1)}GB</p>
                  <p><strong>Available:</strong> {(hardwareInfo.memory?.available / (1024**3)).toFixed(1)}GB</p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      <div className="footer">
        <p>Powered by Advanced AI Optimization | Distributed Mining Ready</p>
        <p><small>Real-time updates every 5 seconds | Phase 8 & 9 Complete</small></p>
      </div>
    </div>
  );
};

const Home = () => {
  return <MiningDashboard />;
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;