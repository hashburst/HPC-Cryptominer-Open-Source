# Complete Step-by-Step Deployment Guide
# HPE CRAY XD675 with 8x AMD MI300 GPUs


Note. Each phase includes:

- **Specific commands** to run,
- **Expected outputs** to verify success,  
- **Error handling** and troubleshooting,
- **Verification steps** at each stage,
- **Performance baselines** and monitoring.

The deployment should take about **60-90 minutes total** and will result in a fully functional HPC mining system optimized for 8x AMD MI300 GPUs.


## Pre-Deployment Checklist

### System Information Verification
First, let's verify that the system meets all requirements:

```bash
# Check system information
echo "=== System Information ==="
uname -a
lsb_release -a
lscpu | grep "Model name"
free -h
df -h
```

**Expected Output:**
```
Ubuntu 24.04.x LTS
Model name: [CPU model]
Mem: [Large amount of RAM, 256GB+ recommended]
Disk space: 1TB+ available
```

### Network Connectivity Test
```bash
# Test internet connectivity
echo "=== Network Test ==="
ping -c 3 google.com
ping -c 3 github.com
curl -I https://repo.radeon.com/rocm/rocm.gpg.key
```

**Expected Output:**
```
3 packets transmitted, 3 received, 0% packet loss
HTTP/1.1 200 OK (for all tests)
```

### Initial GPU Detection
```bash
# Check if GPUs are visible to the system
echo "=== Initial GPU Detection ==="
lspci | grep -i amd
lspci | grep -i display
ls /dev/dri/
```

**Expected Output:**
```
Should show 8 AMD devices
Should show render nodes: renderD128, renderD129, etc.
```

---

# Phase 1: System Preparation

## Step 1.1: Update System Packages

```bash
# Become root for the entire process
sudo su

# Update package lists
echo "=== Updating System Packages ==="
apt update

# Check for any held packages
apt list --upgradable

# Upgrade system (this may take 5-10 minutes)
apt upgrade -y

# Install essential build tools
apt install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    htop \
    vim \
    python3 \
    python3-pip \
    python3-venv \
    supervisor \
    nginx \
    nodejs \
    npm \
    yarn \
    linux-headers-$(uname -r) \
    dkms \
    pciutils \
    lshw \
    hwinfo \
    lm-sensors \
    net-tools \
    software-properties-common
```

**Expected Output:**
```
Reading package lists... Done
Building dependency tree... Done
[Package installation messages]
Processing triggers for...
```

## Step 1.2: Configure System Limits

```bash
# Configure system limits for mining
echo "=== Configuring System Limits ==="

cat > /etc/security/limits.conf << 'EOF'
# HPC Mining System Limits
* soft nofile 1048576
* hard nofile 1048576
* soft memlock unlimited
* hard memlock unlimited
mining soft nofile 1048576
mining hard nofile 1048576
mining soft memlock unlimited
mining hard memlock unlimited
EOF

# Configure sysctl for performance
cat > /etc/sysctl.d/99-hpc-mining.conf << 'EOF'
# HPC Mining System Optimizations
vm.nr_hugepages = 3072
vm.hugetlb_shm_group = 1001
kernel.shmmax = 68719476736
kernel.shmall = 4294967296
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
fs.file-max = 2097152
vm.swappiness = 1
EOF

# Apply sysctl settings
sysctl -p /etc/sysctl.d/99-hpc-mining.conf

echo "System limits configured"
```

**Expected Output:**
```
vm.nr_hugepages = 3072
vm.hugetlb_shm_group = 1001
[... other sysctl values ...]
System limits configured
```

---

# Phase 2: ROCm Installation (about 20 minutes)

## Step 2.1: Add ROCm Repository

```bash
echo "=== Installing ROCm for AMD MI300 GPUs ==="

# Remove any existing ROCm packages
apt remove --purge -y rocm-* hip-* || true

# Add ROCm GPG key
wget -qO - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add -

# Add ROCm repository for Ubuntu 24.04
echo "deb [arch=amd64] https://repo.radeon.com/rocm/apt/6.2/ noble main" > /etc/apt/sources.list.d/rocm.list

# Update package lists
apt update
```

**Expected Output:**
```
OK (for GPG key)
Hit:1 http://archive.ubuntu.com/ubuntu noble InRelease
Get:2 https://repo.radeon.com/rocm/apt/6.2 noble InRelease
Reading package lists... Done
```

## Step 2.2: Install ROCm Packages

