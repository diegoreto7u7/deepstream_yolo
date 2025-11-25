#!/bin/bash
# ==============================================================================
# Docker Development Script for DeepStream 8.0 + YOLO11x
# Runs container in development mode with source code mounted
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="${IMAGE_NAME:-deepstream-yolo11}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="${CONTAINER_NAME:-deepstream-yolo11-dev}"

# GPU selection (default: all GPUs)
GPU_DEVICES="${GPU_DEVICES:-all}"

# API configuration
API_URL="${API_URL:-http://localhost/api}"

# Detect OS for SELinux configuration
OS_ID=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID=$ID
fi

# Determine if SELinux is enabled (RedHat/Rocky/CentOS/Fedora)
SELINUX_ENABLED=false
if [[ "$OS_ID" == "rhel" ]] || [[ "$OS_ID" == "centos" ]] || [[ "$OS_ID" == "rocky" ]] || [[ "$OS_ID" == "almalinux" ]] || [[ "$OS_ID" == "fedora" ]]; then
    if command -v getenforce &> /dev/null && [ "$(getenforce 2>/dev/null)" == "Enforcing" ]; then
        SELINUX_ENABLED=true
    fi
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}=========================================================================${NC}"
echo -e "${BLUE}DeepStream Development Environment${NC}"
echo -e "${BLUE}=========================================================================${NC}"
echo ""

# Display configuration
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Mode:           ${YELLOW}DEVELOPMENT${NC}"
echo -e "  Image:          ${YELLOW}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo -e "  Container Name: ${YELLOW}${CONTAINER_NAME}${NC}"
echo -e "  GPU Devices:    ${YELLOW}${GPU_DEVICES}${NC}"
echo -e "  Project Root:   ${YELLOW}${PROJECT_ROOT}${NC}"
echo -e "  API URL:        ${YELLOW}${API_URL}${NC}"
if [ "$SELINUX_ENABLED" = true ]; then
    echo -e "  SELinux:        ${YELLOW}Enabled (RedHat configuration applied)${NC}"
fi
echo ""

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
    echo -e "${RED}Error: Docker image not found: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo -e "${YELLOW}Please build the image first:${NC}"
    echo -e "  ${YELLOW}./scripts/docker-build.sh${NC}"
    exit 1
fi

# Check NVIDIA GPU availability
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}Error: nvidia-smi not found. NVIDIA GPU drivers may not be installed.${NC}"
    exit 1
fi

# Display GPU information
echo -e "${GREEN}Available GPUs:${NC}"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader | nl -v 0
echo ""

# Enable X11 forwarding
echo -e "${GREEN}Enabling X11 forwarding...${NC}"
xhost +local:docker &> /dev/null || echo -e "${YELLOW}Warning: Could not enable X11 forwarding${NC}"

# Remove existing container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Removing existing container: ${CONTAINER_NAME}${NC}"
    docker rm -f "${CONTAINER_NAME}" 2>/dev/null || true
fi

# Create necessary directories
echo -e "${GREEN}Ensuring directories exist...${NC}"
mkdir -p "${PROJECT_ROOT}/engines/tensorrt"
mkdir -p "${PROJECT_ROOT}/engines/pt"
mkdir -p "${PROJECT_ROOT}/engines/onnx"
mkdir -p "${PROJECT_ROOT}/logs"
mkdir -p "${PROJECT_ROOT}/output"
mkdir -p "${PROJECT_ROOT}/recordings"

echo ""
echo -e "${YELLOW}=========================================================================${NC}"
echo -e "${YELLOW}DEVELOPMENT MODE NOTES:${NC}"
echo -e "${YELLOW}=========================================================================${NC}"
echo -e "${YELLOW}  - Source code is mounted from host${NC}"
echo -e "${YELLOW}  - Changes to code are reflected immediately${NC}"
echo -e "${YELLOW}  - Container is removed on exit (--rm)${NC}"
echo -e "${YELLOW}  - All engines and logs are persisted via volumes${NC}"
echo ""
echo -e "${GREEN}Starting development container...${NC}"
echo -e "${BLUE}=========================================================================${NC}"
echo ""

# Build GPU flag
if [ "${GPU_DEVICES}" = "all" ]; then
    GPU_FLAG="--gpus all"
else
    GPU_FLAG="--gpus device=${GPU_DEVICES}"
fi

# Build SELinux security options for RedHat/Rocky/CentOS
SECURITY_OPTS="--security-opt seccomp=unconfined"
if [ "$SELINUX_ENABLED" = true ]; then
    echo -e "${YELLOW}Applying SELinux configuration for RedHat/Rocky/CentOS...${NC}"
    SECURITY_OPTS="${SECURITY_OPTS} --security-opt label=type:container_runtime_t"
fi

# Detect timezone
TIMEZONE="${TZ:-$(cat /etc/timezone 2>/dev/null || echo 'Europe/Madrid')}"

# Run container in development mode
docker run -it --rm \
    ${GPU_FLAG} \
    --name "${CONTAINER_NAME}" \
    --network host \
    --ipc=host \
    ${SECURITY_OPTS} \
    -e DISPLAY="${DISPLAY:-:0}" \
    -e NVIDIA_VISIBLE_DEVICES="${GPU_DEVICES}" \
    -e NVIDIA_DRIVER_CAPABILITIES=all \
    -e CUDA_VISIBLE_DEVICES="${GPU_DEVICES}" \
    -e GST_DEBUG="${GST_DEBUG:-2}" \
    -e API_URL="${API_URL}" \
    -e TZ="${TIMEZONE}" \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e TZ="$(cat /etc/timezone 2>/dev/null || echo 'America/Los_Angeles')" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${PROJECT_ROOT}:/app" \
    -w /app \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    bash -c '
        echo ""
        echo "=========================================================================="
        echo "  DEVELOPMENT ENVIRONMENT READY"
        echo "=========================================================================="
        echo ""
        echo "Available Commands:"
        echo ""
        echo "  Build TensorRT Engine:"
        echo "    python3 engines/auto_build_engine.py"
        echo ""
        echo "  Run DeepStream Application:"
        echo "    python3 deepstream_api/main.py"
        echo "    python3 deepstream_api/main_low_latency.py"
        echo "    python3 deepstream_api/main_headless.py"
        echo ""
        echo "  Test GPU:"
        echo "    nvidia-smi"
        echo "    python3 -c \"import torch; print(torch.cuda.is_available())\""
        echo ""
        echo "  Check DeepStream:"
        echo "    gst-inspect-1.0 nvstreammux"
        echo "    deepstream-app --version-all"
        echo ""
        echo "  View Logs:"
        echo "    tail -f logs/*.log"
        echo ""
        echo "=========================================================================="
        echo ""
        exec bash
    '

# Exit code
EXIT_CODE=$?

# Cleanup X11
xhost -local:docker &> /dev/null || true

echo ""
if [ ${EXIT_CODE} -eq 0 ]; then
    echo -e "${GREEN}Development session ended${NC}"
else
    echo -e "${RED}Container exited with code: ${EXIT_CODE}${NC}"
fi

exit ${EXIT_CODE}

# ==============================================================================
# Usage Examples:
# ==============================================================================
# Start development environment:
#   ./scripts/docker-dev.sh
#
# Use specific GPU:
#   GPU_DEVICES=0 ./scripts/docker-dev.sh
#
# Use custom image:
#   IMAGE_NAME=my-deepstream IMAGE_TAG=dev ./scripts/docker-dev.sh
#
# Alternative using docker-compose:
#   docker-compose --profile dev up deepstream-dev
# ==============================================================================
