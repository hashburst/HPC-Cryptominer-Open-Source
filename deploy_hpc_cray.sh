#!/bin/bash

# HPC HPE CRAY XD675 Deployment Script
# Optimized for 8x AMD MI300 GPUs with Ubuntu 24.04

set -e

echo "HPC Cryptominer Deployment for HPE CRAY XD675"
echo "============================================="
echo "Target: 8x AMD MI300 GPUs, Ubuntu 24.04"
echo "Algorithms: SHA-256, Kawpow, X11, Scrypt, Yescrypt, Ethash, RandomX"
echo "Pools: NiceHash, Nanopool, ZPool, ViaBTC, NeoPool, ZergPool, 2Miners, F2Pool"
echo ""

# Configuration
INSTALL_DIR="/opt/hpc-cryptominer"
SERVICE_USER="mining"
LOG_DIR="/var/log/hpc-miner"
CONFIG_DIR="/etc/hpc-miner"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# System preparation
prepare_system() {
    log_step "Preparing Ubuntu 24.04 system for HPC mining..."
    
    # Update system
    apt update && apt upgrade -y
    
    # Install essential packages
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
        redis-server \
        nodejs \
        npm \
        yarn \
        docker.io \
        docker-compose \
        linux-headers-$(uname -r) \
        dkms \
        pciutils \
        lshw \
        hwinfo \
        lm-sensors \
        stress-ng
    
    # Configure system limits
    cat > /etc/security/limits.conf << EOF
# HPC Mining Optimizations
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
    cat > /etc/sysctl.d/99-hpc-mining.conf << EOF
# HPC Mining System Optimizations
vm.nr_hugepages = 3072
vm.hugetlb_shm_group = 1001
kernel.shmmax = 68719476736
kernel.shmall = 4294967296
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.core.netdev_max_backlog = 5000
fs.file-max = 2097152
vm.swappiness = 1
EOF
    
    sysctl -p /etc/sysctl.d/99-hpc-mining.conf
    
    log_info "System preparation completed"
}

# Install ROCm for AMD MI300 GPUs
install_rocm() {
    log_step "Installing ROCm for AMD MI300 GPUs..."
    
    # Add ROCm repository
    wget -qO - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add -
    echo "deb [arch=amd64] https://repo.radeon.com/rocm/apt/6.2/ jammy main" > /etc/apt/sources.list.d/rocm.list
    
    apt update
    
    # Install ROCm packages
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
    
    # Add mining user to render and video groups
    usermod -a -G render,video $SERVICE_USER 2>/dev/null || true
    
    # Configure ROCm environment
    cat > /etc/environment << 'EOF'
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/rocm/bin"
ROCM_PATH="/opt/rocm"
HIP_PATH="/opt/rocm"
DEVICE_LIB_PATH="/opt/rocm/amdgcn/bitcode"
HIP_VISIBLE_DEVICES="0,1,2,3,4,5,6,7"
HSA_OVERRIDE_GFX_VERSION="9.4.2"
EOF
    
    # Test ROCm installation
    if command -v rocm-smi &> /dev/null; then
        log_info "ROCm installation successful"
        rocm-smi --showproductname
    else
        log_error "ROCm installation failed"
        return 1
    fi
}

# Create mining user and directories
setup_mining_user() {
    log_step "Setting up mining user and directories..."
    
    # Create mining user
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -m -s /bin/bash -G render,video,docker $SERVICE_USER
        log_info "Created mining user: $SERVICE_USER"
    fi
    
    # Create directories
    mkdir -p $INSTALL_DIR
    mkdir -p $LOG_DIR
    mkdir -p $CONFIG_DIR
    mkdir -p /home/$SERVICE_USER/.hpc-miner
    
    # Set permissions
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    chown -R $SERVICE_USER:$SERVICE_USER $LOG_DIR
    chown -R $SERVICE_USER:$SERVICE_USER $CONFIG_DIR
    chown -R $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER/.hpc-miner
    
    chmod 755 $INSTALL_DIR
    chmod 755 $LOG_DIR
    chmod 755 $CONFIG_DIR
}