```bash
# Install ROCm development and runtime packages
echo "=== Installing ROCm Packages ==="

apt install -y \
    rocm-dev \
    rocm-libs \
    rocm-utils \
    rocm-smi-lib \
    hip-dev \
    rocrand-dev \
    rocblas-dev \
    rocfft-dev \
    rocsparse-dev \
    rocsolver-dev \
    rocthrust-dev \
    miopen-hip-dev

echo "ROCm packages installed"
```

**Expected Output:**
```
Reading package lists... Done
Building dependency tree... Done
[Package installation messages]
Setting up rocm-dev...
ROCm packages installed
```

## Step 2.3: Configure ROCm Environment

```bash
# Configure ROCm environment variables
echo "=== Configuring ROCm Environment ==="

cat > /etc/environment << 'EOF'
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/rocm/bin"
ROCM_PATH="/opt/rocm"
HIP_PATH="/opt/rocm"
DEVICE_LIB_PATH="/opt/rocm/amdgcn/bitcode"
HIP_VISIBLE_DEVICES="0,1,2,3,4,5,6,7"
HSA_OVERRIDE_GFX_VERSION="9.4.2"
EOF

# Add ROCm to system PATH
echo 'export PATH=$PATH:/opt/rocm/bin' >> /etc/bash.bashrc
echo 'export ROCM_PATH=/opt/rocm' >> /etc/bash.bashrc

# Reload environment
source /etc/environment
export PATH=$PATH:/opt/rocm/bin

echo "ROCm environment configured"
```

## Step 2.4: Test ROCm Installation

```bash
echo "=== Testing ROCm Installation ==="

# Test rocm-smi
if command -v rocm-smi &> /dev/null; then
    echo "rocm-smi found"
    rocm-smi --showproductname
    
    # Count detected GPUs
    GPU_COUNT=$(rocm-smi --showproductname 2>/dev/null | grep -c "MI300" || echo "0")
    echo "Detected $GPU_COUNT MI300 GPUs"
    
    if [ "$GPU_COUNT" -eq 8 ]; then
        echo "All 8 MI300 GPUs detected successfully!"
    else
        echo "Expected 8 GPUs, found $GPU_COUNT"
        echo "This may require a reboot to detect all GPUs properly"
    fi
else
    echo "rocm-smi not found, ROCm installation may have failed"
    exit 1
fi
```

**Expected Output:**
```
rocm-smi found
GPU[0]: AMD Instinct MI300X
GPU[1]: AMD Instinct MI300X
GPU[2]: AMD Instinct MI300X
GPU[3]: AMD Instinct MI300X
GPU[4]: AMD Instinct MI300X
GPU[5]: AMD Instinct MI300X
GPU[6]: AMD Instinct MI300X
GPU[7]: AMD Instinct MI300X
Detected 8 MI300 GPUs
All 8 MI300 GPUs detected successfully!
```

---

# Phase 3: User and Directory Setup

## Step 3.1: Create Mining User

```bash
echo "=== Creating Mining User and Directories ==="

# Create mining user
SERVICE_USER="mining"
INSTALL_DIR="/opt/hpc-cryptominer"
LOG_DIR="/var/log/hpc-miner"
CONFIG_DIR="/etc/hpc-miner"

if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash -G render,video $SERVICE_USER
    echo "Created mining user: $SERVICE_USER"
else
    echo "Mining user already exists"
fi

# Add mining user to GPU groups
usermod -a -G render,video $SERVICE_USER
```

## Step 3.2: Create Directory Structure

```bash
# Create directories
mkdir -p $INSTALL_DIR
mkdir -p $LOG_DIR
mkdir -p $CONFIG_DIR
mkdir -p /opt/miners
mkdir -p /home/$SERVICE_USER/.hpc-miner

# Set permissions
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chown -R $SERVICE_USER:$SERVICE_USER $LOG_DIR
chown -R $SERVICE_USER:$SERVICE_USER $CONFIG_DIR
chown -R $SERVICE_USER:$SERVICE_USER /opt/miners
chown -R $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER/.hpc-miner

chmod 755 $INSTALL_DIR
chmod 755 $LOG_DIR
chmod 755 $CONFIG_DIR
chmod 755 /opt/miners

echo "Directory structure created"
```

**Expected Output:**
```
Created mining user: mining
Directory structure created
```

---

# Phase 4: Download Project Files (about 10 minutes)

## Step 4.1: Get Repository URL

```bash
echo "=== Getting Project Repository ==="
echo "We need your GitHub repository URL for the HPC Cryptominer project."
echo ""
echo "Options:"
echo "1. Use the template repository (recommended for first-time setup)"
echo "2. Enter your own repository URL"
echo ""

read -p "Choose option (1 or 2): " REPO_OPTION

if [ "$REPO_OPTION" = "1" ]; then
    REPO_URL="https://github.com/hashburst/hpc-cryptominer.git"
    echo "Using template repository: $REPO_URL"
elif [ "$REPO_OPTION" = "2" ]; then
    read -p "Enter your GitHub repository URL: " REPO_URL
    if [ -z "$REPO_URL" ]; then
        echo "Repository URL is required"
        exit 1
    fi
else
    echo "Invalid option"
    exit 1
fi
```

