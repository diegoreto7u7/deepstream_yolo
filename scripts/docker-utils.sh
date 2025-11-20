#!/bin/bash
# ==============================================================================
# Docker Utilities for DeepStream 8.0 + YOLO11x
# Common operations and maintenance tasks
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

IMAGE_NAME="${IMAGE_NAME:-deepstream-yolo11}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# ==============================================================================
# Functions
# ==============================================================================

show_help() {
    echo -e "${BLUE}=========================================================================${NC}"
    echo -e "${BLUE}DeepStream Docker Utilities${NC}"
    echo -e "${BLUE}=========================================================================${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo ""
    echo "  ${GREEN}build${NC}          - Build Docker image"
    echo "  ${GREEN}run${NC}            - Run container interactively"
    echo "  ${GREEN}dev${NC}            - Start development environment"
    echo "  ${GREEN}headless${NC}       - Run in headless mode"
    echo "  ${GREEN}shell${NC}          - Open shell in running container"
    echo "  ${GREEN}logs${NC}           - View container logs"
    echo "  ${GREEN}stop${NC}           - Stop running containers"
    echo "  ${GREEN}clean${NC}          - Remove stopped containers"
    echo "  ${GREEN}prune${NC}          - Clean unused Docker resources"
    echo "  ${GREEN}inspect${NC}        - Inspect container configuration"
    echo "  ${GREEN}test-gpu${NC}       - Test GPU access in container"
    echo "  ${GREEN}build-engine${NC}   - Build TensorRT engine in container"
    echo "  ${GREEN}export-image${NC}   - Export image to tar file"
    echo "  ${GREEN}import-image${NC}   - Import image from tar file"
    echo "  ${GREEN}push${NC}           - Push image to registry"
    echo "  ${GREEN}stats${NC}          - Show container resource usage"
    echo "  ${GREEN}health${NC}         - Check container health"
    echo ""
    echo "Environment Variables:"
    echo "  IMAGE_NAME      - Docker image name (default: deepstream-yolo11)"
    echo "  IMAGE_TAG       - Docker image tag (default: latest)"
    echo "  GPU_DEVICES     - GPU devices to use (default: all)"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 run"
    echo "  GPU_DEVICES=0 $0 test-gpu"
    echo ""
}

build_image() {
    echo -e "${GREEN}Building Docker image...${NC}"
    ./docker-build.sh
}

run_container() {
    echo -e "${GREEN}Running container...${NC}"
    ./docker-run.sh "$@"
}

run_dev() {
    echo -e "${GREEN}Starting development environment...${NC}"
    ./docker-dev.sh
}

run_headless() {
    echo -e "${GREEN}Starting headless mode...${NC}"
    docker run -d \
        --gpus all \
        --name "${IMAGE_NAME}-headless" \
        -p 8554:8554 \
        -v "$(pwd)/../engines:/app/engines" \
        -v "$(pwd)/../logs:/app/logs" \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        python3 deepstream_api/main_headless.py

    echo -e "${GREEN}Container started: ${IMAGE_NAME}-headless${NC}"
    echo -e "View logs: ${YELLOW}docker logs -f ${IMAGE_NAME}-headless${NC}"
}

shell_into_container() {
    CONTAINER_NAME="${1:-${IMAGE_NAME}-app}"

    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${GREEN}Opening shell in ${CONTAINER_NAME}...${NC}"
        docker exec -it "${CONTAINER_NAME}" bash
    else
        echo -e "${RED}Container ${CONTAINER_NAME} is not running${NC}"
        echo -e "${YELLOW}Available containers:${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}"
        exit 1
    fi
}

view_logs() {
    CONTAINER_NAME="${1:-${IMAGE_NAME}-app}"

    echo -e "${GREEN}Viewing logs for ${CONTAINER_NAME}...${NC}"
    docker logs -f "${CONTAINER_NAME}"
}

stop_containers() {
    echo -e "${YELLOW}Stopping DeepStream containers...${NC}"
    docker ps --format '{{.Names}}' | grep -E "${IMAGE_NAME}" | xargs -r docker stop
    echo -e "${GREEN}Containers stopped${NC}"
}

clean_containers() {
    echo -e "${YELLOW}Removing stopped containers...${NC}"
    docker ps -a --format '{{.Names}}' | grep -E "${IMAGE_NAME}" | xargs -r docker rm
    echo -e "${GREEN}Containers removed${NC}"
}

prune_docker() {
    echo -e "${YELLOW}Cleaning Docker resources...${NC}"
    echo ""
    echo -e "${YELLOW}This will remove:${NC}"
    echo "  - Stopped containers"
    echo "  - Unused networks"
    echo "  - Dangling images"
    echo "  - Build cache"
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -f
        echo -e "${GREEN}Docker cleanup completed${NC}"
    else
        echo -e "${YELLOW}Cleanup cancelled${NC}"
    fi
}