# Deploy application from GitHub
deploy_from_github() {
    log_step "Deploying HPC Cryptominer from GitHub..."
    
    # Clone repository (replace with your actual GitHub repository)
    read -p "Enter your GitHub repository URL (e.g., https://github.com/yourusername/hpc-cryptominer.git): " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        log_error "Repository URL is required"
        exit 1
    fi
    
    if [ -d "$INSTALL_DIR/.git" ]; then
        log_info "Repository exists, updating..."
        cd $INSTALL_DIR
        sudo -u $SERVICE_USER git pull origin main
    else
        log_info "Cloning repository from: $REPO_URL"
        sudo -u $SERVICE_USER git clone $REPO_URL $INSTALL_DIR
    fi
    
    cd $INSTALL_DIR
    
    # Copy HPC-specific configuration
    if [ -f "/app/config/hpc_cray_xd675_config.json" ]; then
        cp /app/config/hpc_cray_xd675_config.json $CONFIG_DIR/mining_config.json
        chown $SERVICE_USER:$SERVICE_USER $CONFIG_DIR/mining_config.json
        log_info "HPC-specific configuration deployed"
    fi
}

# Install Python dependencies
install_python_deps() {
    log_step "Installing Python dependencies..."
    
    cd $INSTALL_DIR
    
    # Create virtual environment
    sudo -u $SERVICE_USER python3 -m venv venv
    
    # Install requirements
    sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER ./venv/bin/pip install -r backend/requirements.txt
    
    # Install additional HPC packages
    sudo -u $SERVICE_USER ./venv/bin/pip install \
        rocm-smi \
        pynvml \
        psutil \
        gpustat \
        py3nvml \
        pyamdgpuinfo
        
    log_info "Python dependencies installed"
}

# Install Node.js dependencies
install_node_deps() {
    log_step "Installing Node.js dependencies..."
    
    cd $INSTALL_DIR/frontend
    
    # Install dependencies
    sudo -u $SERVICE_USER yarn install
    
    # Build frontend
    sudo -u $SERVICE_USER yarn build
    
    log_info "Node.js dependencies installed and frontend built"
}

