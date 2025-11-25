# DeepStream 8.0 + YOLO11x - Docker Quick Start

Fast-track guide to get up and running with DeepStream in Docker.

## Prerequisites Checklist

- [ ] NVIDIA GPU (RTX 3090, 3080, 3070, TESLA T4/V100/A100)
- [ ] NVIDIA GPU Drivers installed (`nvidia-smi` works)
- [ ] Docker installed and running
- [ ] NVIDIA Container Toolkit installed (`nvidia-docker2`)
- [ ] X11 enabled (for GUI): `xhost +local:docker`

## 5-Minute Quick Start

### 1. Build Image (5-10 minutes)

```bash
cd /home/diego/Documentos/deepstream/app
./scripts/docker-build.sh
```

### 2. Run Container

```bash
./scripts/docker-run.sh
```

### 3. Build TensorRT Engine (First Time Only - 10-20 minutes)

Inside the container:

```bash
python3 engines/auto_build_engine.py
```

### 4. Run DeepStream Application

```bash
# Low latency mode (recommended)
python3 deepstream_api/main_low_latency.py

# Standard mode
python3 deepstream_api/main.py

# Headless mode (no GUI)
python3 deepstream_api/main_headless.py
```

## Common Commands

### Build

```bash
# Build Docker image
./scripts/docker-build.sh

# Build with docker-compose
docker-compose build
```

### Run

```bash
# Interactive with GUI
./scripts/docker-run.sh

# Development mode (source code mounted)
./scripts/docker-dev.sh

# Headless production
docker-compose --profile production up -d deepstream-headless

# Specific GPU
GPU_DEVICES=0 ./scripts/docker-run.sh
```

### Utilities

```bash
# All-in-one utility script
./scripts/docker-utils.sh help

# Test GPU access
./scripts/docker-utils.sh test-gpu

# View logs
./scripts/docker-utils.sh logs

# Shell into running container
./scripts/docker-utils.sh shell

# Stop all containers
./scripts/docker-utils.sh stop
```

## Docker Compose Profiles

```bash
# Interactive (default)
docker-compose up deepstream-app

# Development
docker-compose --profile dev up deepstream-dev

# Production headless
docker-compose --profile production up -d deepstream-headless

# Low latency
docker-compose --profile lowlatency up deepstream-lowlatency
```

## Environment Variables

```bash
# Use specific GPU
export CUDA_VISIBLE_DEVICES=0

# Increase GStreamer debug
export GST_DEBUG=3

# Custom image name
export IMAGE_NAME=my-deepstream
export IMAGE_TAG=v1.0
```

## Volume Mounts

Data persisted on host:

- `./engines/` - TensorRT engines (~400MB each, GPU-specific)
- `./configs/` - Configuration files
- `./logs/` - Application logs
- `./output/` - Processed videos/images
- `./recordings/` - Recorded streams

## Troubleshooting

### GPU Not Found

```bash
# Test on host
nvidia-smi

# Test in container
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Restart Docker
sudo systemctl restart docker
```

### X11 Display Issues

```bash
# Enable X11
xhost +local:docker

# Check DISPLAY
echo $DISPLAY

# Run with explicit display
DISPLAY=:0 ./scripts/docker-run.sh
```

### Container Won't Start

```bash
# Check logs
docker logs deepstream-yolo11-app

# Interactive troubleshoot
docker run -it --entrypoint bash deepstream-yolo11:latest
```

### Engine Build Fails

```bash
# Inside container
# Smaller workspace (for GPUs with less memory)
python3 engines/auto_build_engine.py --workspace 4096

# Use FP32 instead of FP16
python3 engines/auto_build_engine.py --no-fp16
```

## Next Steps

1. Read full documentation: `docs/DOCKER.md`
2. Customize configurations in `configs/deepstream/`
3. Set up camera streams
4. Deploy to production

## Support

- Documentation: `docs/DOCKER.md`
- Check logs: `./scripts/docker-utils.sh logs`
- GPU status: `nvidia-smi`
- Container health: `./scripts/docker-utils.sh health`

---

**Platform**: x86_64 | **CUDA**: 12.8 | **DeepStream**: 8.0.0 | **GPUs**: RTX 3090/3080/3070, TESLA T4/V100/A100
