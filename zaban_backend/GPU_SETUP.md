# GPU Setup Guide

This document explains how to set up GPU support for Zaban backend to accelerate ML model inference.

## Prerequisites

### 1. Hardware Requirements
- NVIDIA GPU with CUDA compute capability 3.5 or higher
- Minimum 6GB VRAM (8GB+ recommended for TTS models)

### 2. Software Requirements

#### On Host Machine:
- **NVIDIA GPU Driver**: Version 525.60.13 or newer
  ```bash
  # Check driver version
  nvidia-smi
  ```

- **NVIDIA Container Toolkit** (nvidia-docker2)
  ```bash
  # Install on Ubuntu/Debian
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
  curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

  sudo apt-get update
  sudo apt-get install -y nvidia-docker2
  sudo systemctl restart docker
  ```

- **Docker Compose**: Version 1.28.0+ (for GPU support)
  ```bash
  # Check version
  docker-compose --version
  ```

## What's Included

### Dockerfile Changes
- **Base Image**: `nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04`
- **PyTorch with CUDA**: Installed with CUDA 12.1 support
- **Python 3.11**: Manually installed on CUDA base image

### Docker Compose GPU Configuration
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
environment:
  NVIDIA_VISIBLE_DEVICES: all
  NVIDIA_DRIVER_CAPABILITIES: compute,utility
```

## Verify GPU Setup

### 1. Check NVIDIA Container Toolkit
```bash
# Test GPU access in Docker
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

You should see your GPU listed with driver version and CUDA version.

### 2. Build and Run Zaban
```bash
# Build with GPU support
docker-compose build --build-arg HUGGING_FACE_TOKEN=hf_xxxxx

# Start services
docker-compose up -d

# Check GPU is detected
docker-compose exec backend nvidia-smi
```

### 3. Verify PyTorch GPU Access
```bash
# Check PyTorch CUDA availability
docker-compose exec backend bash -c ". .venv/bin/activate && python -c 'import torch; print(f\"CUDA available: {torch.cuda.is_available()}\"); print(f\"CUDA devices: {torch.cuda.device_count()}\"); print(f\"Current device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}\")'"
```

Expected output:
```
CUDA available: True
CUDA devices: 1
Current device: NVIDIA GeForce RTX 3090 (or your GPU model)
```

## GPU Acceleration in Services

### Which Models Use GPU?

| Service | Model | GPU Acceleration | Performance Gain |
|---------|-------|------------------|------------------|
| **Translation** | IndicTrans2 | ✅ Yes | ~3-5x faster |
| **TTS** | IndicParler | ✅ Yes | ~5-10x faster |
| **STT** | Whisper | ✅ Yes (if available) | ~2-4x faster |
| **Language Detection** | FastText | ❌ No (CPU-only) | N/A |

### Automatic GPU Detection

All services automatically detect and use GPU if available:

```python
# IndicTrans2
self.device = "cuda" if torch.cuda.is_available() else "cpu"

# IndicParler TTS
torch_dtype = torch.float16 if self.device == "cuda" else torch.float32

# Whisper
device = "cuda" if torch.cuda.is_available() else "cpu"
```

## Troubleshooting

### Issue: "nvidia-smi: command not found" in container

**Cause**: NVIDIA Container Toolkit not installed or Docker not restarted.

**Solution**:
```bash
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Issue: "CUDA available: False" in PyTorch

**Cause**: GPU not exposed to container.

**Solution**: Check docker-compose.yml has GPU configuration:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

### Issue: "CUDA out of memory"

**Cause**: GPU VRAM exhausted.

**Solutions**:
1. Use smaller models (e.g., IndicTrans2-200M instead of full size)
2. Reduce batch size in model inference
3. Use CPU fallback for some models
4. Upgrade to GPU with more VRAM

### Issue: GPU driver version mismatch

**Cause**: Host driver too old for CUDA 12.1.

**Solution**: Update NVIDIA driver on host:
```bash
# Ubuntu/Debian
sudo ubuntu-drivers install

# Or manually
sudo apt-get install nvidia-driver-535
sudo reboot
```

## CPU-Only Fallback

To run without GPU (CPU-only mode):

### Option 1: Use CPU-only Dockerfile
Create `Dockerfile.cpu`:
```dockerfile
FROM python:3.11-slim
# ... (rest same as before, without CUDA and without PyTorch CUDA index)
```

### Option 2: Remove GPU Configuration
Comment out GPU config in docker-compose.yml:
```yaml
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: all
#           capabilities: [gpu]
```

**Note**: CPU inference is slower but functional.

## Performance Benchmarks

Approximate inference times (single request):

| Task | Model | CPU (Intel i9) | GPU (RTX 3090) |
|------|-------|---------------|----------------|
| Translation | IndicTrans2 | 800ms | 150ms |
| TTS | IndicParler | 3000ms | 500ms |
| STT | Whisper medium | 2000ms | 800ms |

*Actual performance varies by hardware and input size.*

## Production Recommendations

1. **Use GPU for production** - Significantly better user experience
2. **Monitor GPU usage** - Use `nvidia-smi` or Prometheus exporters
3. **Set memory limits** - Prevent OOM crashes
4. **Use model caching** - Pre-download models during build (already configured)
5. **Load balancing** - Multiple GPU containers for high traffic

## References

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker Compose GPU support](https://docs.docker.com/compose/gpu-support/)
- [PyTorch CUDA installation](https://pytorch.org/get-started/locally/)
