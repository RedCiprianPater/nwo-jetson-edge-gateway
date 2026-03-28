# Model Cache Directory

This directory stores TensorRT-optimized models cached from the cloud.

## Structure

```
models/
├── cache/              # TensorRT engine files (.trt)
│   ├── xiaomi-robotics-0.trt
│   └── pi05.trt
└── README.md           # This file
```

## Cache Management

Models are automatically:
- Downloaded from NWO cloud on first use
- Converted to TensorRT for Jetson optimization
- Stored with LRU eviction when cache is full
- Updated when cloud versions change

## Manual Preload

```bash
curl -X POST http://localhost:8080/models/preload \
  -d '{"model_id": "pi05"}'
```
