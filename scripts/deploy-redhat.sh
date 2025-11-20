#!/bin/bash
#
# deploy-redhat.sh
#
# Script de despliegue para RedHat/Rocky/CentOS
# Inicia el container en modo daemon (background) con todas las configuraciones
# específicas de RedHat, incluyendo SELinux.
#
# Uso:
#   ./scripts/deploy-redhat.sh
#   API_URL=http://172.80.20.22/api ./scripts/deploy-redhat.sh
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
IMAGE_NAME="${IMAGE_NAME:-deepstream-yolo11}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="${CONTAINER_NAME:-deepstream-yolo}"
API_URL="${API_URL:-http://localhost/api}"
TIMEZONE="${TZ:-Europe/Madrid}"
GPU_DEVICES="${GPU_DEVICES:-all}"
GST_DEBUG="${GST_DEBUG:-2}"

# Detectar directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DeepStream Deployment Script for RedHat/Rocky/CentOS         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que estamos en RedHat/Rocky/CentOS
OS_ID=""
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID=$ID
fi

if [[ "$OS_ID" != "rhel" ]] && [[ "$OS_ID" != "centos" ]] && [[ "$OS_ID" != "rocky" ]] && [[ "$OS_ID" != "almalinux" ]]; then
    echo -e "${YELLOW}   Warning: This script is optimized for RedHat/Rocky/CentOS${NC}"
    echo -e "${YELLOW}   Detected OS: $PRETTY_NAME${NC}"
    echo -e "${YELLOW}   Continuing anyway...${NC}"
    echo ""
fi

# Mostrar configuración
echo -e "${GREEN}Deployment Configuration:${NC}"
echo -e "  OS:             ${YELLOW}${PRETTY_NAME}${NC}"
echo -e "  Image:          ${YELLOW}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo -e "  Container:      ${YELLOW}${CONTAINER_NAME}${NC}"
echo -e "  API URL:        ${YELLOW}${API_URL}${NC}"
echo -e "  Timezone:       ${YELLOW}${TIMEZONE}${NC}"
echo -e "  GPU Devices:    ${YELLOW}${GPU_DEVICES}${NC}"
echo -e "  Project Root:   ${YELLOW}${PROJECT_ROOT}${NC}"
echo -e "  GST Debug:      ${YELLOW}${GST_DEBUG}${NC}"
echo ""

# Verificar SELinux
if command -v getenforce &> /dev/null; then
    SELINUX_STATUS=$(getenforce 2>/dev/null || echo "Unknown")
    echo -e "${GREEN}SELinux Status:${NC} ${YELLOW}${SELINUX_STATUS}${NC}"
    if [ "$SELINUX_STATUS" == "Enforcing" ]; then
        echo -e "${GREEN}✓ Applying SELinux security configuration${NC}"
        SELINUX_OPT="--security-opt label=type:container_runtime_t"
    else
        SELINUX_OPT=""
    fi
else
    echo -e "${YELLOW}SELinux not detected${NC}"
    SELINUX_OPT=""
fi
echo ""

# Verificar prerequisitos
echo -e "${YELLOW}[1/5] Checking prerequisites...${NC}"

# Verificar NVIDIA drivers
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}✗ Error: NVIDIA drivers not found (nvidia-smi not available)${NC}"
    echo -e "${YELLOW}Run: sudo ./scripts/install-nvidia-prerequisites.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ NVIDIA drivers found${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Error: Docker not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC}"

# Verificar imagen
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
    echo -e "${RED}✗ Error: Docker image not found: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    echo -e "${YELLOW}Build the image first: ./scripts/docker-build.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker image found${NC}"

# Verificar GPU
echo -e "${GREEN}Available GPUs:${NC}"
nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader | nl -v 0
echo ""

# Habilitar X11 forwarding
echo -e "${YELLOW}[2/5] Enabling X11 forwarding...${NC}"
xhost +local:docker &> /dev/null || echo -e "${YELLOW}⚠ Could not enable X11 forwarding (may not have DISPLAY)${NC}"
echo ""

