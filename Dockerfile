# Multi-stage Dockerfile optimizado para YOLO11x + DeepStream 8.0
# Genera engine TensorRT automáticamente en el contenedor

FROM nvcr.io/nvidia/deepstream:8.0-devel

# Información del contenedor
LABEL maintainer="DeepStream Team"
LABEL description="YOLO11x + DeepStream 8.0 con auto-generación de engine TensorRT"

# Configuración de entorno
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Instalar dependencias de Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar Ultralytics YOLO y dependencias
RUN pip3 install --no-cache-dir \
    ultralytics \
    opencv-python \
    numpy \
    requests \
    tensorrt \
    pyservicemaker

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de la aplicación
COPY . /app/

# Crear directorios necesarios
RUN mkdir -p /app/engines/tensorrt \
    && mkdir -p /app/engines/onnx \
    && mkdir -p /app/configs/deepstream \
    && mkdir -p /app/deepstream_api/config \
    && chmod +x /app/entrypoint.sh \
    && chmod +x /app/export_dynamic_batch/auto_build_engine.py

# Variables de entorno de DeepStream
ENV DEEPSTREAM_DIR=/opt/nvidia/deepstream/deepstream-8.0
ENV GST_PLUGIN_PATH=$GST_PLUGIN_PATH:${DEEPSTREAM_DIR}/lib/gst-plugins
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${DEEPSTREAM_DIR}/lib
ENV PYTHONPATH=$PYTHONPATH:${DEEPSTREAM_DIR}/lib

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["bash"]
