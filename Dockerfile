# ==============================================================================
# Multi-Stage Dockerfile for DeepStream 8.0 + YOLO11
# Optimized for production with separate build and runtime stages
# ==============================================================================

# ==============================================================================
# Stage 1: Base Image with DeepStream 8.0
# ==============================================================================
FROM nvcr.io/nvidia/deepstream:8.0-triton-multiarch AS deepstream-base

# Metadata
LABEL maintainer="DeepStream YOLO Team"
LABEL description="DeepStream 8.0 with YOLO11 support and TensorRT auto-build"
LABEL version="1.0"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    DEEPSTREAM_DIR=/opt/nvidia/deepstream/deepstream-8.0 \
    CUDA_VER=12.8 \
    TENSORRT_VER=10.7.0 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# ==============================================================================
# Stage 2: Build Stage - Install build dependencies and compile custom libs
# ==============================================================================
FROM deepstream-base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    build-essential \
    cmake \
    pkg-config \
    git \
    wget \
    curl \
    ca-certificates \
    # CUDA development tools
    cuda-toolkit-12-8 \
    # GStreamer development
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    # OpenCV and image processing
    libopencv-dev \
    # Additional development libraries
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    # Python development
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for builds
WORKDIR /workspace

# Clone DeepStream-Yolo repository
RUN git clone --depth 1 https://github.com/marcoslucianops/DeepStream-Yolo.git /workspace/DeepStream-Yolo

# Build custom YOLO library for DeepStream
WORKDIR /workspace/DeepStream-Yolo
RUN CUDA_VER=12.8 make -C nvdsinfer_custom_impl_Yolo

# Verify the compiled library
RUN ls -lh /workspace/DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so

# ==============================================================================
# Stage 3: Python Environment - Model conversion tools
# ==============================================================================
FROM builder AS python-builder

# Install Python packages for model conversion and optimization
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
    # YOLO and model conversion
    ultralytics>=8.0.0 \
    # ONNX tools
    onnx>=1.15.0 \
    onnxslim>=0.1.31 \
    onnxruntime-gpu>=1.16.0 \
    # Deep learning frameworks
    torch>=2.0.0 \
    torchvision>=0.15.0 \
    # TensorRT Python bindings (if available)
    # nvidia-tensorrt \
    # Utilities
    numpy>=1.24.0 \
    opencv-python-headless>=4.8.0 \
    pillow>=10.0.0 \
    pyyaml>=6.0 \
    requests>=2.31.0 \
    tqdm>=4.65.0 \
    psutil>=5.9.0

# Verify Python installations
RUN python3 -c "import ultralytics; print(f'Ultralytics: {ultralytics.__version__}')" && \
    python3 -c "import onnx; print(f'ONNX: {onnx.__version__}')" && \
    python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"

# ==============================================================================
# Stage 4: Runtime Stage - Final production image
# ==============================================================================
FROM deepstream-base AS runtime

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python runtime
    python3 \
    python3-pip \
    python3-gi \
    # GStreamer plugins
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-rtsp \
    # OpenCV runtime
    libopencv-core4.5d \
    libopencv-imgproc4.5d \
    libopencv-highgui4.5d \
    # Utilities
    wget \
    curl \
    git \
    vim \
    nano \
    htop \
    tmux \
    # Network tools for debugging
    net-tools \
    iputils-ping \
    # X11 and display support (for visualization)
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled libraries from builder stage
COPY --from=builder /workspace/DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/libnvdsinfer_custom_impl_Yolo.so \
    /opt/nvidia/deepstream/deepstream-8.0/lib/libnvdsinfer_custom_impl_Yolo.so

# Copy Python packages from python-builder stage
COPY --from=python-builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy DeepStream-Yolo utilities and labels
COPY --from=builder /workspace/DeepStream-Yolo/labels.txt /opt/nvidia/deepstream/deepstream-8.0/labels.txt
COPY --from=builder /workspace/DeepStream-Yolo/config_infer_primary_yolo*.txt /opt/nvidia/deepstream/deepstream-8.0/

# Set up application directory
WORKDIR /app

# Copy application files
COPY . /app/

# Ensure scripts are executable
RUN chmod +x /app/*.sh 2>/dev/null || true && \
    chmod +x /app/deepstream_api/*.sh 2>/dev/null || true && \
    chmod +x /app/deepstream_api/*.py 2>/dev/null || true && \
    chmod +x /app/engines/*.py 2>/dev/null || true

# Create necessary directories with proper permissions
RUN mkdir -p /app/engines/tensorrt \
             /app/engines/pt \
             /app/logs \
             /app/configs/deepstream \
             /app/output \
    && chmod -R 755 /app/engines \
    && chmod -R 755 /app/logs \
    && chmod -R 755 /app/output

# Configure DeepStream environment variables
ENV GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$DEEPSTREAM_DIR/lib/gst-plugins \
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DEEPSTREAM_DIR/lib:/usr/local/lib \
    PYTHONPATH=$PYTHONPATH:$DEEPSTREAM_DIR/lib \
    PATH=$PATH:$DEEPSTREAM_DIR/bin

# Add custom library path
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/app

# Set display for X11 (for local visualization)
ENV DISPLAY=:0

# Expose ports for RTSP streaming and monitoring
EXPOSE 8554 8555 9000

# Health check to verify DeepStream and GPU are available
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD nvidia-smi && python3 -c "import gi; gi.require_version('Gst', '1.0')" || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command: start bash for interactive use
CMD ["bash"]

# ==============================================================================
# Build Instructions:
# ==============================================================================
# docker build -t deepstream-yolo11:latest -f Dockerfile .
# docker run -it --gpus all --net=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix deepstream-yolo11:latest
# ==============================================================================