# Detener container anterior si existe
echo -e "${YELLOW}[3/5] Checking for existing container...${NC}"
if docker ps -a | grep -q ${CONTAINER_NAME}; then
    echo -e "${YELLOW}Stopping and removing existing container: ${CONTAINER_NAME}${NC}"
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
    echo -e "${GREEN}✓ Old container removed${NC}"
else
    echo -e "${GREEN}✓ No existing container found${NC}"
fi
echo ""

# Crear directorios necesarios
echo -e "${YELLOW}[4/5] Creating directories...${NC}"
mkdir -p "${PROJECT_ROOT}/engines/tensorrt"
mkdir -p "${PROJECT_ROOT}/engines/pt"
mkdir -p "${PROJECT_ROOT}/engines/onnx"
mkdir -p "${PROJECT_ROOT}/logs"
mkdir -p "${PROJECT_ROOT}/output"
mkdir -p "${PROJECT_ROOT}/recordings"
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Iniciar container
echo -e "${YELLOW}[5/5] Starting DeepStream container in daemon mode...${NC}"
echo ""

docker run -d -it \
  --name ${CONTAINER_NAME} \
  --gpus ${GPU_DEVICES} \
  --net=host \
  --ipc=host \
  --restart unless-stopped \
  -e DISPLAY=${DISPLAY:-:0} \
  -e NVIDIA_VISIBLE_DEVICES=${GPU_DEVICES} \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e GST_DEBUG=${GST_DEBUG} \
  -e API_URL=${API_URL} \
  -e TZ=${TIMEZONE} \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v ${PROJECT_ROOT}/engines:/app/engines \
  -v ${PROJECT_ROOT}/configs:/app/configs \
  -v ${PROJECT_ROOT}/logs:/app/logs \
  -v ${PROJECT_ROOT}/output:/app/output \
  -v ${PROJECT_ROOT}/recordings:/app/recordings \
  --security-opt seccomp=unconfined \
  ${SELINUX_OPT} \
  --workdir /app/deepstream_api \
  ${IMAGE_NAME}:${IMAGE_TAG} \
  bash

# Verificar que el container está corriendo
sleep 3
if docker ps | grep -q ${CONTAINER_NAME}; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ DeepStream container deployed successfully!                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Container Information:${NC}"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo -e "  View logs:          ${GREEN}docker logs -f ${CONTAINER_NAME}${NC}"
    echo -e "  Access container:   ${GREEN}docker exec -it ${CONTAINER_NAME} bash${NC}"
    echo -e "  Stop container:     ${GREEN}docker stop ${CONTAINER_NAME}${NC}"
    echo -e "  Restart container:  ${GREEN}docker restart ${CONTAINER_NAME}${NC}"
    echo -e "  Remove container:   ${GREEN}docker rm -f ${CONTAINER_NAME}${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo -e "  1. Access the container:"
    echo -e "     ${GREEN}docker exec -it ${CONTAINER_NAME} bash${NC}"
    echo ""
    echo -e "  2. Build TensorRT engine (first time only):"
    echo -e "     ${GREEN}python3 /app/engines/auto_build_engine.py${NC}"
    echo ""
    echo -e "  3. Run DeepStream application:"
    echo -e "     ${GREEN}python3 /app/deepstream_api/main_low_latency.py${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Error: Container failed to start${NC}"
    echo -e "${YELLOW}Check logs with: docker logs ${CONTAINER_NAME}${NC}"
    exit 1
fi

# ==============================================================================
# Usage Examples:
# ==============================================================================
# Basic deployment with defaults:
#   ./scripts/deploy-redhat.sh
#
# Deploy with custom API URL:
#   API_URL=http://172.80.20.22/api ./scripts/deploy-redhat.sh
#
# Deploy with custom timezone:
#   TZ=America/New_York ./scripts/deploy-redhat.sh
#
# Deploy with specific GPU:
#   GPU_DEVICES=0 ./scripts/deploy-redhat.sh
#
# Deploy with multiple configurations:
#   API_URL=http://172.80.20.22/api TZ=Europe/Madrid GPU_DEVICES=all ./scripts/deploy-redhat.sh
#
# Deploy with custom container name:
#   CONTAINER_NAME=deepstream-prod ./scripts/deploy-redhat.sh
# ==============================================================================
