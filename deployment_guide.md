# 🚀 HPE CRAY XD675 Deployment Guide

Complete deployment guide for your HPE CRAY XD675 with 8x AMD MI300 GPUs running Ubuntu 24.04.

## Pre-Deployment Checklist

### System Requirements Verification
- HPE CRAY XD675 with 8x AMD MI300 GPUs
- Ubuntu 24.04 LTS
- Minimum 256GB RAM (recommended for RandomX)
- 1TB+ NVMe storage
- Stable internet connection (>100 Mbps)
- Adequate cooling (GPUs will run at 80-90°C)
- Power supply capacity (3.5kW+ recommended)

### Network Setup
```bash
# Ensure firewall allows mining traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080:8082/tcp
sudo ufw allow 3333:4444/tcp  # Mining pool ports
sudo ufw allow 19999/tcp      # Nanopool
sudo ufw allow 8118/tcp       # F2Pool, ViaBTC
```

## Step-by-Step Deployment

### Step 1: Download and Prepare Deployment

```bash
# Create working directory
mkdir ~/hpc-mining-deployment
cd ~/hpc-mining-deployment

# Download deployment files (replace with your GitHub repo)
git clone https://github.com/YOUR_USERNAME/hpc-cryptominer.git
cd hpc-cryptominer

# Make deployment script executable
chmod +x deploy_hpc_cray.sh
```

### Step 2: Run Automated Deployment

```bash
# Run the deployment script (requires sudo)
sudo ./deploy_hpc_cray.sh
```

The script will:
- Install ROCm drivers for MI300 GPUs
- Set up Python environment with all dependencies
- Configure system optimizations
- Create mining user and directories
- Install and configure services
- Set up monitoring and dashboard

### Step 3: Configure Wallet Addresses

```bash
# Edit wallet addresses
sudo nano /etc/hpc-miner/wallet_addresses.txt
```

**Replace with your actual addresses:**
```bash
# Bitcoin (for NiceHash, ZPool, ZergPool)
BITCOIN_ADDRESS=bc1qyourbitcoinaddresshere

# Ethereum Classic (for Nanopool, ViaBTC, 2Miners, F2Pool)  
ETC_ADDRESS=0xYourEthereumClassicAddressHere

# Ravencoin (for Kawpow pools)
RVN_ADDRESS=RYourRavencoinAddressHere

# Monero (for RandomX)
XMR_ADDRESS=4YourMoneroAddressHere
```

### Step 4: Update Mining Configuration

```bash
# Edit mining configuration
sudo nano /etc/hpc-miner/mining_config.json
```

**Key settings to verify:**
```json
{
  "mining": {
    "preferred_algorithm": "Ethash",
    "auto_start": true,
    "auto_switch": true
  },
  "hardware": {
    "detected_gpus": 8,
    "gpu_intensity": 95,
    "temperature_limit": 90
  },
  "pools": {
    "nicehash_ethash": {
      "username": "YOUR_BITCOIN_ADDRESS_HERE"
    }
  }
}
```

### Step 5: Start Mining Services

```bash
# Start all mining services
sudo supervisorctl start all

# Check service status
sudo supervisorctl status

# View real-time logs
tail -f /var/log/hpc-miner/mining-engine.log
```

### Step 6: Verify GPU Detection

```bash
# Check GPU status
rocm-smi

# Expected output: 8x MI300 GPUs detected
# GPU[0]: AMD Instinct MI300X
# GPU[1]: AMD Instinct MI300X
# ... (8 total)
```

### Step 7: Access Web Dashboard

Open your browser and go to:
- **Dashboard**: `http://YOUR_SERVER_IP`
- **API**: `http://YOUR_SERVER_IP/api/mining/status`
- **Metrics**: `http://YOUR_SERVER_IP:8082/metrics`

## Algorithm-Specific Setup

### For Ethash Mining (Recommended Start)
```bash
# Verify Ethash configuration
curl -X POST http://localhost:8080/api/mining/command \
  -H "Content-Type: application/json" \
  -d '{"action": "start", "algorithm": "Ethash"}'
```

**Expected Performance**: 20+ GH/s total (2.5 GH/s per GPU)

### For Multi-Algorithm Auto-Switching
```bash
# Enable profitability switching
sudo nano /etc/hpc-miner/mining_config.json

# Set:
"optimization": {
  "profitability_switching": {
    "enabled": true,
    "check_interval": 300
  }
}
```

## Pool-Specific Configuration

### NiceHash Setup (Easiest Start)
1. Create Bitcoin wallet (recommend hardware wallet)
2. Update configuration:
```json
"nicehash_ethash": {
  "username": "your_bitcoin_address",
  "worker_name": "HPE_CRAY_XD675"
}
```