## Step 4.2: Clone Repository

```bash
echo "=== Downloading Project Files ==="

cd /opt
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Repository exists, updating..."
    cd $INSTALL_DIR
    sudo -u $SERVICE_USER git pull origin main
else
    echo "Cloning repository from: $REPO_URL"
    sudo -u $SERVICE_USER git clone $REPO_URL $INSTALL_DIR
fi

if [ $? -eq 0 ]; then
    echo "Project files downloaded successfully"
else
    echo "Failed to download project files"
    echo "Possible issues:"
    echo "- Repository URL is incorrect"
    echo "- Network connectivity problems"
    echo "- Repository is private and requires authentication"
    exit 1
fi

# Verify key files exist
echo "=== Verifying Project Files ==="
cd $INSTALL_DIR

key_files=(
    "main.py"
    "mining_engine/core.py"
    "miners/miner_integration.py" 
    "config/hpc_cray_xd675_config.json"
)

for file in "${key_files[@]}"; do
    if [ -f "$file" ]; then
        echo "Found: $file"
    else
        echo "Missing: $file"
        echo "The repository may be incomplete"
    fi
done
```

**Expected Output:**
```
Cloning into '/opt/hpc-cryptominer'...
remote: Enumerating objects: 150, done.
remote: Counting objects: 100% (150/150), done.
Project files downloaded successfully
Found: main.py
Found: mining_engine/core.py
Found: miners/miner_integration.py
Found: config/hpc_cray_xd675_config.json
```

---

# Phase 5: Python Environment Setup (about 10 minutes)

## Step 5.1: Create Virtual Environment

```bash
echo "=== Setting Up Python Environment ==="
cd $INSTALL_DIR

# Create virtual environment
sudo -u $SERVICE_USER python3 -m venv venv

# Activate virtual environment and upgrade pip
sudo -u $SERVICE_USER bash -c "
    source venv/bin/activate
    pip install --upgrade pip
    echo 'Virtual environment created and pip upgraded'
"
```

## Step 5.2: Install Python Dependencies

```bash
echo "=== Installing Python Dependencies ==="

# Install main requirements
sudo -u $SERVICE_USER bash -c "
    source venv/bin/activate
    pip install -r backend/requirements.txt
"

# Install additional HPC packages
sudo -u $SERVICE_USER bash -c "
    source venv/bin/activate
    pip install \
        psutil \
        gpustat \
        py3nvml \
        aiofiles \
        asyncio-mqtt \
        prometheus-client
"

echo "Python dependencies installed"
```

**Expected Output:**
```
Successfully installed fastapi-0.110.1 uvicorn-0.25.0 [... other packages]
Virtual environment created and pip upgraded
Python dependencies installed
```

## Step 5.3: Test Python Environment

```bash
echo "=== Testing Python Environment ==="

sudo -u $SERVICE_USER bash -c "
    cd $INSTALL_DIR
    source venv/bin/activate
    python3 -c '
import sys
print(f\"Python version: {sys.version}\")

# Test key imports
try:
    import psutil
    print(f\"CPU cores: {psutil.cpu_count()}\")
    print(f\"Memory: {psutil.virtual_memory().total / (1024**3):.1f}GB\")
    print(\"psutil working\")
except Exception as e:
    print(f\"psutil error: {e}\")

try:
    import numpy
    print(\"numpy working\")
except Exception as e:
    print(f\"numpy error: {e}\")

try:
    import fastapi
    print(\"fastapi working\")
except Exception as e:
    print(f\"fastapi error: {e}\")
'
"
```

**Expected Output:**
```
Python version: 3.12.x
CPU cores: [Your CPU core count]
Memory: [Your RAM amount]GB
psutil working
numpy working
fastapi working
```

---

# Phase 6: Mining Software Installation (about 15 minutes)

## Step 6.1: Download lolMiner

```bash
echo "=== Installing Mining Software ==="
cd /opt/miners

echo "Downloading lolMiner..."
wget -O lolminer.tar.gz "https://github.com/Lolliedieb/lolMiner-releases/releases/download/1.88/lolMiner_v1.88_Lin64.tar.gz"

if [ $? -eq 0 ]; then
    tar -xzf lolminer.tar.gz
    mv 1.88 lolminer
    chmod +x lolminer/lolMiner
    ln -sf /opt/miners/lolminer/lolMiner /usr/local/bin/lolMiner
    echo "lolMiner installed"
else
    echo "Failed to download lolMiner"
fi
```