inspect_container() {
    CONTAINER_NAME="${1:-${IMAGE_NAME}-app}"

    echo -e "${GREEN}Inspecting ${CONTAINER_NAME}...${NC}"
    echo ""

    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        docker inspect "${CONTAINER_NAME}" | less
    else
        echo -e "${RED}Container ${CONTAINER_NAME} not found${NC}"
        exit 1
    fi
}

test_gpu() {
    echo -e "${GREEN}Testing GPU access...${NC}"
    echo ""

    docker run --rm --gpus all "${IMAGE_NAME}:${IMAGE_TAG}" bash -c '
        echo "========================================="
        echo "GPU Information:"
        echo "========================================="
        nvidia-smi
        echo ""
        echo "========================================="
        echo "CUDA Test:"
        echo "========================================="
        python3 -c "import torch; print(f\"CUDA Available: {torch.cuda.is_available()}\"); print(f\"CUDA Devices: {torch.cuda.device_count()}\")"
        echo ""
        echo "========================================="
        echo "DeepStream Test:"
        echo "========================================="
        gst-inspect-1.0 nvstreammux | head -20
    '
}

build_engine() {
    echo -e "${GREEN}Building TensorRT engine in container...${NC}"

    docker run --rm --gpus all \
        -v "$(pwd)/../engines:/app/engines" \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        python3 engines/auto_build_engine.py "$@"
}

export_image() {
    OUTPUT_FILE="${1:-deepstream-yolo11-latest.tar}"

    echo -e "${GREEN}Exporting image to ${OUTPUT_FILE}...${NC}"
    docker save "${IMAGE_NAME}:${IMAGE_TAG}" | gzip > "${OUTPUT_FILE}"

    SIZE=$(du -h "${OUTPUT_FILE}" | cut -f1)
    echo -e "${GREEN}Image exported successfully${NC}"
    echo -e "File: ${YELLOW}${OUTPUT_FILE}${NC} (${SIZE})"
}

import_image() {
    INPUT_FILE="${1}"

    if [ -z "$INPUT_FILE" ]; then
        echo -e "${RED}Error: Please specify the tar file to import${NC}"
        echo "Usage: $0 import-image <file.tar>"
        exit 1
    fi

    if [ ! -f "$INPUT_FILE" ]; then
        echo -e "${RED}Error: File not found: ${INPUT_FILE}${NC}"
        exit 1
    fi

    echo -e "${GREEN}Importing image from ${INPUT_FILE}...${NC}"
    docker load < "${INPUT_FILE}"
    echo -e "${GREEN}Image imported successfully${NC}"
}

push_image() {
    REGISTRY="${1}"

    if [ -z "$REGISTRY" ]; then
        echo -e "${RED}Error: Please specify registry URL${NC}"
        echo "Usage: $0 push <registry-url>"
        echo "Example: $0 push ghcr.io/username"
        exit 1
    fi

    FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

    echo -e "${GREEN}Tagging image as ${FULL_IMAGE}...${NC}"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${FULL_IMAGE}"

    echo -e "${GREEN}Pushing to registry...${NC}"
    docker push "${FULL_IMAGE}"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully pushed to ${FULL_IMAGE}${NC}"
    else
        echo -e "${RED}Failed to push to registry${NC}"
        exit 1
    fi
}

show_stats() {
    echo -e "${GREEN}Container Resource Usage:${NC}"
    echo ""
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" \
        $(docker ps --format '{{.Names}}' | grep -E "${IMAGE_NAME}")
}

check_health() {
    CONTAINER_NAME="${1:-${IMAGE_NAME}-app}"

    echo -e "${GREEN}Checking health of ${CONTAINER_NAME}...${NC}"
    echo ""

    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "no healthcheck")

        echo -e "Health Status: ${YELLOW}${STATUS}${NC}"
        echo ""

        if [ "$STATUS" != "no healthcheck" ]; then
            echo "Recent Health Checks:"
            docker inspect --format='{{range .State.Health.Log}}{{.Start}} - {{.ExitCode}} - {{.Output}}{{end}}' "${CONTAINER_NAME}" | tail -5
        fi
    else
        echo -e "${RED}Container ${CONTAINER_NAME} is not running${NC}"
        exit 1
    fi
}

# ==============================================================================
# Main
# ==============================================================================

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse command
COMMAND="${1:-help}"
shift 2>/dev/null || true

case "$COMMAND" in
    build)
        build_image
        ;;
    run)
        run_container "$@"
        ;;
    dev)
        run_dev
        ;;
    headless)
        run_headless
        ;;
    shell)
        shell_into_container "$@"
        ;;
    logs)
        view_logs "$@"
        ;;
    stop)
        stop_containers
        ;;
    clean)
        clean_containers
        ;;
    prune)
        prune_docker
        ;;
    inspect)
        inspect_container "$@"
        ;;
    test-gpu)
        test_gpu
        ;;
    build-engine)
        build_engine "$@"
        ;;
    export-image)
        export_image "$@"
        ;;
    import-image)
        import_image "$@"
        ;;
    push)
        push_image "$@"
        ;;
    stats)
        show_stats
        ;;
    health)
        check_health "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: ${COMMAND}${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
