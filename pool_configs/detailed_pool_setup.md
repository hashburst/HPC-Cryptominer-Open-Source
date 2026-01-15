# Detailed Pool Configuration for HPE CRAY XD675

## Pool Configuration Guide for 8x AMD MI300 GPUs

Neurallity's HPE CRAY XD675 with 8x AMD MI300 GPUs is exceptionally powerful. Here's the optimized configuration for maximum profitability across all supported pools and algorithms.

## Expected Performance & Profitability

### Algorithm Performance Estimates (8x MI300):
- **Ethash**: ~20 GH/s total (~$150-200/day estimated)
- **Kawpow**: ~960 MH/s total (~$80-120/day estimated)
- **RandomX**: ~120 KH/s total (~$40-60/day estimated)
- **X11**: ~360 GH/s total (~$100-150/day estimated)
- **SHA-256**: ~64 TH/s total (~$200-300/day estimated)
- **Scrypt**: ~22.4 GH/s total (~$60-90/day estimated)
- **Yescrypt**: ~68 KH/s total (~$20-30/day estimated)

## Pool Configurations

### 1. NiceHash (Recommended - Highest Liquidity)

**Best for**: All algorithms, automatic profitability switching

```json
"nicehash_ethash": {
  "name": "NiceHash Ethash",
  "url": "stratum+tcp://daggerhashimoto.nicehash.com:3353",
  "backup_url": "stratum+tcp://daggerhashimoto.eu.nicehash.com:3353",
  "username": "YOUR_BITCOIN_ADDRESS",
  "password": "x",
  "algorithm": "Ethash",
  "worker_name": "HPE_CRAY_XD675",
  "priority": 1
}
```

**Wallet Setup**: You need a Bitcoin address
- **Recommended**: Hardware wallet (Ledger/Trezor)
- **Alternative**: Coinbase, Binance, or other exchange
- **Format**: bc1... or 3... or 1...

### 2. Nanopool (Low Fees, Stable)

**Best for**: Ethereum Classic, stable payouts

```json
"nanopool_etc": {
  "name": "Nanopool Ethereum Classic", 
  "url": "stratum+tcp://etc-us-east1.nanopool.org:19999",
  "username": "YOUR_ETC_ADDRESS",
  "password": "x",
  "algorithm": "Ethash",
  "min_payout": "0.1 ETC"
}
```

**Wallet Setup**: Ethereum Classic address
- **MetaMask**: Add ETC network
- **Trust Wallet**: Native ETC support
- **Format**: 0x...

### 3. ZPool (Multi-Algorithm Auto-Switching)

**Best for**: Automatic profitability switching

```json
"zpool_multi": {
  "name": "ZPool Multi-Algorithm",
  "url": "stratum+tcp://mine.zpool.ca:4553",
  "username": "YOUR_BITCOIN_ADDRESS",
  "password": "c=BTC,mc=RVN,ID=HPE_CRAY_XD675",
  "auto_switch": true
}
```

### 4. ViaBTC (Professional Pool)

**Best for**: Large-scale mining, enterprise features

```json
"viabtc_etc": {
  "name": "ViaBTC Ethereum Classic",
  "url": "stratum+tcp://etc.viabtc.com:8118", 
  "username": "YOUR_ETC_ADDRESS.HPE_CRAY_XD675",
  "password": "x",
  "algorithm": "Ethash"
}
```

### 5. NeoPool (Low Fees)

**Best for**: Kawpow (Ravencoin), competitive fees

```json
"neopool_kawpow": {
  "name": "NeoPool Kawpow",
  "url": "stratum+tcp://kawpow.neopool.org:4501",
  "username": "YOUR_RVN_ADDRESS", 
  "password": "x",
  "algorithm": "Kawpow"
}
```

**Wallet Setup**: Ravencoin address
- **Ravencoin Core**: Official wallet
- **Trust Wallet**: RVN support
- **Format**: R...

### 6. ZergPool (Lowest Fees)

**Best for**: Maximum profit with 0.5% fees

```json
"zergpool_multi": {
  "name": "ZergPool Multi-Algorithm",
  "url": "stratum+tcp://mine.zergpool.com:4553",
  "username": "YOUR_BITCOIN_ADDRESS",
  "password": "c=BTC,mc=RVN,ID=HPE_CRAY_XD675",
  "fee": 0.005
}
```

### 7. 2Miners (Transparent, Fair)

**Best for**: Transparent statistics, PPLNS rewards

```json
"2miners_etc": {
  "name": "2Miners Ethereum Classic",
  "url": "stratum+tcp://etc.2miners.com:1010",
  "username": "YOUR_ETC_ADDRESS",
  "password": "x",
  "algorithm": "Ethash"
}
```