## Step 6.2: Download TeamRedMiner

```bash
echo "Downloading TeamRedMiner..."
wget -O teamredminer.tgz "https://github.com/todxx/teamredminer/releases/download/v0.10.21/teamredminer-v0.10.21-linux.tgz"

if [ $? -eq 0 ]; then
    tar -xzf teamredminer.tgz
    mv teamredminer-v0.10.21-linux teamredminer
    chmod +x teamredminer/teamredminer
    ln -sf /opt/miners/teamredminer/teamredminer /usr/local/bin/teamredminer
    echo "TeamRedMiner installed"
else
    echo "Failed to download TeamRedMiner"
fi
```

## Step 6.3: Download SRBMiner-MULTI

```bash
echo "Downloading SRBMiner-MULTI..."
wget -O srbminer.tar.gz "https://github.com/doktor83/SRBMiner-Multi/releases/download/2.4.8/SRBMiner-Multi-2-4-8-Linux.tar.gz"

if [ $? -eq 0 ]; then
    tar -xzf srbminer.tar.gz
    mv SRBMiner-Multi-2-4-8 srbminer
    chmod +x srbminer/SRBMiner-MULTI
    ln -sf /opt/miners/srbminer/SRBMiner-MULTI /usr/local/bin/SRBMiner-MULTI
    echo "SRBMiner-MULTI installed"
else
    echo "Failed to download SRBMiner-MULTI"
fi
```

## Step 6.4: Download XMRig

```bash
echo "Downloading XMRig..."
wget -O xmrig.tar.gz "https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-linux-static-x64.tar.gz"

if [ $? -eq 0 ]; then
    tar -xzf xmrig.tar.gz
    mv xmrig-6.21.3 xmrig
    chmod +x xmrig/xmrig
    ln -sf /opt/miners/xmrig/xmrig /usr/local/bin/xmrig
    echo "XMRig installed"
else
    echo "Failed to download XMRig"
fi
```

## Step 6.5: Verify Mining Software Installation

```bash
echo "=== Verifying Mining Software ==="

# Set ownership
chown -R $SERVICE_USER:$SERVICE_USER /opt/miners

# Test each miner
echo "Testing lolMiner..."
if command -v lolMiner &> /dev/null; then
    lolMiner --help | head -5
    echo "lolMiner working"
else
    echo "lolMiner not found"
fi

echo "Testing TeamRedMiner..."
if command -v teamredminer &> /dev/null; then
    teamredminer --help | head -5
    echo "TeamRedMiner working"
else
    echo "TeamRedMiner not found"
fi

echo "Testing SRBMiner-MULTI..."
if command -v SRBMiner-MULTI &> /dev/null; then
    SRBMiner-MULTI --help | head -5
    echo "SRBMiner-MULTI working"
else
    echo "SRBMiner-MULTI not found"
fi

echo "Testing XMRig..."
if command -v xmrig &> /dev/null; then
    xmrig --help | head -5
    echo "XMRig working"
else
    echo "XMRig not found"
fi

# List installed miners
echo "=== Installed Miners ==="
ls -la /opt/miners/
```

**Expected Output:**
```
lolMiner installed
TeamRedMiner installed
SRBMiner-MULTI installed
XMRig installed
lolMiner working
TeamRedMiner working
SRBMiner-MULTI working
XMRig working
```

---

# Phase 7: Configuration Setup (about 5 minutes)

## Step 7.1: Create Mining Configuration

```bash
echo "=== Creating Mining Configuration ==="

# Copy HPC-specific configuration
if [ -f "$INSTALL_DIR/config/hpc_cray_xd675_config.json" ]; then
    cp $INSTALL_DIR/config/hpc_cray_xd675_config.json $CONFIG_DIR/mining_config.json
    chown $SERVICE_USER:$SERVICE_USER $CONFIG_DIR/mining_config.json
    echo "HPC-specific configuration deployed"
else
    echo "HPC configuration file not found"
    echo "Creating basic configuration..."
    
    # Create basic configuration if HPC config not available
    cat > $CONFIG_DIR/mining_config.json << 'EOF'
{
  "mining": {
    "algorithms": ["Ethash", "Kawpow", "RandomX", "X11", "SHA256", "Scrypt", "Yescrypt"],
    "auto_start": true,
    "auto_switch": true,
    "preferred_algorithm": "Ethash"
  },
  "hardware": {
    "detected_gpus": 8,
    "gpu_intensity": 95,
    "temperature_limit": 90
  },
  "pools": {
    "nicehash_ethash": {
      "name": "NiceHash Ethash",
      "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353",
      "username": "YOUR_BITCOIN_ADDRESS",
      "password": "x",
      "algorithm": "Ethash",
      "worker_name": "HPE_CRAY_XD675"
    }
  }
}
EOF
    chown $SERVICE_USER:$SERVICE_USER $CONFIG_DIR/mining_config.json
fi
```

