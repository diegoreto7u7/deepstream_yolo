# Host System Setup for DeepStream Docker

This guide explains how to set up a **completely fresh system** (without any NVIDIA/CUDA libraries) to run the DeepStream Docker container.

## Table of Contents

- [Overview](#overview)
- [Prerequisites on Host](#prerequisites-on-host)
- [Automated Installation](#automated-installation)
- [Manual Installation](#manual-installation)
- [OS Compatibility](#os-compatibility)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What's Inside the Docker Container?

The Docker container includes:
- ✅ CUDA 12.8
- ✅ cuDNN
- ✅ TensorRT 10.7.0
- ✅ DeepStream 8.0
- ✅ All application dependencies

### What's Needed on the Host?

The **host system** only needs:
1. **NVIDIA GPU Drivers** (525.60.13 or newer for CUDA 12.8)
2. **nvidia-container-toolkit** (formerly nvidia-docker)
3. **Docker** or **Docker Compose**

> **Key Point**: The Docker container has CUDA inside, but the host needs GPU drivers to access the hardware.

### Why This Matters

Docker containers are **OS-independent**, meaning:
- The container runs **Ubuntu 24.04** with DeepStream
- But it works on **any Linux host**: Ubuntu, Debian, RedHat, Rocky Linux, CentOS, etc.
- The host OS only provides the GPU drivers and Docker runtime

---

## Prerequisites on Host

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **GPU** | NVIDIA GPU (RTX 3080/3090, TESLA T4/V100/A100, etc.) |
| **Driver** | NVIDIA Driver ≥ 525.60.13 (for CUDA 12.8 support) |
| **OS** | Linux (Ubuntu 20.04+, Debian 10+, RHEL 8+, Rocky 8+) |
| **Kernel** | Linux kernel with NVIDIA driver support |
| **Docker** | Docker Engine 19.03+ or Docker Compose v2 |
| **nvidia-docker** | nvidia-container-toolkit (latest) |

### Supported Host Operating Systems

The Docker container works on **any** of these host systems:

#### Debian-based
- ✅ Ubuntu 20.04, 22.04, 24.04
- ✅ Debian 10, 11, 12
- ✅ Linux Mint
- ✅ Pop!_OS

#### RedHat-based
- ✅ RHEL 8, 9
- ✅ CentOS Stream 8, 9
- ✅ Rocky Linux 8, 9
- ✅ AlmaLinux 8, 9
- ✅ Oracle Linux 8, 9

---

## Automated Installation

We provide an automated script that installs everything needed on a fresh system.

### Quick Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/deepstream-yolo11x.git
cd deepstream-yolo11x

# 2. Run the automated installer
sudo ./scripts/install-nvidia-prerequisites.sh
```

This script will:
1. ✅ Detect your OS (Ubuntu/Debian/RHEL/Rocky/CentOS)
2. ✅ Check for existing NVIDIA drivers
3. ✅ Install NVIDIA drivers (if needed)
4. ✅ Install nvidia-container-toolkit
5. ✅ Configure Docker to use NVIDIA runtime
6. ✅ Verify the installation

### Script Options

```bash
# Show help
sudo ./scripts/install-nvidia-prerequisites.sh --help

# Skip driver installation (if already installed)
sudo ./scripts/install-nvidia-prerequisites.sh --skip-driver

# Dry run (show what would be installed)
sudo ./scripts/install-nvidia-prerequisites.sh --dry-run
```

### After Installation

If the script installed new drivers, **reboot your system**:

```bash
sudo reboot
```

Then verify the installation:

```bash
# Check NVIDIA driver
nvidia-smi

# Test Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

---

## Manual Installation

If you prefer to install manually or the automated script doesn't work for your system:

### Step 1: Install NVIDIA Driver

#### Ubuntu/Debian

```bash
# Update package list
sudo apt-get update

# Install ubuntu-drivers tool
sudo apt-get install -y ubuntu-drivers-common

# Show available drivers
ubuntu-drivers devices

# Auto-install recommended driver
sudo ubuntu-drivers autoinstall

# Reboot
sudo reboot
```

After reboot, verify:

```bash
nvidia-smi
```

#### RHEL/Rocky/CentOS 8+

```bash
# Install EPEL and development tools
sudo dnf install -y epel-release
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y kernel-devel kernel-headers gcc make dkms

# Add NVIDIA CUDA repository
sudo dnf config-manager --add-repo \
    https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo

# Install NVIDIA driver
sudo dnf clean all
sudo dnf -y module install nvidia-driver:latest-dkms

# Reboot
sudo reboot
```

After reboot, verify:

```bash
nvidia-smi
```

### Step 2: Install Docker

#### Ubuntu/Debian

```bash
# Install Docker using official script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### RHEL/Rocky/CentOS 8+

```bash
# Add Docker repository
sudo dnf config-manager --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

# Install Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 3: Install nvidia-container-toolkit

#### Ubuntu/Debian

```bash
# Add NVIDIA Container Toolkit repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

#### RHEL/Rocky/CentOS 8+

```bash
# Add NVIDIA Container Toolkit repository
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
    sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# Install
sudo dnf clean expire-cache
sudo dnf install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## OS Compatibility

### Host OS vs Container OS

| Host OS | Container OS | Compatible? | Notes |
|---------|--------------|-------------|-------|
| Ubuntu 20.04 | Ubuntu 24.04 | ✅ Yes | Host needs NVIDIA drivers + nvidia-docker |
| Ubuntu 22.04 | Ubuntu 24.04 | ✅ Yes | Host needs NVIDIA drivers + nvidia-docker |
| Debian 11 | Ubuntu 24.04 | ✅ Yes | Host needs NVIDIA drivers + nvidia-docker |
| **RHEL 8** | **Ubuntu 24.04** | ✅ **Yes** | Host needs NVIDIA drivers + nvidia-docker |
| **Rocky 8/9** | **Ubuntu 24.04** | ✅ **Yes** | Host needs NVIDIA drivers + nvidia-docker |
| CentOS Stream 8 | Ubuntu 24.04 | ✅ Yes | Host needs NVIDIA drivers + nvidia-docker |
| AlmaLinux 8/9 | Ubuntu 24.04 | ✅ Yes | Host needs NVIDIA drivers + nvidia-docker |

> **Key Point**: The container OS (Ubuntu 24.04) is completely independent from the host OS. As long as the host has Docker + NVIDIA drivers + nvidia-container-toolkit, it will work.

### Why Docker Containers are OS-Independent

```
┌─────────────────────────────────────────┐
│  DeepStream Container (Ubuntu 24.04)    │
│  - CUDA 12.8                            │
│  - TensorRT 10.7.0                      │
│  - DeepStream 8.0                       │
│  - All app dependencies                 │
└─────────────────────────────────────────┘
                  │
                  │ Docker Engine
                  │
┌─────────────────────────────────────────┐
│  Host System (ANY Linux)                │
│  - Ubuntu / Debian / RHEL / Rocky       │
│  - NVIDIA Drivers (525.60.13+)          │
│  - nvidia-container-toolkit             │
│  - Docker Engine                        │
└─────────────────────────────────────────┘
                  │
                  │ GPU Drivers
                  │
┌─────────────────────────────────────────┐
│  NVIDIA GPU Hardware                    │
│  - RTX 3090 / RTX 3080 / TESLA T4/V100  │
└─────────────────────────────────────────┘
```

### Package Manager Differences

The automated script handles different package managers:

| Host OS | Package Manager | Handled? |
|---------|-----------------|----------|
| Ubuntu/Debian | `apt` | ✅ Yes |
| RHEL 8+ / Rocky 8+ | `dnf` | ✅ Yes |
| CentOS 7 / RHEL 7 | `yum` | ✅ Yes |

---

## Verification

### Check NVIDIA Driver

```bash
# Should show GPU info and driver version
nvidia-smi

# Expected output:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.8    |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |===============================+======================+======================|
# |   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0  On |                  N/A |
# | 30%   45C    P8    25W / 350W |    500MiB / 24576MiB |      0%      Default |
# +-------------------------------+----------------------+----------------------+
```

### Check nvidia-container-toolkit

```bash
# Should show version info
nvidia-ctk --version

# Should show runtime config
docker info | grep -i nvidia
```

### Test GPU Access in Docker

```bash
# Run a test CUDA container
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Should show the same output as 'nvidia-smi' on host
```

### Test with DeepStream Container

```bash
cd /home/diego/Documentos/deepstream/app

# Build the DeepStream image
./scripts/docker-build.sh

# Test GPU access
docker run --rm --gpus all deepstream-yolo11x:latest nvidia-smi
```

---

## Troubleshooting

### Problem: "nvidia-smi: command not found"

**Cause**: NVIDIA driver not installed

**Solution**:
```bash
sudo ./scripts/install-nvidia-prerequisites.sh
sudo reboot
```

### Problem: "docker: Error response from daemon: could not select device driver"

**Cause**: nvidia-container-toolkit not installed or not configured

**Solution**:
```bash
# Install nvidia-container-toolkit
sudo apt-get install -y nvidia-container-toolkit  # Ubuntu/Debian
# OR
sudo dnf install -y nvidia-container-toolkit       # RHEL/Rocky

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Problem: "Failed to initialize NVML: Driver/library version mismatch"

**Cause**: NVIDIA driver was updated but kernel module not reloaded

**Solution**:
```bash
sudo reboot
```

### Problem: "docker: Error response from daemon: Unknown runtime specified nvidia"

**Cause**: Docker not configured to use NVIDIA runtime

**Solution**:
```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Problem: Driver installation fails on RHEL/Rocky

**Cause**: Secure Boot enabled, or nouveau driver conflicts

**Solution**:
```bash
# Disable nouveau driver
echo "blacklist nouveau" | sudo tee /etc/modprobe.d/blacklist-nouveau.conf
echo "options nouveau modeset=0" | sudo tee -a /etc/modprobe.d/blacklist-nouveau.conf
sudo dracut --force
sudo reboot

# For Secure Boot: disable in BIOS, or sign the NVIDIA kernel module
```

### Problem: "CUDA version mismatch"

**Cause**: Driver too old for CUDA 12.8

**Solution**:
```bash
# Check current driver version
nvidia-smi | grep "Driver Version"

# Minimum required: 525.60.13
# Update driver if needed
sudo ubuntu-drivers autoinstall  # Ubuntu
# OR
sudo dnf -y module install nvidia-driver:latest-dkms  # RHEL/Rocky
sudo reboot
```

### Problem: Works on Ubuntu but not on RedHat

**Cause**: Likely SELinux blocking Docker

**Solution**:
```bash
# Check SELinux status
getenforce

# Temporarily disable (for testing)
sudo setenforce 0

# Permanently disable (in /etc/selinux/config)
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
sudo reboot

# OR: Create SELinux policy for Docker+NVIDIA (advanced)
```

---

## Next Steps

After setting up the host system:

1. **Build the DeepStream Docker image**:
   ```bash
   cd /home/diego/Documentos/deepstream/app
   ./scripts/docker-build.sh
   ```

2. **Run the container**:
   ```bash
   ./scripts/docker-run.sh
   ```

3. **Inside the container, build TensorRT engine**:
   ```bash
   python3 engines/auto_build_engine.py
   ```

4. **Run the DeepStream application**:
   ```bash
   python3 deepstream_api/main_low_latency.py
   ```

For more information:
- **Docker usage**: See [docs/DOCKER.md](DOCKER.md)
- **Quick start**: See [DOCKER_QUICKSTART.md](../DOCKER_QUICKSTART.md)
- **Troubleshooting**: See [docs/DOCKER.md#troubleshooting](DOCKER.md#troubleshooting)

---

## Summary

### What You Need on the Host

```
✅ NVIDIA GPU (RTX 3090/3080, TESLA, etc.)
✅ NVIDIA Driver (525.60.13+)
✅ Docker Engine (19.03+)
✅ nvidia-container-toolkit
```

### What's Inside the Container

```
✅ Ubuntu 24.04
✅ CUDA 12.8
✅ TensorRT 10.7.0
✅ DeepStream 8.0
✅ All dependencies
```

### OS Compatibility

```
Host OS: Ubuntu, Debian, RHEL, Rocky, CentOS, AlmaLinux
Container OS: Ubuntu 24.04
Result: ✅ Works on all Linux distros with NVIDIA GPU
```

The key insight: **Docker makes your application portable**. The container always runs Ubuntu 24.04 with DeepStream, regardless of what Linux distribution is running on the host.
