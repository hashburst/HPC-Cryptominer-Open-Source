"""
Web Dashboard Server
FastAPI-based web interface for monitoring and controlling the mining operations
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

logger = logging.getLogger(__name__)

class DashboardServer:
    """Web dashboard server for mining operations"""
    
    def __init__(self, mining_engine=None, cluster_manager=None, port: int = 8081):
        self.mining_engine = mining_engine
        self.cluster_manager = cluster_manager
        self.port = port
        self.app = FastAPI(title="HPC Cryptominer Dashboard", version="1.0.0")
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Setup routes
        self._setup_routes()
        
        # Server instance
        self.server = None
        
        logger.info(f"Dashboard server initialized on port {port}")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>HPC Cryptominer Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                    .stat-card { background: #2d2d2d; padding: 20px; border-radius: 8px; border-left: 4px solid #00ff88; }
                    .stat-value { font-size: 2em; font-weight: bold; color: #00ff88; }
                    .stat-label { color: #ccc; margin-top: 5px; }
                    .controls { margin: 20px 0; text-align: center; }
                    .btn { background: #00ff88; color: #000; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 0 10px; }
                    .btn:hover { background: #00cc6a; }
                    .status-online { color: #00ff88; }
                    .status-offline { color: #ff4444; }
                    .log-container { background: #000; padding: 15px; border-radius: 4px; height: 300px; overflow-y: auto; font-family: monospace; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>HPC Cryptominer Dashboard</h1>
                        <p>Advanced Multi-Algorithm Mining with AI Optimization</p>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value" id="hashrate">0.00 H/s</div>
                            <div class="stat-label">Total Hashrate</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="accepted-shares">0</div>
                            <div class="stat-label">Accepted Shares</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="rejected-shares">0</div>
                            <div class="stat-label">Rejected Shares</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="active-workers">0</div>
                            <div class="stat-label">Active Workers</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="algorithm">N/A</div>
                            <div class="stat-label">Current Algorithm</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" id="temperature">0°C</div>
                            <div class="stat-label">Max Temperature</div>
                        </div>
                    </div>
                    
                    <div class="controls">
                        <button class="btn" onclick="startMining()">Start Mining</button>
                        <button class="btn" onclick="stopMining()">Stop Mining</button>
                        <button class="btn" onclick="optimizeMining()">AI Optimize</button>
                    </div>
                    
                    <div style="margin-top: 30px;">
                        <h3>Real-time Logs</h3>
                        <div class="log-container" id="logs"></div>
                    </div>
                </div>
                
                <script>
                    const ws = new WebSocket('ws://localhost:8081/ws');
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        updateDashboard(data);
                        addLog(data);
                    };
                    
                    function updateDashboard(data) {
                        if (data.type === 'stats') {
                            document.getElementById('hashrate').textContent = (data.hashrate || 0).toFixed(2) + ' H/s';
                            document.getElementById('accepted-shares').textContent = data.accepted_shares || 0;
                            document.getElementById('rejected-shares').textContent = data.rejected_shares || 0;
                            document.getElementById('active-workers').textContent = data.workers_active || 0;
                            document.getElementById('algorithm').textContent = data.algorithm || 'N/A';
                            
                            const maxTemp = Math.max(...Object.values(data.temperature || {}), 0);
                            document.getElementById('temperature').textContent = maxTemp.toFixed(1) + '°C';
                        }
                    }
                    
                    function addLog(data) {
                        const logsContainer = document.getElementById('logs');
                        const timestamp = new Date().toLocaleTimeString();
                        const logLine = `[${timestamp}] ${JSON.stringify(data)}\\n`;
                        logsContainer.textContent += logLine;
                        logsContainer.scrollTop = logsContainer.scrollHeight;
                    }
                    
                    function startMining() {
                        fetch('/api/start', {method: 'POST'});
                    }
                    
                    function stopMining() {
                        fetch('/api/stop', {method: 'POST'});
                    }
                    
                    function optimizeMining() {
                        fetch('/api/optimize', {method: 'POST'});
                    }
                </script>
            </body>
            </html>
            """)
        
        @self.app.get("/api/status")
        async def get_status():
            """Get mining status"""
            status = {"status": "inactive"}
            
            if self.mining_engine:
                engine_status = self.mining_engine.get_status()
                status.update(engine_status)
            
            if self.cluster_manager:
                cluster_status = self.cluster_manager.get_cluster_status()
                status["cluster"] = cluster_status
            
            return JSONResponse(content=status)
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get mining statistics"""
            stats = {}
            
            if self.mining_engine:
                mining_stats = self.mining_engine.get_stats()
                stats["mining"] = {
                    "hashrate": mining_stats.hashrate,
                    "accepted_shares": mining_stats.accepted_shares,
                    "rejected_shares": mining_stats.rejected_shares,
                    "workers_active": mining_stats.workers_active,
                    "algorithm": mining_stats.algorithm,
                    "temperature": mining_stats.temperature,
                    "uptime": mining_stats.uptime
                }
            
            if self.cluster_manager:
                cluster_stats = self.cluster_manager.get_cluster_status()
                stats["cluster"] = cluster_stats["stats"]
            
            return JSONResponse(content=stats)
        
        @self.app.post("/api/start")
        async def start_mining():
            """Start mining"""
            if self.mining_engine:
                await self.mining_engine.start()
                return {"success": True, "message": "Mining started"}
            return {"success": False, "message": "Mining engine not available"}
        
        @self.app.post("/api/stop")
        async def stop_mining():
            """Stop mining"""
            if self.mining_engine:
                await self.mining_engine.stop()
                return {"success": True, "message": "Mining stopped"}
            return {"success": False, "message": "Mining engine not available"}
        
        @self.app.post("/api/optimize")
        async def optimize_mining():
            """Trigger AI optimization"""
            # This would trigger immediate optimization
            return {"success": True, "message": "AI optimization triggered"}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    # Send periodic updates
                    stats = await self._get_realtime_stats()
                    await websocket.send_text(json.dumps(stats))
                    await asyncio.sleep(5)
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    async def _get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time statistics for WebSocket updates"""
        stats = {
            "type": "stats",
            "timestamp": time.time(),
            "hashrate": 0.0,
            "accepted_shares": 0,
            "rejected_shares": 0,
            "workers_active": 0,
            "algorithm": "",
            "temperature": {},
            "uptime": 0.0
        }
        
        if self.mining_engine:
            mining_stats = self.mining_engine.get_stats()
            stats.update({
                "hashrate": mining_stats.hashrate,
                "accepted_shares": mining_stats.accepted_shares,
                "rejected_shares": mining_stats.rejected_shares,
                "workers_active": mining_stats.workers_active,
                "algorithm": mining_stats.algorithm,
                "temperature": mining_stats.temperature,
                "uptime": mining_stats.uptime
            })
        
        return stats
    
    async def start(self):
        """Start the dashboard server"""
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        
        # Start server in background task
        asyncio.create_task(self.server.serve())
        
        logger.info(f"Dashboard server started on http://0.0.0.0:{self.port}")
    
    async def stop(self):
        """Stop the dashboard server"""
        if self.server:
            self.server.should_exit = True
        
        # Close all WebSocket connections
        for connection in self.active_connections:
            await connection.close()
        
        logger.info("Dashboard server stopped")