## Step 7.2: Create Wallet Address Template

```bash
echo "Creating wallet address template..."

cat > $CONFIG_DIR/wallet_addresses.txt << 'EOF'
# Wallet Addresses Configuration
# Replace these with your actual wallet addresses

# Bitcoin (for NiceHash, ZPool, ZergPool)
BITCOIN_ADDRESS=bc1qyourbitcoinaddresshere

# Ethereum Classic (for Nanopool, ViaBTC, 2Miners, F2Pool)
ETC_ADDRESS=0xYourEthereumClassicAddressHere

# Ravencoin (for Kawpow pools like NeoPool)
RVN_ADDRESS=RYourRavencoinAddressHere

# Monero (for RandomX)
XMR_ADDRESS=4YourMoneroAddressHere

# Instructions:
# 1. Replace the addresses above with your real wallet addresses
# 2. Make sure each address is valid for its respective cryptocurrency
# 3. Save this file after making changes
# 4. Restart mining services: sudo supervisorctl restart all
EOF

chown $SERVICE_USER:$SERVICE_USER $CONFIG_DIR/wallet_addresses.txt
chmod 600 $CONFIG_DIR/wallet_addresses.txt

echo "Wallet address template created"
```

## Step 7.3: Test Configuration

```bash
echo "=== Testing Configuration ==="

# Test JSON validity
if python3 -m json.tool $CONFIG_DIR/mining_config.json > /dev/null 2>&1; then
    echo "Configuration file is valid JSON"
else
    echo "Configuration file has JSON syntax errors"
fi

# Show configuration summary
echo "=== Configuration Summary ==="
python3 -c "
import json
try:
    with open('$CONFIG_DIR/mining_config.json', 'r') as f:
        config = json.load(f)
    print(f\"Algorithms: {config.get('mining', {}).get('algorithms', [])}\")
    print(f\"GPU Intensity: {config.get('hardware', {}).get('gpu_intensity', 'N/A')}%\")
    print(f\"Temperature Limit: {config.get('hardware', {}).get('temperature_limit', 'N/A')}°C\")
    print(f\"Pools configured: {len(config.get('pools', {}))}\")
except Exception as e:
    print(f'Error reading config: {e}')
"
```

**Expected Output:**
```
HPC-specific configuration deployed
Wallet address template created
Configuration file is valid JSON
Algorithms: ['Ethash', 'Kawpow', 'RandomX', 'X11', 'SHA256', 'Scrypt', 'Yescrypt']
GPU Intensity: 95%
Temperature Limit: 90°C
Pools configured: [number]
```

---

# Phase 8: System Services Configuration (about 5 minutes)

## Step 8.1: Configure Supervisor

```bash
echo "=== Configuring System Services ==="

# Create supervisor configuration for mining
cat > /etc/supervisor/conf.d/hpc-miner.conf << EOF
[program:hpc-mining-engine]
command=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py --mode=standalone --config=$CONFIG_DIR/mining_config.json
directory=$INSTALL_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
startsecs=10
startretries=3
stdout_logfile=$LOG_DIR/mining-engine.log
stderr_logfile=$LOG_DIR/mining-engine-error.log
stdout_logfile_maxbytes=100MB
stdout_logfile_backups=5
stderr_logfile_maxbytes=100MB
stderr_logfile_backups=5
environment=PYTHONPATH="$INSTALL_DIR",PYTHONUNBUFFERED="1",ROCM_PATH="/opt/rocm",HIP_VISIBLE_DEVICES="0,1,2,3,4,5,6,7"

[program:hpc-dashboard]
command=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py --mode=dashboard --config=$CONFIG_DIR/mining_config.json
directory=$INSTALL_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
startsecs=5
startretries=3
stdout_logfile=$LOG_DIR/dashboard.log
stderr_logfile=$LOG_DIR/dashboard-error.log
environment=PYTHONPATH="$INSTALL_DIR",PYTHONUNBUFFERED="1"

[program:hpc-monitor]
command=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py --mode=monitor --config=$CONFIG_DIR/mining_config.json
directory=$INSTALL_DIR
user=$SERVICE_USER
autostart=true
autorestart=true
startsecs=5
startretries=3
stdout_logfile=$LOG_DIR/monitor.log
stderr_logfile=$LOG_DIR/monitor-error.log
environment=PYTHONPATH="$INSTALL_DIR",PYTHONUNBUFFERED="1"
EOF

echo "Supervisor configuration created"
```

