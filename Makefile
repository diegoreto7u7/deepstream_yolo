# ==============================================================================
# Makefile for DeepStream 8.0 + YOLO11x Docker Project
# ==============================================================================

.PHONY: help build run dev stop clean prune test shell logs

# Default target
.DEFAULT_GOAL := help

# Configuration
IMAGE_NAME ?= deepstream-yolo11
IMAGE_TAG ?= latest
CONTAINER_NAME ?= deepstream-yolo11-app
GPU_DEVICES ?= all

# ==============================================================================
# Help
# ==============================================================================

help: ## Show this help message
	@echo "========================================================================"
	@echo "DeepStream 8.0 + YOLO11x Docker Makefile"
	@echo "========================================================================"
	@echo ""
	@echo "Available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Configuration:"
	@echo "  IMAGE_NAME      = $(IMAGE_NAME)"
	@echo "  IMAGE_TAG       = $(IMAGE_TAG)"
	@echo "  GPU_DEVICES     = $(GPU_DEVICES)"
	@echo ""
	@echo "Examples:"
	@echo "  make build"
	@echo "  make run"
	@echo "  make GPU_DEVICES=0 run"
	@echo "  make dev"
	@echo ""

# ==============================================================================
# Build Targets
# ==============================================================================

build: ## Build Docker image
	@echo "Building Docker image..."
	./scripts/docker-build.sh

build-nocache: ## Build Docker image without cache
	@echo "Building Docker image (no cache)..."
	docker build --no-cache -t $(IMAGE_NAME):$(IMAGE_TAG) -f Dockerfile.x86 .

build-compose: ## Build using docker-compose
	@echo "Building with docker-compose..."
	docker-compose build

# ==============================================================================
# Run Targets
# ==============================================================================

run: ## Run container interactively with GUI
	@echo "Running container..."
	./scripts/docker-run.sh

dev: ## Start development environment
	@echo "Starting development environment..."
	./scripts/docker-dev.sh

headless: ## Run in headless mode (background)
	@echo "Starting headless mode..."
	docker-compose --profile production up -d deepstream-headless

lowlatency: ## Run in low latency mode
	@echo "Starting low latency mode..."
	docker-compose --profile lowlatency up deepstream-lowlatency

# ==============================================================================
# Management Targets
# ==============================================================================

stop: ## Stop all running containers
	@echo "Stopping containers..."
	./scripts/docker-utils.sh stop

restart: stop run ## Restart container

clean: ## Remove stopped containers
	@echo "Cleaning stopped containers..."
	./scripts/docker-utils.sh clean

prune: ## Remove all unused Docker resources
	@echo "Pruning Docker resources..."
	./scripts/docker-utils.sh prune

# ==============================================================================
# Testing Targets
# ==============================================================================

test: ## Test GPU access
	@echo "Testing GPU access..."
	./scripts/docker-utils.sh test-gpu

test-build: ## Test if image builds successfully
	@echo "Testing build..."
	docker build -t $(IMAGE_NAME):test -f Dockerfile.x86 . && \
	docker run --rm $(IMAGE_NAME):test python3 -c "import ultralytics; print('OK')"

# ==============================================================================
# Utility Targets
# ==============================================================================

shell: ## Open shell in running container
	@echo "Opening shell..."
	./scripts/docker-utils.sh shell

logs: ## View container logs
	@echo "Viewing logs..."
	./scripts/docker-utils.sh logs

stats: ## Show container resource usage
	@echo "Resource usage..."
	./scripts/docker-utils.sh stats

health: ## Check container health
	@echo "Checking health..."
	./scripts/docker-utils.sh health

inspect: ## Inspect container configuration
	@echo "Inspecting container..."
	./scripts/docker-utils.sh inspect

# ==============================================================================
# Engine Targets
# ==============================================================================

build-engine: ## Build TensorRT engine in container
	@echo "Building TensorRT engine..."
	./scripts/docker-utils.sh build-engine

build-engine-fp32: ## Build TensorRT engine with FP32 precision
	@echo "Building TensorRT engine (FP32)..."
	./scripts/docker-utils.sh build-engine --no-fp16

# ==============================================================================
# Deployment Targets
# ==============================================================================

