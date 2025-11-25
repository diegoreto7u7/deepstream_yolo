# Setup on Fresh System (No NVIDIA/CUDA Installed)

Quick guide for setting up DeepStream Docker on a **brand new system** without any NVIDIA or CUDA libraries.

## TL;DR - Quick Commands

```bash
# 1. Install NVIDIA drivers + nvidia-docker (automated)
sudo ./scripts/install-nvidia-prerequisites.sh

# 2. Reboot (if drivers were installed)
sudo reboot

# 3. Verify installation
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# 4. Build DeepStream image
./scripts/docker-build.sh

# 5. Run container
./scripts/docker-run.sh
```

## What You Need

### On the Host System (Outside Docker)

✅ **NVIDIA GPU** (RTX 3090, 3080, TESLA T4/V100, etc.)
✅ **NVIDIA Drivers** (≥ 525.60.13)
✅ **Docker Engine** (19.03+)
✅ **nvidia-container-toolkit** (nvidia-docker)

### Inside the Docker Container (Automatic)

✅ **CUDA 12.8** - Included in container
✅ **TensorRT 10.7.0** - Included in container
✅ **DeepStream 8.0** - Included in container
✅ **All dependencies** - Included in container

## Step-by-Step Setup

### Step 1: Install Prerequisites on Host

We provide an **automated script** that works on:
- ✅ Ubuntu 20.04, 22.04, 24.04
- ✅ Debian 10, 11, 12
- ✅ **RHEL 8, 9**
- ✅ **Rocky Linux 8, 9**
- ✅ **CentOS Stream 8, 9**
- ✅ AlmaLinux 8, 9

```bash
cd /home/diego/Documentos/deepstream/app
sudo ./scripts/install-nvidia-prerequisites.sh
```

This script will:
1. Detect your OS (Ubuntu/Debian/RHEL/Rocky/CentOS)
2. Check for existing NVIDIA drivers
3. Install NVIDIA drivers (if needed)
4. Install nvidia-container-toolkit
5. Configure Docker to use NVIDIA runtime

### Step 2: Reboot (if needed)

If the script installed new drivers:

```bash
sudo reboot
```

### Step 3: Verify Installation

After reboot, verify everything works:

```bash
# Test NVIDIA driver
nvidia-smi

# Should show:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.8   |
# +-----------------------------------------------------------------------------+

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Should show the same output as nvidia-smi above
```

### Step 4: Build DeepStream Image

```bash
cd /home/diego/Documentos/deepstream/app

# Build the image (takes 5-10 minutes)
./scripts/docker-build.sh
```

### Step 5: Run Container

```bash
# Run interactive container with GPU access
./scripts/docker-run.sh

# You're now inside the container!
```

### Step 6: Build TensorRT Engine (First Time Only)

Inside the container:

```bash
# This auto-detects your GPU and builds optimized engine
python3 engines/auto_build_engine.py

# Takes 10-20 minutes on first run
# Saves engine to: engines/tensorrt/yolo11x_b1.engine
```

### Step 7: Run DeepStream Application

```bash
# Inside container
python3 deepstream_api/main_low_latency.py
```

## OS Compatibility Matrix

### Does it work on RedHat/Rocky/CentOS?

**YES!** The container is Ubuntu 24.04, but Docker makes it work on **any Linux host**:

| Host OS | Container OS | Works? | Notes |
|---------|--------------|--------|-------|
| Ubuntu 20.04/22.04 | Ubuntu 24.04 | ✅ Yes | Host needs nvidia-docker |
| Debian 11/12 | Ubuntu 24.04 | ✅ Yes | Host needs nvidia-docker |
| **RHEL 8/9** | **Ubuntu 24.04** | ✅ **Yes** | Host needs nvidia-docker |
| **Rocky Linux 8/9** | **Ubuntu 24.04** | ✅ **Yes** | Host needs nvidia-docker |
| CentOS Stream 8/9 | Ubuntu 24.04 | ✅ Yes | Host needs nvidia-docker |

### Why This Works

