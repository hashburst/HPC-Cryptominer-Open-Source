#!/usr/bin/env python3
"""
HPC Cryptominer Service Management Script
Phase 7: System Services and Orchestration Configuration
"""

import argparse
import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import HPCMiner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceManager:
    """Manages HPC Cryptominer services"""
    
    def __init__(self):
        self.available_modes = ["standalone", "cluster", "orchestrator", "dashboard", "monitor"]
        self.service_status = {}
    
    def start_service(self, mode: str, config_path: str = None) -> bool:
        """Start a specific service mode"""
        if mode not in self.available_modes:
            logger.error(f"Invalid mode: {mode}. Available modes: {self.available_modes}")
            return False
        
        try:
            logger.info(f"Starting HPC Miner in {mode} mode...")
            
            # Create and configure miner instance
            miner = HPCMiner(config_path)
            
            # Start the appropriate mode
            if mode == "standalone":
                asyncio.run(self._run_standalone(miner))
            elif mode == "cluster":
                asyncio.run(self._run_cluster(miner))
            elif mode == "orchestrator":
                asyncio.run(self._run_orchestrator(miner))
            elif mode == "dashboard":
                asyncio.run(self._run_dashboard(miner))
            elif mode == "monitor":
                asyncio.run(self._run_monitor(miner))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {mode} mode: {e}")
            return False
    
    async def _run_standalone(self, miner: HPCMiner):
        """Run standalone mining mode"""
        await miner.start_standalone_mode()
        await miner.run_main_loop()
    
    async def _run_cluster(self, miner: HPCMiner):
        """Run cluster master mode"""
        await miner.start_cluster_mode()
        await miner.run_main_loop()
    
    async def _run_orchestrator(self, miner: HPCMiner):
        """Run orchestrator-only mode"""
        await miner.start_orchestrator_mode()
        await miner.run_main_loop()
    
    async def _run_dashboard(self, miner: HPCMiner):
        """Run dashboard-only mode"""
        await miner.start_dashboard_mode()
        await miner.run_main_loop()
    
    async def _run_monitor(self, miner: HPCMiner):
        """Run monitoring-only mode"""
        await miner.start_monitor_mode()
        await miner.run_main_loop()
    
    def stop_service(self, mode: str) -> bool:
        """Stop a specific service mode"""
        try:
            # This would typically send a stop signal to the running process
            logger.info(f"Stopping {mode} service...")
            
            # For now, we'll use a simple approach
            # In production, this would involve process management
            subprocess.run(["pkill", "-f", f"main.py --mode={mode}"], check=False)
            
            logger.info(f"{mode} service stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop {mode} service: {e}")
            return False
    
    def restart_service(self, mode: str, config_path: str = None) -> bool:
        """Restart a specific service mode"""
        logger.info(f"Restarting {mode} service...")
        
        if self.stop_service(mode):
            time.sleep(2)  # Wait for clean shutdown
            return self.start_service(mode, config_path)
        
        return False
    
    def get_service_status(self) -> dict:
        """Get status of all services"""
        status = {}
        
        for mode in self.available_modes:
            try:
                # Check if process is running
                result = subprocess.run(
                    ["pgrep", "-f", f"main.py --mode={mode}"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    status[mode] = {
                        "running": True,
                        "pid": result.stdout.strip().split('\n')[0]
                    }
                else:
                    status[mode] = {"running": False, "pid": None}
                    
            except Exception as e:
                status[mode] = {"running": False, "error": str(e)}
        
        return status
    
    def list_services(self):
        """List all available services and their status"""
        print("\n HPC Cryptominer Services")
        print("=" * 50)
        
        status = self.get_service_status()
        
        for mode in self.available_modes:
            service_status = status.get(mode, {})
            running = service_status.get("running", False)
            pid = service_status.get("pid", "N/A")
            
            status_icon = "✅" if running else "❌"
            status_text = "RUNNING" if running else "STOPPED"
            
            print(f"{status_icon} {mode.upper():15} {status_text:10} PID: {pid}")
        
        print()
    
    def setup_systemd_services(self):
        """Setup systemd service files for production deployment"""
        logger.info("Setting up systemd service files...")
        
        service_template = """[Unit]
Description=HPC Cryptominer - {mode} Mode
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/app
Environment=PYTHONPATH=/app
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 /app/main.py --mode={mode} --log-level=INFO
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        for mode in self.available_modes:
            service_content = service_template.format(mode=mode)
            service_file = f"/etc/systemd/system/hpc-miner-{mode}.service"
            
            try:
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                logger.info(f"Created systemd service: {service_file}")
                
            except Exception as e:
                logger.error(f"Failed to create systemd service for {mode}: {e}")
        
        # Reload systemd
        try:
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            logger.info("Systemd daemon reloaded")
        except Exception as e:
            logger.error(f"Failed to reload systemd daemon: {e}")

def main():
    parser = argparse.ArgumentParser(description="HPC Cryptominer Service Manager")
    parser.add_argument("action", 
                       choices=["start", "stop", "restart", "status", "list", "setup-systemd"],
                       help="Action to perform")
    parser.add_argument("--mode", 
                       choices=["standalone", "cluster", "orchestrator", "dashboard", "monitor", "all"],
                       help="Service mode to manage")
    parser.add_argument("--config", 
                       default="/app/config/mining_config.json",
                       help="Configuration file path")
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    if args.action == "list":
        manager.list_services()
        return
    
    if args.action == "setup-systemd":
        manager.setup_systemd_services()
        return
    
    if args.action == "status":
        status = manager.get_service_status()
        print("\n Service Status:")
        for mode, info in status.items():
            running = "RUNNING" if info.get("running") else "STOPPED"
            pid = info.get("pid", "N/A")
            print(f"  {mode}: {running} (PID: {pid})")
        return
    
    if not args.mode:
        logger.error("--mode is required for start, stop, and restart actions")
        return
    
    if args.mode == "all":
        modes = manager.available_modes
    else:
        modes = [args.mode]
    
    success = True
    for mode in modes:
        if args.action == "start":
            success &= manager.start_service(mode, args.config)
        elif args.action == "stop":
            success &= manager.stop_service(mode)
        elif args.action == "restart":
            success &= manager.restart_service(mode, args.config)
    
    if success:
        logger.info(f"Successfully {args.action}ed {args.mode} service(s)")
    else:
        logger.error(f"Failed to {args.action} {args.mode} service(s)")
        sys.exit(1)

if __name__ == "__main__":
    main()