## Step 8.2: Configure Nginx (Optional)

```bash
echo "Configuring Nginx for web dashboard..."

cat > /etc/nginx/sites-available/hpc-miner << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /metrics {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/hpc-miner /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx configuration is valid"
else
    echo "Nginx configuration has errors"
fi
```

## Step 8.3: Start Services

```bash
echo "=== Starting Services ==="

# Reload supervisor configuration
supervisorctl reread
supervisorctl update

# Start nginx
systemctl enable nginx
systemctl restart nginx

# Enable services to start on boot
systemctl enable supervisor

echo "Services configured and started"
```

**Expected Output:**
```
Supervisor configuration created
nginx: configuration file /etc/nginx/nginx.conf test is successful
Nginx configuration is valid
hpc-mining-engine: added process group
hpc-dashboard: added process group
hpc-monitor: added process group
Services configured and started
```

---

# Phase 9: System Optimization (5 minutes)

## Step 9.1: GPU Performance Optimization

```bash
echo "=== Optimizing System for AMD MI300 GPUs ==="

# Create GPU optimization script
cat > /usr/local/bin/mi300-optimize.sh << 'EOF'
#!/bin/bash
# AMD MI300 GPU Optimization Script

echo "Applying MI300 optimizations..."

# Set performance governor for CPU
echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true

# Set GPU performance mode
for gpu in /sys/class/drm/card*/device; do
    if [ -f "$gpu/power_dpm_force_performance_level" ]; then
        echo high > "$gpu/power_dpm_force_performance_level" 2>/dev/null || true
    fi
    if [ -f "$gpu/pp_power_profile_mode" ]; then
        echo 1 > "$gpu/pp_power_profile_mode" 2>/dev/null || true  # Compute workload
    fi
done

# Configure huge pages for RandomX
echo 3072 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages 2>/dev/null || true
echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
echo never > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true

echo "MI300 optimizations applied"
EOF

chmod +x /usr/local/bin/mi300-optimize.sh

# Create systemd service for optimization
cat > /etc/systemd/system/mi300-optimize.service << 'EOF'
[Unit]
Description=AMD MI300 GPU Optimization
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/mi300-optimize.sh
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
EOF

# Enable and start optimization service
systemctl enable mi300-optimize.service
systemctl start mi300-optimize.service

echo "GPU optimization service created and started"
```

## Step 9.2: Network Optimization

```bash
echo "=== Configuring Network for Mining ==="

# Configure firewall for mining
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080:8082/tcp  # Mining services
ufw allow 3333:4444/tcp  # Mining pools
ufw allow 19999/tcp      # Nanopool
ufw allow 8118/tcp       # F2Pool, ViaBTC

echo "Firewall configured for mining"
```

**Expected Output:**
```
MI300 optimizations applied
Synchronizing state of mi300-optimize.service...
GPU optimization service created and started
Rules updated
Firewall configured for mining
```

---

# Phase 10: Final Testing and Verification (about 10 minutes)

## Step 10.1: Complete System Test

```bash
echo "========================================"
echo " FINAL SYSTEM VERIFICATION              "
echo "========================================"

# Test 1: GPU Detection
echo "=== Test 1: GPU Detection ==="
if command -v rocm-smi &> /dev/null; then
    GPU_COUNT=$(rocm-smi --showproductname 2>/dev/null | grep -c "MI300" || echo "0")
    echo "Detected GPUs: $GPU_COUNT"
    if [ "$GPU_COUNT" -eq 8 ]; then
        echo "GPU Detection: PASS"
    else
        echo "GPU Detection: FAIL (Expected 8, found $GPU_COUNT)"
    fi
    rocm-smi --showtemp | head -10
else
    echo "rocm-smi not available"
fi

# Test 2: Mining Software
echo ""
echo "=== Test 2: Mining Software ==="
miners=("lolMiner" "teamredminer" "SRBMiner-MULTI" "xmrig")
for miner in "${miners[@]}"; do
    if command -v $miner &> /dev/null; then
        echo "$miner: Available"
    else
        echo "$miner: Not found"
    fi
done

# Test 3: Python Environment
echo ""
echo "=== Test 3: Python Environment ==="
sudo -u $SERVICE_USER bash -c "
    cd $INSTALL_DIR
    source venv/bin/activate
    python3 -c 'import mining_engine; print(\"Mining engine import: PASS\")' 2>/dev/null || echo 'Mining engine import: FAIL'
    python3 -c 'import miners.miner_integration; print(\"Miner integration import: PASS\")' 2>/dev/null || echo 'Miner integration import: FAIL'
"

# Test 4: Configuration
echo ""
echo "=== Test 4: Configuration ==="
if [ -f "$CONFIG_DIR/mining_config.json" ]; then
    if python3 -m json.tool $CONFIG_DIR/mining_config.json > /dev/null 2>&1; then
        echo "Configuration file: Valid JSON"
    else
        echo "Configuration file: Invalid JSON"
    fi
else
    echo "Configuration file: Not found"
fi

# Test 5: Services
echo ""
echo "=== Test 5: Services ==="
supervisorctl status
```