export: ## Export Docker image to tar file
	@echo "Exporting image..."
	./scripts/docker-utils.sh export-image $(IMAGE_NAME)-$(IMAGE_TAG).tar

import: ## Import Docker image from tar file (requires FILE=path/to/file.tar)
	@echo "Importing image..."
	./scripts/docker-utils.sh import-image $(FILE)

push: ## Push image to registry (requires REGISTRY=registry-url)
	@echo "Pushing to registry..."
	./scripts/docker-utils.sh push $(REGISTRY)

# ==============================================================================
# Docker Compose Targets
# ==============================================================================

compose-up: ## Start services with docker-compose
	docker-compose up

compose-up-d: ## Start services in background
	docker-compose up -d

compose-down: ## Stop and remove docker-compose services
	docker-compose down

compose-logs: ## View docker-compose logs
	docker-compose logs -f

compose-ps: ## List docker-compose services
	docker-compose ps

# ==============================================================================
# Development Targets
# ==============================================================================

format: ## Format Python code (if ruff/black installed)
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format deepstream_api/; \
	elif command -v black >/dev/null 2>&1; then \
		black deepstream_api/; \
	else \
		echo "Install ruff or black for code formatting"; \
	fi

lint: ## Lint Python code (if ruff/flake8 installed)
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check deepstream_api/; \
	elif command -v flake8 >/dev/null 2>&1; then \
		flake8 deepstream_api/; \
	else \
		echo "Install ruff or flake8 for linting"; \
	fi

# ==============================================================================
# Information Targets
# ==============================================================================

info: ## Show system information
	@echo "========================================================================"
	@echo "System Information"
	@echo "========================================================================"
	@echo ""
	@echo "Docker Version:"
	@docker --version
	@echo ""
	@echo "Docker Compose Version:"
	@docker-compose --version
	@echo ""
	@echo "NVIDIA Driver:"
	@nvidia-smi --query-gpu=driver_version --format=csv,noheader || echo "Not available"
	@echo ""
	@echo "GPUs:"
	@nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader || echo "Not available"
	@echo ""
	@echo "Docker Images:"
	@docker images $(IMAGE_NAME) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}" || true
	@echo ""
	@echo "Running Containers:"
	@docker ps --filter ancestor=$(IMAGE_NAME):$(IMAGE_TAG) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true
	@echo ""

images: ## List Docker images
	@docker images $(IMAGE_NAME)

containers: ## List all containers (running and stopped)
	@docker ps -a --filter ancestor=$(IMAGE_NAME):$(IMAGE_TAG)

volumes: ## List volumes
	@echo "Mounted volumes:"
	@ls -lh engines/ logs/ output/ 2>/dev/null || echo "Directories not created yet"

# ==============================================================================
# Cleanup Targets
# ==============================================================================

clean-all: clean ## Remove containers, images, and volumes
	@echo "Removing images..."
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) || true
	@echo "Removing volumes..."
	docker volume prune -f

reset: clean-all build ## Complete reset: clean everything and rebuild
	@echo "Reset complete"

# ==============================================================================
# CI/CD Targets
# ==============================================================================

ci-build: ## CI build (no cache, with tests)
	docker build --no-cache -t $(IMAGE_NAME):ci -f Dockerfile.x86 .
	docker run --rm $(IMAGE_NAME):ci python3 -c "import ultralytics; import onnx; print('CI tests passed')"

ci-test: ## Run CI tests
	@echo "Running CI tests..."
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) bash -c '\
		python3 -c "import ultralytics" && \
		python3 -c "import onnx" && \
		gst-inspect-1.0 nvstreammux && \
		ls /app/libnvdsinfer_custom_impl_Yolo.so \
	'

# ==============================================================================
# Documentation Targets
# ==============================================================================

docs: ## Open documentation
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open docs/DOCKER.md; \
	else \
		cat docs/DOCKER.md | less; \
	fi

quickstart: ## Show quick start guide
	@cat DOCKER_QUICKSTART.md

# ==============================================================================
# Notes
# ==============================================================================
# - Run 'make help' to see all available targets
# - Environment variables can be set: make GPU_DEVICES=0 run
# - For development: make dev
# - For production: make headless
# ==============================================================================
