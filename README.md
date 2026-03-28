# NWO Jetson Edge Gateway

Lightweight edge-gateway for Jetson Orin that enables hybrid edge-cloud robot control. Caches inference models locally for tight servo loops (~1kHz) while pushing telemetry and planning requests to cloud.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Jetson Orin   │     │   Edge Gateway   │     │   NWO Cloud     │
│   (Unitree G1)  │◄───►│   (Docker)       │◄───►│   API           │
│                 │ 1kHz│                  │ 10Hz│                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
        │                 ┌──────┴──────┐                 │
        │                 │ Local Cache │                 │
        │                 │ TensorRT    │                 │
        │                 └─────────────┘                 │
```

**Control Loop:**
- **Local**: 1kHz servo control (cached models)
- **Cloud**: 10Hz planning, training, complex inference
- **Hybrid**: Best of both worlds

## Quick Start

### 1. Install on Jetson Orin

```bash
# Clone repo
git clone https://github.com/RedCiprianPater/nwo-jetson-edge-gateway.git
cd nwo-jetson-edge-gateway

# Configure
export NWO_API_KEY="your_api_key"
export NWO_AGENT_ID="g1_001"

# Run with Docker
docker-compose up -d
```

### 2. Verify Installation

```bash
# Check edge gateway status
curl http://localhost:8080/health

# View local model cache
curl http://localhost:8080/models

# Test control loop
curl -X POST http://localhost:8080/test/servo
```

## Features

- **TensorRT Optimization**: Models compiled for Jetson Orin
- **Local Servo Control**: 1kHz real-time loops
- **Cloud Sync**: Telemetry batching, planning requests
- **Hybrid Inference**: Route decisions between edge/cloud
- **Auto-Failover**: Cloud fallback if edge fails
- **Model Caching**: LRU cache with cloud prefetch

## Performance

| Metric | Cloud-Only | Edge-Only | Hybrid (NWO) |
|--------|-----------|-----------|--------------|
| Servo Rate | 50Hz | 1kHz | **1kHz** |
| Latency | 20ms | 1ms | **1ms local** |
| Planning | 10Hz | N/A | **10Hz cloud** |
| Model Updates | Real-time | Manual | **Auto-sync** |

## Configuration

### Environment Variables

```bash
NWO_API_KEY=your_api_key
NWO_AGENT_ID=g1_001
NWO_CLOUD_URL=https://nwo.capital/webapp

# Edge settings
EDGE_SERVO_RATE=1000
EDGE_MODEL_CACHE_MB=2048
EDGE_CLOUD_SYNC_HZ=10

# TensorRT optimization
TENSORRT_FP16=true
TENSORRT_MAX_BATCH=4
```

### Model Cache

Cached models (auto-downloaded from cloud):
- `xiaomi-robotics-0` (policy model)
- `pi05` (manipulation)
- `gr00t-n1.7` (navigation)

## API Endpoints

### Local Edge API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Gateway status |
| `GET /models` | Cached models |
| `POST /control/servo` | Direct servo control |
| `POST /inference/local` | Edge inference |
| `POST /inference/cloud` | Cloud proxy |
| `POST /telemetry/batch` | Queue telemetry |

### Example: Hybrid Control

```python
import requests

# High-frequency servo (local)
while True:
    response = requests.post('http://localhost:8080/control/servo', json={
        'joint_targets': [0.1, -0.5, 1.2, ...],
        'timestamp': time.time_ns()
    })
    # Runs at 1kHz, ~1ms latency

# Low-frequency planning (cloud via edge)
response = requests.post('http://localhost:8080/inference/cloud', json={
    'model_id': 'gr00t-n1.7',
    'instruction': 'Navigate to the kitchen',
    'priority': 'low'
})
```

## Docker Deployment

### Jetson Orin (ARM64)

```bash
# Build for Jetson
docker build -f docker/Dockerfile.jetson -t nwo-edge-gateway:jetson .

# Run with GPU support
docker run --runtime nvidia --gpus all \
  -e NWO_API_KEY=$NWO_API_KEY \
  -e NWO_AGENT_ID=g1_001 \
  -p 8080:8080 \
  -v /dev/shm:/dev/shm \
  nwo-edge-gateway:jetson
```

### Development (x86)

```bash
docker-compose -f docker/docker-compose.dev.yml up
```

## Model Optimization

### Convert to TensorRT

```bash
# Inside container
python scripts/optimize_tensorrt.py \
  --model xiaomi-robotics-0 \
  --output models/xiaomi-robotics-0.trt \
  --fp16
```

### Cache Management

```bash
# List cached models
curl http://localhost:8080/models

# Preload model
curl -X POST http://localhost:8080/models/preload \
  -d '{"model_id": "pi05"}'

# Clear cache
curl -X POST http://localhost:8080/models/clear
```

## Telemetry & Cloud Sync

The edge gateway automatically:
1. **Batches telemetry** (100Hz local → 10Hz cloud)
2. **Syncs models** (cloud updates → local cache)
3. **Routes inference** (local for servo, cloud for planning)
4. **Handles failover** (edge → cloud if local fails)

## Comparison: NWO vs NVIDIA Isaac

| Feature | NWO Edge Gateway | NVIDIA Isaac |
|---------|-----------------|--------------|
| **Hardware** | Jetson Orin ($16k robot) | DGX + Jetson ($500k+) |
| **Setup** | Docker container | Complex infrastructure |
| **Servo Rate** | 1kHz | 1kHz |
| **Cloud Integration** | Native | Manual |
| **Model Updates** | Auto-sync | Manual deployment |
| **Cost** | Included | $50k+/year |

## Repository Structure

```
nwo-jetson-edge-gateway/
├── docker/
│   ├── Dockerfile.jetson      # Jetson Orin optimized
│   ├── Dockerfile.dev         # Development
│   └── docker-compose.yml
├── src/
│   ├── edge_gateway.py        # Main gateway
│   ├── servo_controller.py    # 1kHz servo loop
│   ├── model_cache.py         # TensorRT cache
│   ├── cloud_proxy.py         # Cloud sync
│   └── inference_router.py    # Edge/cloud routing
├── models/                    # Cached TensorRT models
├── config/
│   └── gateway.yaml          # Configuration
└── scripts/
    ├── optimize_tensorrt.py   # Model optimization
    ├── setup_jetson.sh       # Jetson setup
    └── benchmark.py          # Performance tests
```

## Development

### Build from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run gateway
python src/edge_gateway.py

# Run tests
pytest tests/
```

### Benchmark

```bash
python scripts/benchmark.py --duration 60
```

## License

MIT License - See LICENSE

## Support

- **Documentation**: https://nwo.capital/webapp/nwo-jetson-edge-gateway
- **Issues**: https://github.com/RedCiprianPater/nwo-jetson-edge-gateway/issues
- **Email**: ciprian.pater@publicae.org

## References

- Unitree G1: https://www.unitree.com/products/g1
- Jetson Orin: https://developer.nvidia.com/embedded/jetson-orin
- TensorRT: https://developer.nvidia.com/tensorrt
- NWO Robotics API: https://nwo.capital/webapp/nwo-robotics.html