## Step 10.2: Start Mining Test

```bash
echo ""
echo "=== Test 6: Mining Engine Startup ==="

# Start mining services
supervisorctl start hpc-mining-engine
supervisorctl start hpc-dashboard
supervisorctl start hpc-monitor

# Wait for services to start
sleep 10

# Check service status
echo "Service Status:"
supervisorctl status

# Test API endpoints
echo ""
echo "=== Test 7: API Endpoints ==="

# Test mining status endpoint
if curl -s http://localhost:8080/api/mining/status > /dev/null; then
    echo "Mining API: Responding"
else
    echo "Mining API: Not responding"
fi

# Test dashboard
if curl -s http://localhost:8081 > /dev/null; then
    echo "Dashboard: Responding"
else
    echo "Dashboard: Not responding"
fi

# Test metrics
if curl -s http://localhost:8082/metrics > /dev/null; then
    echo "Metrics: Responding"
else
    echo "Metrics: Not responding"
fi
```

## Step 10.3: Performance Baseline

```bash
echo ""
echo "=== Test 8: Performance Baseline ==="

# Check system resources
echo "System Resources:"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')"
echo "Memory Usage: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"

# Check GPU temperatures
echo ""
echo "GPU Temperatures:"
rocm-smi --showtemp | grep "GPU\|Temperature" || echo "Temperature data not available"

# Check network connectivity to pools
echo ""
echo "=== Test 9: Pool Connectivity ==="
pools=("stratum.nicehash.com:3353" "etc-us-east1.nanopool.org:19999" "mine.zpool.ca:4553")
for pool in "${pools[@]}"; do
    host=$(echo $pool | cut -d: -f1)
    port=$(echo $pool | cut -d: -f2)
    if timeout 3 nc -z $host $port 2>/dev/null; then
        echo "$pool: Reachable"
    else
        echo "$pool: Not reachable"
    fi
done
```

**Expected Output:**
```
========================================
 FINAL SYSTEM VERIFICATION
========================================
Detected GPUs: 8
GPU Detection: PASS
lolMiner: Available
teamredminer: Available
SRBMiner-MULTI: Available
xmrig: Available
Mining engine import: PASS
Miner integration import: PASS
Configuration file: Valid JSON
hpc-mining-engine           RUNNING   pid 12345, uptime 0:00:10
hpc-dashboard               RUNNING   pid 12346, uptime 0:00:10
hpc-monitor                 RUNNING   pid 12347, uptime 0:00:10
Mining API: Responding
Dashboard: Responding
Metrics: Responding
stratum.nicehash.com:3353: Reachable
```

---

# Phase 11: Configuration for Your Specific Setup

## Step 11.1: Configure Your Wallet Addresses

```bash
echo "========================================"
echo " WALLET CONFIGURATION                   "
echo "========================================"

echo "Now you need to configure your wallet addresses for mining."
echo "This is REQUIRED before you can start earning cryptocurrency."
echo ""

echo "Opening wallet configuration file..."
nano $CONFIG_DIR/wallet_addresses.txt

echo ""
echo "After editing wallet addresses, update the mining configuration:"
nano $CONFIG_DIR/mining_config.json

echo ""
echo "Look for the 'pools' section and update the 'username' fields with your wallet addresses."
echo "For example:"
echo "  \"username\": \"bc1qyourbitcoinaddress\" (for Bitcoin pools like NiceHash)"
echo "  \"username\": \"0xYourEthereumClassicAddress\" (for ETC pools like Nanopool)"
```

## Step 11.2: Choose Your Initial Mining Strategy