```
┌─────────────────────────────────────────┐
│  DeepStream Container (Ubuntu 24.04)    │  ← Always Ubuntu
│  - CUDA 12.8 (inside container)         │
│  - DeepStream 8.0 (inside container)    │
└─────────────────────────────────────────┘
                  ↕
          Docker Engine
                  ↕
┌─────────────────────────────────────────┐
│  Host System (ANY Linux)                │  ← Ubuntu, RHEL, Rocky, etc.
│  - NVIDIA Drivers (on host)             │
│  - nvidia-container-toolkit (on host)   │
└─────────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────────┐
│  NVIDIA GPU Hardware                    │
│  - RTX 3090 / RTX 3080 / TESLA          │
└─────────────────────────────────────────┘
```

**Key Point**: The container has CUDA inside. The host only needs GPU drivers + Docker.

## Script Options

### Automated Installer Options

```bash
# Show help
sudo ./scripts/install-nvidia-prerequisites.sh --help

# Skip driver installation (if already installed)
sudo ./scripts/install-nvidia-prerequisites.sh --skip-driver

# Dry run (show what would be installed)
sudo ./scripts/install-nvidia-prerequisites.sh --dry-run
```

### Check What's Missing

```bash
# Check NVIDIA driver
nvidia-smi
# If this fails → need to install driver

# Check Docker
docker --version
# If this fails → need to install Docker

# Check nvidia-docker
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
# If this fails → need nvidia-container-toolkit
```

## Troubleshooting

### Problem: "nvidia-smi: command not found"

**Solution**: Install NVIDIA drivers

```bash
sudo ./scripts/install-nvidia-prerequisites.sh
sudo reboot
```

### Problem: "docker: unknown flag: --gpus"

**Solution**: Docker version too old

```bash
# Update Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Problem: "could not select device driver"

**Solution**: nvidia-container-toolkit not installed

```bash
# Ubuntu/Debian
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# RHEL/Rocky
sudo dnf install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Problem: Works on Ubuntu but not on RedHat

**Likely cause**: SELinux blocking Docker

```bash
# Check SELinux
getenforce

# Temporarily disable (for testing)
sudo setenforce 0

# Test again
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# If it works, SELinux is the issue
# Permanent fix: disable SELinux or create policy
```

## Manual Installation

If the automated script doesn't work, see **[docs/HOST_SETUP.md](docs/HOST_SETUP.md)** for manual installation instructions.

## Next Steps

After setup:

1. **Read Docker guide**: [docs/DOCKER.md](docs/DOCKER.md)
2. **Read quick start**: [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)
3. **Build your first engine**: Inside container, run `python3 engines/auto_build_engine.py`
4. **Run the application**: `python3 deepstream_api/main_low_latency.py`

## Summary

### What the Automated Script Does

```bash
sudo ./scripts/install-nvidia-prerequisites.sh
```

This one command installs:
- ✅ NVIDIA drivers (if not installed)
- ✅ nvidia-container-toolkit
- ✅ Configures Docker for GPU access
- ✅ Works on Ubuntu, Debian, RHEL, Rocky, CentOS

### After Installation

```bash
# 1. Reboot (if drivers were installed)
sudo reboot

# 2. Build image
./scripts/docker-build.sh

# 3. Run container
./scripts/docker-run.sh

# 4. Build engine (inside container)
python3 engines/auto_build_engine.py

# 5. Run app (inside container)
python3 deepstream_api/main_low_latency.py
```

### Host vs Container

| Component | Location | Version |
|-----------|----------|---------|
| **NVIDIA Drivers** | Host | ≥ 525.60.13 |
| **Docker Engine** | Host | ≥ 19.03 |
| **nvidia-docker** | Host | Latest |
| **CUDA** | Container | 12.8 |
| **TensorRT** | Container | 10.7.0 |
| **DeepStream** | Container | 8.0 |
| **Ubuntu** | Container | 24.04 |

The container always runs Ubuntu 24.04 with all dependencies, regardless of host OS.

---

**Need help?** See [docs/HOST_SETUP.md](docs/HOST_SETUP.md) for detailed setup instructions.