### 8. F2Pool (Established, Global)

**Best for**: Global presence, multiple algorithms

```json
"f2pool_etc": {
  "name": "F2Pool Ethereum Classic", 
  "url": "stratum+tcp://etc.f2pool.com:8118",
  "username": "YOUR_ETC_ADDRESS.HPE_CRAY_XD675",
  "password": "x",
  "algorithm": "Ethash"
}
```

## Algorithm-Specific Optimizations

### Ethash (Primary Recommendation)
- **Best Pools**: NiceHash, Nanopool, 2Miners
- **GPU Settings**: 95% intensity, aggressive memory timing
- **Expected**: 2.5 GH/s per MI300
- **Power**: ~300W per GPU
- **Profit**: Highest for your hardware

### Kawpow (Secondary)
- **Best Pools**: NiceHash, NeoPool
- **GPU Settings**: 90% intensity, bandwidth optimized
- **Expected**: 120 MH/s per MI300
- **Memory**: 2GB DAG size
- **Profit**: Good alternative to Ethash

### RandomX (CPU + GPU Hybrid)
- **Best Pools**: NiceHash, supportxmr.com
- **Settings**: 32 threads per GPU, 2GB per thread
- **Expected**: 15 KH/s per MI300
- **Memory**: Requires large system RAM
- **Profit**: Good for CPU+GPU combo

## Advanced Configuration Tips

### 1. Profitability Switching
```json
"profitability_switching": {
  "enabled": true,
  "check_interval": 300,
  "min_profit_difference": 0.05,
  "stability_period": 600
}
```

### 2. Temperature Management
```json
"temperature_limits": {
  "critical": 90,
  "warning": 85,
  "target": 80,
  "fan_curve": "aggressive"
}
```

### 3. Power Optimization
```json
"power_management": {
  "per_gpu_limit": 400,
  "total_system_limit": 3500,
  "efficiency_mode": true
}
```

## Monitoring & Analytics

### Real-time Monitoring
- **Dashboard**: http://your-server-ip:8081
- **Metrics**: http://your-server-ip:8082/metrics
- **API**: http://your-server-ip:8080/api

### Performance Tracking
- **Hashrate monitoring**: Every 15 seconds
- **Temperature alerts**: > 85°C
- **Profit tracking**: Real-time USD calculations
- **Pool switching**: Automatic based on profitability

## Deployment Commands

### Quick Start
```bash
# Download and run deployment script
curl -L https://github.com/hashburst/HPC-Cryptominer/blob/main/deploy_hpc_cray.sh | sudo bash

# Configure wallet addresses
sudo nano /etc/hpc-miner/wallet_addresses.txt

# Start mining
sudo supervisorctl start all
```

### Manual Configuration
```bash
# Edit configuration
sudo nano /etc/hpc-miner/mining_config.json

# Test configuration
cd /opt/hpc-cryptominer
./venv/bin/python create_default_config.py

# Restart services
sudo supervisorctl restart all
```

## Optimization Recommendations

### For Maximum Profit:
1. **Start with Ethash** - Highest profit potential
2. **Enable auto-switching** - Let AI optimize pool selection
3. **Monitor temperature** - Keep GPUs under 85°C
4. **Use NiceHash initially** - Easiest setup, good profitability
5. **Scale gradually** - Test with 2 GPUs first, then full 8

### For Stability:
1. **Single algorithm focus** - Less switching overhead
2. **Conservative power limits** - 350W per GPU
3. **Fixed pool selection** - Avoid frequent switching
4. **Temperature priority** - Stability over maximum hashrate

### For Experimentation:
1. **Multi-pool setup** - Compare profitability
2. **Algorithm rotation** - Test all supported algorithms
3. **Custom intensity** - Fine-tune per GPU
4. **Dual mining** - CPU RandomX + GPU Ethash

## Important Notes

1. **Power Requirements**: 8x MI300 = ~3.2kW total system power
2. **Cooling**: Ensure adequate cooling for sustained mining
3. **Network**: Stable internet connection essential
4. **Regulations**: Check local cryptocurrency mining laws
5. **Electricity Costs**: Factor in ~$10-15/day electricity costs

## Troubleshooting

### Common Issues:
- **Low hashrate**: Check GPU temperature throttling
- **High rejection rate**: Switch pools or check network
- **GPU crashes**: Reduce intensity or power limit
- **Pool connection fails**: Check firewall and DNS

### Support Resources:
- **Logs**: `/var/log/hpc-miner/`
- **GPU Status**: `rocm-smi`
- **Service Status**: `supervisorctl status`
- **Configuration Test**: `python3 -m json.tool /etc/hpc-miner/mining_config.json`

This configuration should maximize the mining profitability with the powerful HPE CRAY XD675 system.