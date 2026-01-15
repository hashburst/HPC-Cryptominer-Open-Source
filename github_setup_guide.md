# GitHub Repository Setup Guide for HashBurst Developers Team, Developers Community and Miners Communities.

Complete guide to set up HPC Cryptominer (Open Source Version) GitHub repository for deployment on HPE CRAY XD675.

## Step 1: Create GitHub Repository

### 1.1 Create New Repository
1. Go to [GitHub.com](https://github.com) and sign in
2. Click "New Repository" (green button)
3. Repository name: `hpc-cryptominer` (or your preferred name)
4. Description: "Advanced HPC Cryptominer with AI Optimization for AMD MI300"
5. Set to **Public** (or Private if you prefer)
6. Initialize with README
7. Add `.gitignore` template: **Python**
8. License: **MIT License** (recommended)
9. Click "Create Repository"

### 1.2 Repository Structure
Your repository should have this structure:
```
hpc-cryptominer/
├── README.md
├── .gitignore
├── LICENSE
├── requirements.txt
├── main.py
├── deploy_hpc_cray.sh
├── backend/
│   ├── server.py
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── src/
│   └── public/
├── mining_engine/
│   ├── __init__.py
│   ├── core.py
│   ├── algorithms.py
│   ├── hardware.py
│   └── optimizer.py
├── miners/
│   └── miner_integration.py
├── config/
│   ├── hpc_cray_xd675_config.json
│   └── mining_config_template.json
├── containers/
│   ├── docker/
│   └── podman/
└── docs/
    ├── deployment_guide.md
    └── pool_setup.md
```

## Step 2: Upload Files to Repository

### 2.1 Clone Repository Locally
```bash
# Clone your new repository
git clone https://github.com/YOUR_USERNAME/hpc-cryptominer.git
cd hpc-cryptominer
```

### 2.2 Copy Files from Current Project
```bash
# If you have access to the current project files:
# Copy all project files to your repository
cp -r /app/* ./

# Ensure proper permissions
chmod +x deploy_hpc_cray.sh
chmod +x containers/docker/entrypoint.sh
chmod +x containers/podman/entrypoint.sh
```

### 2.3 Create Essential Files

**requirements.txt** (main project):
```bash
cat > requirements.txt << 'EOF'
fastapi==0.110.1
uvicorn==0.25.0
aiohttp>=3.8.0
websockets>=11.0
numpy>=1.24.0
scipy>=1.10.0
psutil>=5.9.0
scikit-learn>=1.2.0
cryptography>=42.0.8
requests>=2.31.0
prometheus-client>=0.16.0
pymongo==4.5.0
motor==3.3.1
python-dotenv>=1.0.1
pydantic>=2.6.4
typer>=0.9.0
click>=8.1.0
pyyaml>=6.0
passlib>=1.7.4
pyjwt>=2.10.1
python-jose>=3.3.0
boto3>=1.34.129
pandas>=2.2.0
EOF
```

### 2.4 Commit and Push Files
```bash
# Add all files
git add .

# Commit changes
git commit -m "Initial HPC Cryptominer implementation with real miner integration"

# Push to GitHub
git push origin main
```

## Step 3: Update Deployment Script

Update the `deploy_hpc_cray.sh` script to use your GitHub repository URL:

```bash
# Edit the deployment script
nano deploy_hpc_cray.sh

# Find this line:
REPO_URL="https://github.com/YOUR_USERNAME/hpc-cryptominer.git"

# Replace YOUR_USERNAME with your actual GitHub username
REPO_URL="https://github.com/yourusername/hpc-cryptominer.git"
```

## Step 4: Deployment on HPE CRAY XD675

### 4.1 Direct Download and Deploy
```bash
# SSH to your HPE CRAY XD675
ssh user@your-hpc-system

# Download deployment script directly
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/hpc-cryptominer/main/deploy_hpc_cray.sh

# Make executable
chmod +x deploy_hpc_cray.sh

# Run deployment
sudo ./deploy_hpc_cray.sh
```

### 4.2 Clone and Deploy Method
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/hpc-cryptominer.git
cd hpc-cryptominer

# Run deployment
sudo ./deploy_hpc_cray.sh
```

### 4.3 What the Deployment Script Does

1. **System Preparation**:
   - Updates Ubuntu 24.04
   - Installs dependencies
   - Configures system optimizations

2. **ROCm Installation**:
   - Installs ROCm drivers for MI300
   - Configures GPU environment
   - Sets up device permissions

3. **Mining Software**:
   - Downloads and installs real miners:
     - lolMiner (for Ethash, Kawpow)
     - TeamRedMiner (for Ethash, Kawpow, X11)
     - SRBMiner-MULTI (for RandomX, multi-algorithm)
     - XMRig (for RandomX CPU mining)

4. **Framework Setup**:
   - Installs Python environment
   - Sets up web dashboard
   - Configures monitoring
   - Creates system services

5. **Configuration**:
   - Creates optimized configs for MI300
   - Sets up pool configurations
   - Configures wallet templates

## Step 5: Configuration After Deployment

### 5.1 Configure Wallet Addresses
```bash
# Edit wallet addresses
sudo nano /etc/hpc-miner/wallet_addresses.txt

# Add your real addresses:
BITCOIN_ADDRESS=bc1qyourbitcoinaddresshere...
ETC_ADDRESS=0xYourEthereumClassicAddressHere...
RVN_ADDRESS=RYourRavencoinAddressHere...
XMR_ADDRESS=4YourMoneroAddressHere...
```

### 5.2 Update Mining Configuration
```bash
# Edit main configuration
sudo nano /etc/hpc-miner/mining_config.json

# Key settings to update:
{
  "pools": {
    "nicehash_ethash": {
      "username": "YOUR_BITCOIN_ADDRESS_FROM_ABOVE"
    }
  }
}
```

### 5.3 Start Mining
```bash
# Start all services
sudo supervisorctl start all

# Check status
sudo supervisorctl status

# View logs
tail -f /var/log/hpc-miner/mining-engine.log
```

## Step 6: Monitor Performance

### 6.1 Web Dashboard
- Open: `http://your-server-ip`
- View real-time statistics
- Control mining operations

### 6.2 GPU Monitoring
```bash
# Check GPU status
rocm-smi

# Monitor temperatures
watch -n 1 'rocm-smi --showtemp'

# Check hashrates
curl http://localhost:8080/api/mining/stats
```

### 6.3 Expected Performance
With 8x MI300 GPUs, you should see:
- **Ethash**: ~20 GH/s total
- **Kawpow**: ~960 MH/s total  
- **RandomX**: ~120 KH/s total
- **Temperatures**: 80-90°C per GPU
- **Power**: ~350W per GPU

## Step 7: Optimization Tips

### 7.1 Algorithm Selection
- **Start with Ethash** - highest profit potential
- **Enable auto-switching** for profitability optimization
- **Monitor temperatures** - keep under 90°C

### 7.2 Pool Configuration
- **NiceHash**: Easiest setup, good profitability
- **Multi-pool**: Compare different pools
- **Auto-switching**: Let AI select optimal pools

### 7.3 Performance Tuning
```bash
# Reduce intensity if too hot
# Edit: /etc/hpc-miner/mining_config.json
"gpu_intensity": 85  # Reduce from 95

# Monitor and adjust
sudo supervisorctl restart hpc-mining-engine
```

## Troubleshooting

### Common Issues:

1. **GitHub Repository Not Found**:
   ```bash
   # Make sure repository is public or you have access
   git clone https://github.com/yourusername/hpc-cryptominer.git
   ```

2. **ROCm Installation Fails**:
   ```bash
   # Check Ubuntu version
   lsb_release -a
   
   # Should be Ubuntu 24.04
   ```

3. **Miners Not Starting**:
   ```bash
   # Check if miners installed
   ls -la /opt/miners/
   
   # Check logs
   tail -f /var/log/hpc-miner/mining-engine.log
   ```

4. **Low Hashrate**:
   ```bash
   # Check GPU temperatures
   rocm-smi --showtemp
   
   # Check GPU clocks
   rocm-smi --showclocks
   ```

## Support

For deployment issues:
1. Check logs in `/var/log/hpc-miner/`
2. Verify GPU status with `rocm-smi`
3. Test pool connectivity: `telnet pool-address port`
4. Create GitHub issue with error details

This setup will give to all developers and miners a production-ready mining system that integrates real mining software with intelligent management and monitoring.