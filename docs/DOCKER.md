# DeepStream 8.0 + YOLO11x Docker Guide

Complete guide for running DeepStream 8.0 with YOLO11x object detection in Docker containers on x86 platforms with NVIDIA GPUs.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Building the Image](#building-the-image)
- [Running the Container](#running-the-container)
- [Docker Compose](#docker-compose)
- [GPU Configuration](#gpu-configuration)
- [Volume Mounts](#volume-mounts)
- [Environment Variables](#environment-variables)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)
- [Production Deployment](#production-deployment)

---

## Overview

### Supported Platforms

- **Architecture**: x86_64 (64-bit)
- **GPUs**: NVIDIA RTX 3090, RTX 3080, RTX 3070, TESLA T4, V100, A100, etc.
- **CUDA**: 12.8
- **TensorRT**: 10.7.0
- **DeepStream**: 8.0.0

### Image Details

- **Base Image**: `nvcr.io/nvidia/deepstream:8.0-gc-triton-devel`
- **Size**: ~8-10 GB (multi-stage optimized)
- **Python**: 3.10
- **YOLO**: 11x (Ultralytics)

---

## Prerequisites

> **🚨 IMPORTANT: Fresh System Setup**
>
> If you're setting up on a **fresh system without NVIDIA/CUDA libraries**, we provide an automated installer:
>
> ```bash
> sudo ./scripts/install-nvidia-prerequisites.sh
> ```
>
> This installs NVIDIA drivers + nvidia-container-toolkit on Ubuntu/Debian/RHEL/Rocky/CentOS.
>
> **See [HOST_SETUP.md](HOST_SETUP.md) for complete host setup instructions.**

### 1. NVIDIA GPU Drivers

The host system needs NVIDIA GPU drivers (version ≥ 525.60.13 for CUDA 12.8):

```bash
# Check if drivers are installed
nvidia-smi

# Ubuntu/Debian - Install drivers
sudo apt update
sudo apt install nvidia-driver-550  # or latest version
sudo reboot
```

### 2. Docker

Install Docker Engine:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### 3. NVIDIA Container Toolkit

Install NVIDIA Container Toolkit for GPU access in Docker:

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt update
sudo apt install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

### 4. X11 for GUI (Optional)

For GUI applications with display:

```bash
# Allow Docker to connect to X server
xhost +local:docker
```

---

## Quick Start

### 1. Clone and Navigate

```bash
cd /home/diego/Documentos/deepstream/app
```

### 2. Build the Image

```bash
./scripts/docker-build.sh
```

### 3. Run Interactively

```bash
./scripts/docker-run.sh
```

### 4. Build TensorRT Engine (First Time)

```bash
# Inside container
python3 engines/auto_build_engine.py
```

### 5. Run DeepStream Application

```bash
# Inside container
python3 deepstream_api/main_low_latency.py
```

---

## Building the Image

### Option 1: Using Build Script (Recommended)

```bash
# Basic build
./scripts/docker-build.sh

# Custom configuration
IMAGE_NAME=my-deepstream IMAGE_TAG=v1.0 ./scripts/docker-build.sh

# With specific CUDA version
CUDA_VER=12.8 ./scripts/docker-build.sh
```

### Option 2: Manual Docker Build

```bash
# Build with default settings
docker build -t deepstream-yolo11:latest -f Dockerfile.x86 .

# Build with custom tags
docker build \
    -t deepstream-yolo11:latest \
    -t deepstream-yolo11:8.0 \
    --build-arg CUDA_VER=12.8 \
    -f Dockerfile.x86 .
```

### Option 3: Using Docker Compose

```bash
docker-compose build deepstream-app
```

### Build Options

| Build Argument | Default | Description |
|---------------|---------|-------------|
| `CUDA_VER` | 12.8 | CUDA version |
| `TENSORRT_VER` | 10.7.0 | TensorRT version |

---

## Running the Container

### Option 1: Using Run Script (Recommended)

```bash
# Interactive mode with GUI
./scripts/docker-run.sh

# Run specific command
./scripts/docker-run.sh python3 deepstream_api/main.py

# Use specific GPU
GPU_DEVICES=0 ./scripts/docker-run.sh

# Multiple GPUs
GPU_DEVICES=0,1 ./scripts/docker-run.sh
```

### Option 2: Manual Docker Run

```bash
# Interactive with GUI
docker run -it --rm \
    --gpus all \
    --network host \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $(pwd)/engines:/app/engines \
    -v $(pwd)/logs:/app/logs \
    deepstream-yolo11:latest

# Headless mode (no GUI)
docker run -d --rm \
    --gpus all \
    -p 8554:8554 \
    -v $(pwd)/engines:/app/engines \
    -v $(pwd)/logs:/app/logs \
    deepstream-yolo11:latest \
    python3 deepstream_api/main_headless.py
```

### Option 3: Development Mode

```bash
# Mount source code for live editing
./scripts/docker-dev.sh

# Or manually
docker run -it --rm \
    --gpus all \
    --network host \
    -v $(pwd):/app \
    deepstream-yolo11:latest bash
```

---

## Docker Compose

Docker Compose provides easier orchestration with predefined configurations.

### Available Services

1. **deepstream-app**: Main interactive service
2. **deepstream-dev**: Development mode with source mounted
3. **deepstream-headless**: Headless production mode
4. **deepstream-lowlatency**: Low latency optimized

### Usage Examples

```bash
# Start interactive service
docker-compose up deepstream-app

# Start in development mode
docker-compose --profile dev up deepstream-dev

# Start headless in background
docker-compose --profile production up -d deepstream-headless

# View logs
docker-compose logs -f deepstream-headless

# Stop services
docker-compose down

# Rebuild and start
docker-compose build && docker-compose up
```

### Custom Configuration

Create `docker-compose.override.yml` for local customization:

```yaml
version: '3.8'

services:
  deepstream-app:
    environment:
      - CUDA_VISIBLE_DEVICES=0  # Use only GPU 0
      - GST_DEBUG=3              # Increase GStreamer debug level
    volumes:
      - ./custom-configs:/app/custom-configs
```

---

## GPU Configuration

### Select Specific GPU

```bash
# Environment variable
export CUDA_VISIBLE_DEVICES=0
./scripts/docker-run.sh

# Or inline
CUDA_VISIBLE_DEVICES=0 ./scripts/docker-run.sh

# Docker run directly
docker run --gpus '"device=0"' ...
```

### Multiple GPUs

```bash
# Use GPUs 0 and 1
GPU_DEVICES=0,1 ./scripts/docker-run.sh

# Docker run
docker run --gpus '"device=0,1"' ...
```

### All GPUs

```bash
# Default behavior
./scripts/docker-run.sh

# Explicit
docker run --gpus all ...
```

### Check GPU in Container

```bash
# Inside container
nvidia-smi

# Check CUDA availability in Python
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## Volume Mounts

### Default Volumes

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./engines` | `/app/engines` | TensorRT engines (persistent) |
| `./configs` | `/app/configs` | Configuration files |
| `./logs` | `/app/logs` | Application logs |
| `./output` | `/app/output` | Output videos/images |
| `./recordings` | `/app/recordings` | Recorded streams |
| `/tmp/.X11-unix` | `/tmp/.X11-unix` | X11 display (GUI) |

### Custom Volume Mounts

```bash
docker run -it --rm --gpus all \
    -v $(pwd)/engines:/app/engines \
    -v $(pwd)/models:/app/models \
    -v /data/videos:/app/input:ro \
    deepstream-yolo11:latest
```

### Important Notes

- **TensorRT Engines**: GPU-specific, ~400MB each, must be rebuilt for different GPUs
- **Models**: YOLO11x.pt (~220MB) and YOLO11x.onnx (~440MB) can be downloaded at runtime
- **Logs**: Mount to persist logs outside container

---

## Environment Variables

### GPU and CUDA

| Variable | Default | Description |
|----------|---------|-------------|
| `CUDA_VISIBLE_DEVICES` | all | GPU device IDs |
| `NVIDIA_VISIBLE_DEVICES` | all | NVIDIA devices to expose |
| `NVIDIA_DRIVER_CAPABILITIES` | all | Driver capabilities |
| `CUDA_HOME` | /usr/local/cuda-12.8 | CUDA installation path |

### DeepStream

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSTREAM_DIR` | /opt/nvidia/deepstream/deepstream-8.0 | DeepStream path |
| `GST_DEBUG` | 1 | GStreamer debug level (0-9) |
| `GST_PLUGIN_PATH` | (auto) | GStreamer plugins path |

### Display and GUI

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY` | :0 | X11 display server |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | 1 | Disable Python output buffering |
| `TZ` | America/Los_Angeles | Timezone |

### Setting Environment Variables

```bash
# Via script
CUDA_VISIBLE_DEVICES=0 GST_DEBUG=3 ./scripts/docker-run.sh

# Docker run
docker run -e GST_DEBUG=3 -e TZ=UTC ...

# Docker Compose - in docker-compose.yml or .env file
```

---

## Common Use Cases

### 1. First Time Setup - Build Engine

```bash
# Start container
./scripts/docker-run.sh

# Inside container - auto-detect and build engine
python3 engines/auto_build_engine.py

# Or specify model
python3 engines/auto_build_engine.py --onnx /app/engines/yolo11x.onnx
```

### 2. Run DeepStream Application

```bash
# Interactive mode with display
./scripts/docker-run.sh python3 deepstream_api/main.py

# Low latency mode
./scripts/docker-run.sh python3 deepstream_api/main_low_latency.py

# Headless (no GUI)
docker run -d --gpus all \
    -p 8554:8554 \
    -v $(pwd)/engines:/app/engines \
    deepstream-yolo11:latest \
    python3 deepstream_api/main_headless.py
```

### 3. Development Workflow

```bash
# Start development container
./scripts/docker-dev.sh

# Inside container - code changes are reflected immediately
vim deepstream_api/modules/camera_config.py
python3 deepstream_api/main.py
```

### 4. Process RTSP Stream

```bash
docker run -d --gpus all \
    --name deepstream-rtsp \
    -p 8554:8554 \
    -v $(pwd)/engines:/app/engines \
    -e RTSP_URL=rtsp://camera.local:554/stream \
    deepstream-yolo11:latest \
    python3 deepstream_api/main_headless.py
```

### 5. Batch Processing Videos

```bash
docker run --rm --gpus all \
    -v $(pwd)/videos:/app/videos:ro \
    -v $(pwd)/output:/app/output \
    -v $(pwd)/engines:/app/engines \
    deepstream-yolo11:latest \
    python3 process_videos.py --input /app/videos --output /app/output
```

### 6. Multi-Camera Setup

```bash
# Use docker-compose with configuration
docker-compose --profile production up -d deepstream-headless

# Or custom run
docker run -d --gpus all \
    -p 8554:8554 \
    -v $(pwd)/configs/cameras.json:/app/configs/cameras.json \
    -v $(pwd)/engines:/app/engines \
    deepstream-yolo11:latest \
    python3 deepstream_api/main_headless.py
```

---

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA driver on host
nvidia-smi

# Check nvidia-docker2 installation
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Restart Docker daemon
sudo systemctl restart docker
```

### X11 Display Issues

```bash
# Enable X11 forwarding
xhost +local:docker

# Check DISPLAY variable
echo $DISPLAY

# Run with explicit display
docker run -e DISPLAY=:0 -e XAUTHORITY=$XAUTHORITY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $XAUTHORITY:/root/.Xauthority:ro \
    ...
```

### TensorRT Engine Build Fails

```bash
# Check GPU memory
nvidia-smi

# Build with smaller workspace
python3 engines/auto_build_engine.py --workspace 4096

# Use FP32 instead of FP16
python3 engines/auto_build_engine.py --no-fp16
```

### GStreamer Errors

```bash
# Increase debug level
GST_DEBUG=3 ./scripts/docker-run.sh

# Check plugins
docker run --rm --gpus all deepstream-yolo11:latest \
    gst-inspect-1.0 nvstreammux

# Verify DeepStream installation
docker run --rm --gpus all deepstream-yolo11:latest \
    deepstream-app --version-all
```

### Permission Issues

```bash
# Fix volume permissions
sudo chown -R $USER:$USER engines/ logs/ output/

# Run as current user
docker run --user $(id -u):$(id -g) ...
```

### Container Exits Immediately

```bash
# Check logs
docker logs deepstream-yolo11-app

# Run with interactive shell
docker run -it --entrypoint bash deepstream-yolo11:latest

# Check health
docker inspect --format='{{.State.Health}}' deepstream-yolo11-app
```

---

## Performance Optimization

### 1. TensorRT Optimization

```bash
# Build engine with optimal settings
python3 engines/auto_build_engine.py \
    --workspace 8192 \
    --fp16  # Enable FP16 precision

# For RTX 3090/3080 - enable optimizations
python3 engines/auto_build_engine.py --workspace 16384
```

### 2. GStreamer Tuning

```bash
# Reduce latency
export GST_DEBUG=0  # Disable debug output

# In configuration files
# Set buffer sizes appropriately
```

### 3. GPU Memory Management

```bash
# Limit GPU memory for multi-container setups
docker run --gpus '"device=0"' \
    --memory 8g \
    --memory-swap 16g \
    ...
```

### 4. CPU Affinity

```bash
# Pin to specific CPUs
docker run --cpuset-cpus="0-7" ...
```

### 5. Network Performance

```bash
# Use host network for better performance
docker run --network host ...
```

---

## Production Deployment

### 1. Using Docker Compose (Recommended)

```bash
# Deploy headless service
docker-compose --profile production up -d deepstream-headless

# Scale if needed (with orchestrator)
docker-compose --profile production up -d --scale deepstream-headless=2
```

### 2. Auto-Restart on Failure

```bash
docker run -d --restart unless-stopped \
    --gpus all \
    deepstream-yolo11:latest \
    python3 deepstream_api/main_headless.py
```

### 3. Health Monitoring

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Inspect health
docker inspect --format='{{.State.Health.Status}}' container-name
```

### 4. Logging

```bash
# Use Docker logging drivers
docker run -d \
    --log-driver json-file \
    --log-opt max-size=100m \
    --log-opt max-file=10 \
    ...

# Or mount logs volume
docker run -v $(pwd)/logs:/app/logs ...
```

### 5. Resource Limits

```bash
docker run -d \
    --gpus all \
    --memory 8g \
    --memory-swap 16g \
    --cpus 8 \
    --pids-limit 200 \
    ...
```

### 6. Security

```bash
# Run as non-root user
docker run --user 1000:1000 ...

# Use read-only filesystem where possible
docker run --read-only \
    -v /app/engines:/app/engines \
    -v /tmp:/tmp \
    ...

# Drop capabilities
docker run --cap-drop=ALL --cap-add=SYS_ADMIN ...
```

### 7. Registry Push

```bash
# Tag for registry
docker tag deepstream-yolo11:latest ghcr.io/youruser/deepstream-yolo11:latest

# Push
docker push ghcr.io/youruser/deepstream-yolo11:latest

# Pull on deployment server
docker pull ghcr.io/youruser/deepstream-yolo11:latest
```

---

## Additional Resources

- [NVIDIA DeepStream Documentation](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Overview.html)
- [DeepStream-Yolo GitHub](https://github.com/marcoslucianops/DeepStream-Yolo)
- [Ultralytics YOLO11](https://docs.ultralytics.com/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)

---

## Support and Contributing

For issues, questions, or contributions:

1. Check the troubleshooting section
2. Review application logs in `logs/`
3. Check container logs: `docker logs container-name`
4. Inspect GPU status: `nvidia-smi`

---

**Last Updated**: 2025-11-20
**DeepStream Version**: 8.0.0
**CUDA Version**: 12.8
**Platform**: x86_64
