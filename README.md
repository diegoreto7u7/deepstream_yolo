# DeepStream 8.0 + YOLO11x - Docker Setup

Complete Docker containerization for DeepStream 8.0 with YOLO11x object detection on x86 platforms (RTX 3090/3080, TESLA T4/V100).

## 🚀 Quick Start

```bash
# 1. Build Docker image
./scripts/docker-build.sh

# 2. Run container
./scripts/docker-run.sh

# 3. Inside container - build TensorRT engine (first time only)
python3 engines/auto_build_engine.py

# 4. Run DeepStream application
python3 deepstream_api/main_low_latency.py
```

## 📋 System Requirements

- **Platform**: x86_64 (Intel/AMD)
- **GPU**: NVIDIA RTX 3090/3080, TESLA T4/V100/A100
- **Host OS**: Ubuntu 20.04+, Debian 11+, RHEL 8+, Rocky Linux 8+
- **Requirements on Host**:
  - NVIDIA GPU Drivers ≥ 525.60.13
  - Docker Engine ≥ 19.03
  - nvidia-container-toolkit

## 🔧 Fresh System Setup

If you're setting up on a **fresh system without NVIDIA/CUDA libraries**:

```bash
# Install prerequisites automatically
sudo ./scripts/install-nvidia-prerequisites.sh

# Reboot (if drivers were installed)
sudo reboot

# Build and run
./scripts/docker-build.sh
./scripts/docker-run.sh
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[SETUP_FRESH_SYSTEM.md](SETUP_FRESH_SYSTEM.md)** | Setup on fresh system without NVIDIA |
| **[DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)** | 5-minute quick start guide |
| **[docs/DOCKER.md](docs/DOCKER.md)** | Complete Docker reference |
| **[docs/HOST_SETUP.md](docs/HOST_SETUP.md)** | Host prerequisites setup |
| **[docs/REDHAT_DEPLOYMENT.md](docs/REDHAT_DEPLOYMENT.md)** | RedHat/Rocky specific guide |
| **[DEPENDENCY_VERSIONS_CORRECTED.md](DEPENDENCY_VERSIONS_CORRECTED.md)** | Dependency versions reference |

## 🎯 Project Features

- ✅ **Auto-Build TensorRT Engine** - Detects GPU and builds optimized engine automatically
- ✅ **Multi-Camera Support** - Process up to 16 cameras simultaneously
- ✅ **RedHat Compatible** - Works on Ubuntu, Debian, RHEL, Rocky Linux
- ✅ **SELinux Support** - Auto-detects and configures SELinux for X11 display
- ✅ **Persistent Storage** - TensorRT engines persist across container restarts
- ✅ **Production Ready** - CI/CD, health checks, security scanning

## 🛠️ Available Scripts

| Script | Description |
|--------|-------------|
| `./scripts/docker-build.sh` | Build Docker image |
| `./scripts/docker-run.sh` | Run interactive container |
| `./scripts/docker-dev.sh` | Run in development mode (source mounted) |
| `./scripts/deploy-redhat.sh` | Deploy in daemon mode (RedHat optimized) |
| `./scripts/docker-utils.sh` | Utility commands (logs, stats, health, etc.) |
| `./scripts/install-nvidia-prerequisites.sh` | Install NVIDIA drivers + nvidia-docker |

## 🐳 Docker Commands

```bash
# Build image
./scripts/docker-build.sh

# Run interactive
./scripts/docker-run.sh

# Run with custom API URL
API_URL=http://172.80.20.22/api ./scripts/docker-run.sh

# Run in background (daemon)
./scripts/deploy-redhat.sh

# Development mode (live code editing)
./scripts/docker-dev.sh

# Using docker-compose
docker-compose up deepstream-app
```

## 🔍 Troubleshooting

### Build fails with "CUDA 12.8 not found"
- **Fixed**: Use `./scripts/docker-build.sh` (uses correct Dockerfile.x86)
- Correct versions: CUDA 12.2, TensorRT 8.6.1

### "nvidia-smi: command not found"
- **Solution**: Install NVIDIA drivers
  ```bash
  sudo ./scripts/install-nvidia-prerequisites.sh
  sudo reboot
  ```

### "cannot open display :0" on RedHat
- **Solution**: Already handled automatically by scripts
- Scripts detect SELinux and apply `--security-opt label=type:container_runtime_t`

### More troubleshooting
- See [docs/DOCKER.md - Troubleshooting](docs/DOCKER.md#troubleshooting)
- See [docs/REDHAT_DEPLOYMENT.md](docs/REDHAT_DEPLOYMENT.md) for RedHat-specific issues

## 📊 Technology Stack

| Component | Version |
|-----------|---------|
| **DeepStream** | 8.0.0 |
| **CUDA** | 12.2 |
| **TensorRT** | 8.6.1 |
| **Python** | 3.10 |
| **YOLO** | 11x (Ultralytics) |
| **GStreamer** | 1.20.x |

## 🌐 OS Compatibility

The Docker container (Ubuntu 24.04) works on **any Linux host**:

| Host OS | Container OS | Compatible? |
|---------|--------------|-------------|
| Ubuntu 20.04+ | Ubuntu 24.04 | ✅ Yes |
| Debian 11+ | Ubuntu 24.04 | ✅ Yes |
| **RHEL 8/9** | Ubuntu 24.04 | ✅ Yes |
| **Rocky Linux 8/9** | Ubuntu 24.04 | ✅ Yes |
| CentOS Stream 8+ | Ubuntu 24.04 | ✅ Yes |

**Key Point**: The container is always Ubuntu 24.04, regardless of host OS. Host only needs NVIDIA drivers + Docker.

## 📄 License

See LICENSE file.

## 🤝 Contributing

See CONTRIBUTING.md for development guidelines.

## 📧 Support

For issues and questions:
- Check [docs/DOCKER.md](docs/DOCKER.md)
- See troubleshooting guides
- Open an issue on GitHub

---

**Version**: 2.0
**Last Updated**: 2025-11-20
**Platform**: x86_64 with NVIDIA GPUs