### Multi-Pool Setup
1. Create accounts on desired pools:
   - NiceHash (Bitcoin address)
   - Nanopool (ETC address)
   - 2Miners (ETC address)
   - ZPool (Bitcoin address)

2. Update pool configurations in `/etc/hpc-miner/mining_config.json`

## Performance Optimization

### GPU Temperature Management
```bash
# Monitor temperatures
watch -n 1 'rocm-smi --showtemp'

# If temperatures > 90°C, reduce intensity:
# Edit mining_config.json: "gpu_intensity": 85
```

### Power Optimization
```bash
# Check power consumption
rocm-smi --showpower

# Adjust power limits if needed:
# rocm-smi --setpoweroverdrive 350 --gpu 0,1,2,3,4,5,6,7
```

### Memory Optimization
```bash
# Check memory usage
rocm-smi --showmeminfo

# For RandomX, ensure huge pages:
echo 3072 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
```

## Troubleshooting

### Common Issues and Solutions

#### 1. GPUs Not Detected
```bash
# Check ROCm installation
rocm-smi --showproductname

# Reinstall ROCm if needed
sudo apt remove rocm-dev rocm-libs
sudo apt install rocm-dev rocm-libs
sudo reboot
```

#### 2. Low Hashrate
```bash
# Check GPU clocks
rocm-smi --showclocks

# Verify temperature throttling
rocm-smi --showtemp

# Check system load
htop
```

#### 3. Pool Connection Issues
```bash
# Test pool connectivity
telnet stratum.nicehash.com 3353

# Check firewall
sudo ufw status

# Verify DNS resolution
nslookup stratum.nicehash.com
```

#### 4. Service Won't Start
```bash
# Check service logs
sudo journalctl -u supervisor -f

# Check supervisor status
sudo supervisorctl status

# Restart services
sudo supervisorctl restart all
```

### Advanced Debugging
```bash
# Full system check
sudo /opt/hpc-cryptominer/venv/bin/python /opt/hpc-cryptominer/main.py --mode=standalone --log-level=DEBUG

# GPU memory check
sudo dmesg | grep -i amd

# ROCm environment check
echo $ROCM_PATH
echo $HIP_VISIBLE_DEVICES
```

## Performance Expectations

### Expected Hashrates (8x MI300):
| Algorithm | Per GPU | Total | Daily Revenue* |
|-----------|---------|-------|---------------|
| Ethash    | 2.5 GH/s| 20 GH/s | $150-200 |
| Kawpow    | 120 MH/s| 960 MH/s| $80-120  |
| RandomX   | 15 KH/s | 120 KH/s| $40-60   |
| X11       | 45 GH/s | 360 GH/s| $100-150 |
| SHA-256   | 8 TH/s  | 64 TH/s | $200-300 |
| Scrypt    | 2.8 GH/s| 22.4 GH/s| $60-90  |
| Yescrypt  | 8.5 KH/s| 68 KH/s | $20-30   |

*Estimates based on current market conditions, actual results may vary.

### Power Consumption:
- **Per GPU**: 300-400W depending on algorithm
- **Total System**: 2.8-3.5kW
- **Daily Power Cost**: $8-15 (at $0.12/kWh)

## Maintenance

### Daily Monitoring
```bash
# Check mining status
sudo supervisorctl status

# View hashrate
curl http://localhost:8080/api/mining/stats

# Check temperatures
rocm-smi --showtemp
```

### Weekly Maintenance  
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Clean logs
sudo find /var/log/hpc-miner -name "*.log" -mtime +7 -delete

# Check disk space
df -h
```

### Monthly Optimization
```bash
# Review profitability
# Update mining configuration based on market conditions
# Check for software updates
# Optimize power and temperature settings
```

## Support Resources

### Log Locations
- Mining Engine: `/var/log/hpc-miner/mining-engine.log`
- Dashboard: `/var/log/hpc-miner/dashboard.log`
- System: `/var/log/syslog`

### Useful Commands
```bash
# Mining status
sudo supervisorctl status

# GPU status  
rocm-smi

# System resources
htop

# Network connections
netstat -tulpn | grep :3353

# Configuration test
python3 -m json.tool /etc/hpc-miner/mining_config.json
```

### Getting Help
1. Check logs first: `/var/log/hpc-miner/`
2. Verify GPU temperatures: `rocm-smi --showtemp`
3. Test pool connectivity: `telnet pool-address port`
4. Review configuration: validate JSON syntax

Note: HPE CRAY XD675 with 8x MI300 GPUs is an exceptional mining system and, with proper configuration, should achieve excellent performance across all supported algorithms.