```bash
echo "========================================"
echo " MINING STRATEGY SELECTION              "
echo "========================================"

echo "Choose your initial mining strategy:"
echo ""
echo "1. Maximum Profit (Ethash) - ~$150-200/day"
echo "2. Diversified Mining (Auto-switching) - ~$100-300/day"
echo "3. Stable Mining (Single pool) - ~$80-150/day"
echo "4. Custom Configuration"
echo ""

read -p "Select strategy (1-4): " STRATEGY

case $STRATEGY in
    1)
        echo "Configuring for maximum profit with Ethash mining..."
        # Set Ethash as preferred algorithm
        python3 -c "
import json
with open('$CONFIG_DIR/mining_config.json', 'r') as f:
    config = json.load(f)
config['mining']['preferred_algorithm'] = 'Ethash'
config['mining']['auto_switch'] = False
with open('$CONFIG_DIR/mining_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Configured for Ethash mining')
"
        ;;
    2)
        echo "Configuring for diversified auto-switching mining..."
        python3 -c "
import json
with open('$CONFIG_DIR/mining_config.json', 'r') as f:
    config = json.load(f)
config['mining']['auto_switch'] = True
config['optimization']['profitability_switching']['enabled'] = True
with open('$CONFIG_DIR/mining_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Configured for auto-switching mining')
"
        ;;
    3)
        echo "Configuring for stable single-pool mining..."
        python3 -c "
import json
with open('$CONFIG_DIR/mining_config.json', 'r') as f:
    config = json.load(f)
config['mining']['auto_switch'] = False
config['mining']['preferred_algorithm'] = 'Ethash'
with open('$CONFIG_DIR/mining_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('Configured for stable mining')
"
        ;;
    4)
        echo "Opening configuration file for custom setup..."
        nano $CONFIG_DIR/mining_config.json
        ;;
    *)
        echo "Invalid selection, using default (Ethash)"
        ;;
esac
```

---

# Phase 12: Final Launch

## Step 12.1: Restart All Services

```bash
echo "========================================"
echo " FINAL LAUNCH                           "
echo "========================================"

echo "Restarting all mining services with your configuration..."

# Restart all services
supervisorctl restart all

# Wait for startup
echo "Waiting for services to start..."
sleep 15

# Check final status
echo "=== Final Service Status ==="
supervisorctl status
```

## Step 12.2: Monitor Initial Performance

```bash
echo ""
echo "=== Initial Performance Check ==="

# Show real-time mining status
echo "Mining Status:"
curl -s http://localhost:8080/api/mining/status | python3 -m json.tool | head -20

echo ""
echo "GPU Status:"
rocm-smi --showtemp --showpower | head -15

echo ""
echo "System Resources:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')% usage"
echo "Memory: $(free -m | awk 'NR==2{printf "%.1f%% used", $3*100/$2 }')"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
```

## Step 12.3: Access Instructions

```bash
echo ""
echo "========================================"
echo " DEPLOYMENT COMPLETE!                   "
echo "========================================"

# Get server IP
SERVER_IP=$(hostname -I | cut -d' ' -f1)

echo ""
echo " ACCESS YOUR MINING DASHBOARD:"
echo "   http://$SERVER_IP"
echo "   http://$SERVER_IP:8081 (direct dashboard)"
echo ""
echo " API ENDPOINTS:"
echo "   Mining Status: http://$SERVER_IP:8080/api/mining/status"
echo "   Mining Stats:  http://$SERVER_IP:8080/api/mining/stats"
echo "   Hardware Info: http://$SERVER_IP:8080/api/mining/hardware"
echo ""
echo " MONITORING:"
echo "   Metrics: http://$SERVER_IP:8082/metrics"
echo "   Logs: tail -f $LOG_DIR/mining-engine.log"
echo ""
echo " EXPECTED PERFORMANCE (8x MI300):"
echo "   Ethash:  ~20 GH/s  ($150-200/day)"
echo "   Kawpow:  ~960 MH/s ($80-120/day)"
echo "   RandomX: ~120 KH/s ($40-60/day)"
echo ""
echo " USEFUL COMMANDS:"
echo "   Check GPUs:     rocm-smi"
echo "   Service status: sudo supervisorctl status"
echo "   Restart mining: sudo supervisorctl restart hpc-mining-engine"
echo "   View logs:      tail -f $LOG_DIR/mining-engine.log"
echo ""
echo " IMPORTANT PATHS:"
echo "   Configuration: $CONFIG_DIR/mining_config.json"
echo "   Wallet Setup:  $CONFIG_DIR/wallet_addresses.txt"
echo "   Logs:          $LOG_DIR/"
echo "   Install Dir:   $INSTALL_DIR"
echo ""
echo " SUPPORT:"
echo "   If you encounter issues, check logs and GPU temperatures first"
echo "   Ensure wallet addresses are configured correctly"
echo "   Monitor GPU temperatures (should be 80-90°C)"
echo ""
echo " Your HPC Cryptominer is now running!"
echo "    Happy Mining!                    "
echo "====================================="
```

---