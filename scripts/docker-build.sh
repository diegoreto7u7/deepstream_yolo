#!/bin/bash
# ==============================================================================
# Docker Build Script for DeepStream 8.0 + YOLO11x
# Platform: x86_64 with NVIDIA GPUs
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
DOCKERFILE="${DOCKERFILE:-Dockerfile.x86}"
BUILD_CONTEXT="${BUILD_CONTEXT:-..}"

# Build arguments
CUDA_VER="${CUDA_VER:-12.8}"
TENSORRT_VER="${TENSORRT_VER:-10.7.0}"

echo -e "${BLUE}=========================================================================${NC}"
echo -e "${BLUE}Building DeepStream 8.0 + YOLO11x Docker Image${NC}"
echo -e "${BLUE}=========================================================================${NC}"
echo ""

# Display configuration
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Image Name:    ${YELLOW}${IMAGE_NAME}${NC}"
echo -e "  Image Tag:     ${YELLOW}${IMAGE_TAG}${NC}"
echo -e "  Dockerfile:    ${YELLOW}${DOCKERFILE}${NC}"
echo -e "  Build Context: ${YELLOW}${BUILD_CONTEXT}${NC}"
echo -e "  CUDA Version:  ${YELLOW}${CUDA_VER}${NC}"
echo -e "  TensorRT Ver:  ${YELLOW}${TENSORRT_VER}${NC}"
echo ""

# Check if Dockerfile exists
if [ ! -f "${BUILD_CONTEXT}/${DOCKERFILE}" ]; then
    echo -e "${RED}Error: Dockerfile not found: ${BUILD_CONTEXT}/${DOCKERFILE}${NC}"
    exit 1
fi

# Check Docker availability
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check NVIDIA Docker runtime
if ! docker info 2>/dev/null | grep -q nvidia; then
    echo -e "${YELLOW}Warning: NVIDIA Docker runtime not detected${NC}"
    echo -e "${YELLOW}Make sure nvidia-docker2 is installed and configured${NC}"
fi

# Optional: Clean old images
read -p "Do you want to remove old images with the same tag? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Removing old images...${NC}"
    docker rmi ${IMAGE_NAME}:${IMAGE_TAG} 2>/dev/null || true
fi

# Start build
echo ""
echo -e "${GREEN}Starting Docker build...${NC}"
echo -e "${BLUE}=========================================================================${NC}"
echo ""

# Build with BuildKit for better performance
export DOCKER_BUILDKIT=1

# Build command with all options
docker build \
    --file "${BUILD_CONTEXT}/${DOCKERFILE}" \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    --tag "${IMAGE_NAME}:8.0" \
    --build-arg CUDA_VER="${CUDA_VER}" \
    --build-arg TENSORRT_VER="${TENSORRT_VER}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    "${BUILD_CONTEXT}"

# Check build status
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${BLUE}=========================================================================${NC}"
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo -e "${BLUE}=========================================================================${NC}"
    echo ""

    # Display image information
    echo -e "${GREEN}Image Details:${NC}"
    docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}"
    echo ""

    # Display next steps
    echo -e "${GREEN}Next Steps:${NC}"
    echo ""
    echo -e "  1. Run interactively with GUI:"
    echo -e "     ${YELLOW}./scripts/docker-run.sh${NC}"
    echo ""
    echo -e "  2. Run in development mode:"
    echo -e "     ${YELLOW}./scripts/docker-dev.sh${NC}"
    echo ""
    echo -e "  3. Use docker-compose:"
    echo -e "     ${YELLOW}docker-compose up deepstream-app${NC}"
    echo ""
    echo -e "  4. Build TensorRT engine:"
    echo -e "     ${YELLOW}docker run -it --gpus all -v \$(pwd)/engines:/app/engines ${IMAGE_NAME}:${IMAGE_TAG} python3 engines/auto_build_engine.py${NC}"
    echo ""
    echo -e "  5. Run headless mode:"
    echo -e "     ${YELLOW}docker run -d --gpus all -p 8554:8554 ${IMAGE_NAME}:${IMAGE_TAG} python3 deepstream_api/main_headless.py${NC}"
    echo ""

else
    echo ""
    echo -e "${RED}=========================================================================${NC}"
    echo -e "${RED}Build failed!${NC}"
    echo -e "${RED}=========================================================================${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Check Dockerfile syntax"
    echo -e "  2. Verify internet connection (for package downloads)"
    echo -e "  3. Check disk space: ${YELLOW}df -h${NC}"
    echo -e "  4. Review build logs above"
    echo ""
    exit 1
fi

# Optional: Push to registry
echo ""
read -p "Do you want to push the image to a registry? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter registry URL (e.g., ghcr.io/username): " REGISTRY
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        echo -e "${YELLOW}Tagging image as ${FULL_IMAGE}${NC}"
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE}"

        echo -e "${YELLOW}Pushing to registry...${NC}"
        docker push "${FULL_IMAGE}"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Successfully pushed to ${FULL_IMAGE}${NC}"
        else
            echo -e "${RED}Failed to push to registry${NC}"
        fi
    fi
fi

echo ""
echo -e "${BLUE}=========================================================================${NC}"
echo -e "${GREEN}Build process completed!${NC}"
echo -e "${BLUE}=========================================================================${NC}"
echo ""

# ==============================================================================
# Usage Examples:
# ==============================================================================
# Basic build:
#   ./scripts/docker-build.sh
#
# Custom image name and tag:
#   IMAGE_NAME=my-deepstream IMAGE_TAG=v1.0 ./scripts/docker-build.sh
#
# Custom Dockerfile:
#   DOCKERFILE=Dockerfile.custom ./scripts/docker-build.sh
#
# Build with specific CUDA version:
#   CUDA_VER=12.6 ./scripts/docker-build.sh
# ==============================================================================