# Configure system services
configure_services() {
    log_step "Configuring system services..."
    
    # Supervisor configuration
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

    # Nginx configuration for dashboard
    cat > /etc/nginx/sites-available/hpc-miner << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /metrics {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

    ln -sf /etc/nginx/sites-available/hpc-miner /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Reload services
    supervisorctl reread
    supervisorctl update
    systemctl reload nginx
    systemctl enable nginx
    systemctl enable supervisor
    
    log_info "System services configured"
}

# Optimize system for MI300 GPUs
optimize_mi300() {
    log_step "Optimizing system for AMD MI300 GPUs..."
    
    # Set GPU power and clock settings
    cat > /usr/local/bin/mi300-optimize.sh << 'EOF'
#!/bin/bash
# AMD MI300 GPU Optimization Script

# Set performance governor
echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set GPU performance mode
for gpu in /sys/class/drm/card*/device; do
    if [ -f "$gpu/power_dpm_force_performance_level" ]; then
        echo high > "$gpu/power_dpm_force_performance_level"
    fi
    if [ -f "$gpu/pp_power_profile_mode" ]; then
        echo 1 > "$gpu/pp_power_profile_mode"  # Compute workload
    fi
done

# Optimize memory
echo 3072 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag

# Set IRQ affinity for better performance
echo 2 > /proc/irq/*/smp_affinity_list 2>/dev/null || true
EOF

    chmod +x /usr/local/bin/mi300-optimize.sh
    
    # Create systemd service for optimization
    cat > /etc/systemd/system/mi300-optimize.service << EOF
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

    systemctl enable mi300-optimize.service
    systemctl start mi300-optimize.service
    
    log_info "MI300 optimization applied"
}

# Test installation
test_installation() {
    log_step "Testing installation..."
    
    # Test GPU detection
    log_info "Testing GPU detection..."
    if command -v rocm-smi &> /dev/null; then
        rocm-smi --showproductname
        GPU_COUNT=$(rocm-smi --showproductname | grep -c "MI300" || echo "0")
        log_info "Detected $GPU_COUNT MI300 GPUs"
    fi
    
    # Test Python environment
    log_info "Testing Python environment..."
    cd $INSTALL_DIR
    sudo -u $SERVICE_USER ./venv/bin/python -c "
import sys
print(f'Python version: {sys.version}')

try:
    import psutil
    print(f'CPU cores: {psutil.cpu_count()}')
    print(f'Memory: {psutil.virtual_memory().total / (1024**3):.1f}GB')
except Exception as e:
    print(f'Error: {e}')
"
    
    # Test configuration
    log_info "Testing configuration..."
    if [ -f "$CONFIG_DIR/mining_config.json" ]; then
        log_info "Configuration file found"
        python3 -m json.tool $CONFIG_DIR/mining_config.json > /dev/null && log_info "Configuration file is valid JSON"
    fi
    
    # Test services
    log_info "Testing services..."
    supervisorctl status
    
    log_info "Installation test completed"
}

# Generate mining addresses template
generate_addresses_template() {
    log_step "Generating wallet addresses template..."
    
    cat > $CONFIG_DIR/wallet_addresses.txt << 'EOF'
# Wallet Addresses Configuration
# Replace these with your actual wallet addresses

# Bitcoin (for NiceHash, ZPool, ZergPool)
BITCOIN_ADDRESS=bc1qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Ethereum Classic (for Nanopool, ViaBTC, 2Miners, F2Pool)
ETC_ADDRESS=0xXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Ravencoin (for Kawpow pools)
RVN_ADDRESS=RXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxx

# Monero (for RandomX)
XMR_ADDRESS=4XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx
EOF

    chown $SERVICE_USER:$SERVICE_USER $CONFIG_DIR/wallet_addresses.txt
    chmod 600 $CONFIG_DIR/wallet_addresses.txt
    
    log_info "Wallet addresses template created at $CONFIG_DIR/wallet_addresses.txt"
}

# Main deployment function
main() {
    log_info "Starting HPC Cryptominer deployment for HPE CRAY XD675..."
    
    check_root
    prepare_system
    install_rocm
    setup_mining_user
    deploy_from_github
    install_python_deps
    install_node_deps
    configure_services
    optimize_mi300
    generate_addresses_template
    test_installation
    
    echo ""
    echo "*** HPC Cryptominer deployment completed successfully!"
    echo ""
    echo "** Next Steps:"
    echo "1. Edit wallet addresses in: $CONFIG_DIR/wallet_addresses.txt"
    echo "2. Configure mining pools in: $CONFIG_DIR/mining_config.json"
    echo "3. Start mining: supervisorctl start all"
    echo "4. View dashboard: http://$(hostname -I | cut -d' ' -f1)"
    echo "5. Monitor logs: tail -f $LOG_DIR/mining-engine.log"
    echo ""
    echo "** Useful Commands:"
    echo "- Check GPU status: rocm-smi"
    echo "- Service status: supervisorctl status"
    echo "- Restart mining: supervisorctl restart hpc-mining-engine"
    echo "- View configuration: cat $CONFIG_DIR/mining_config.json"
    echo ""
    echo "** Expected Performance (8x MI300):"
    echo "- Ethash: ~20 GH/s total"
    echo "- Kawpow: ~960 MH/s total"
    echo "- RandomX: ~120 KH/s total"
    echo "- X11: ~360 GH/s total"
    echo ""
}

# Run main function
main "$@"