#!/bin/bash
# Entrypoint para Docker - Detecta e inicializa el sistema automáticamente

set -e

echo "=========================================================================="
echo "🚀 INICIANDO DEEPSTREAM AUTO-CONFIG"
echo "=========================================================================="
echo ""

# 1. Source DeepStream environment
echo "📦 Configurando variables de entorno..."
source /app/setup_deepstream_env.sh
echo ""

# 2. Verificar si existe engine
ENGINE_DIR="/app/engines/tensorrt"
ENGINE_FILE="$ENGINE_DIR/yolo11x_b1.engine"

if [ ! -f "$ENGINE_FILE" ]; then
    echo "⚠️  Engine TensorRT no encontrado en $ENGINE_FILE"
    echo ""
    echo "🔍 Detectando componentes del sistema..."
    echo ""

    # Ejecutar auto-builder desde nueva ubicación
    echo "🔨 Compilando TensorRT engine..."
    python3 /app/engines/auto_build_engine.py

    # Copiar engine generado
    GENERATED_ENGINE=$(ls -t /app/engines/yolo11x.engine 2>/dev/null | head -1)
    if [ -n "$GENERATED_ENGINE" ]; then
        echo ""
        echo "📋 Copiando engine generado..."
        mkdir -p "$ENGINE_DIR"
        cp "$GENERATED_ENGINE" "$ENGINE_FILE"
        echo "✅ Engine copiado a: $ENGINE_FILE"
    fi
    echo ""
fi

# 2.5. Corregir rutas de configuración (DeepStream 7.1 → 8.0)
echo "⚙️  Actualizando configuración de DeepStream..."
if [ -f "/app/configs/deepstream/tracker_config.txt" ]; then
    # Crear copia temporal con permisos de escritura
    cp /app/configs/deepstream/tracker_config.txt /tmp/tracker_config.txt

    # Corregir rutas de deepstream-7.1 a deepstream-8.0
    sed -i 's|/opt/nvidia/deepstream/deepstream/|/opt/nvidia/deepstream/deepstream-8.0/|g' /tmp/tracker_config.txt

    # Copiar back
    cp /tmp/tracker_config.txt /app/configs/deepstream/tracker_config.txt 2>/dev/null || true
    rm -f /tmp/tracker_config.txt

    echo "   ✅ Rutas de configuración actualizadas"
else
    echo "   ⚠️  tracker_config.txt no encontrado"
fi
echo ""

# 3. Verificar instalación
echo "=========================================================================="
echo "✅ VERIFICACIÓN DE SISTEMA"
echo "=========================================================================="
echo ""

# Verificar GPU
echo "🔷 GPU:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1 || echo "   ❌ GPU no disponible"

# Verificar CUDA
echo "🔶 CUDA:"
nvcc --version 2>/dev/null | grep release || echo "   ❌ CUDA no disponible"

# Verificar TensorRT
echo "🔶 TensorRT:"
python3 -c "import tensorrt as trt; print(f'   Versión: {trt.__version__}')" 2>/dev/null || echo "   ❌ TensorRT no disponible"

# Verificar DeepStream
echo "🟢 DeepStream:"
cat /opt/nvidia/deepstream/deepstream-8.0/version 2>/dev/null || echo "   ❌ DeepStream no detectado"

# Verificar PyDS
echo "🐍 PyDS:"
python3 -c "import pyds; print(f'   Version: {pyds.__version__}')" 2>/dev/null || echo "   ❌ PyDS no disponible"

# Verificar Engine
echo "📦 Engine TensorRT:"
if [ -f "$ENGINE_FILE" ]; then
    SIZE=$(du -h "$ENGINE_FILE" | cut -f1)
    echo "   ✅ $ENGINE_FILE ($SIZE)"
else
    echo "   ⚠️  No se encontró engine"
fi

echo ""
echo "=========================================================================="
echo "✅ SISTEMA LISTO"
echo "=========================================================================="
echo ""

# Ejecutar comando proporcionado o mostrar ayuda
if [ $# -eq 0 ]; then
    echo "📋 Comandos disponibles:"
    echo ""
    echo "  cd deepstream_api && python3 main_pyds.py  - Multi-camara con PyDS (RECOMENDADO)"
    echo "  python3 main_low_latency.py                - Iniciar con baja latencia"
    echo "  python3 main.py                            - Iniciar normal"
    echo "  python3 main_headless.py                   - Iniciar sin interfaz grafica"
    echo ""
    echo "  bash                                        - Abrir terminal"
    echo ""
    echo "Ejemplo de uso:"
    echo "  docker run -it deepstream-app bash -c 'cd deepstream_api && python3 main_pyds.py'"
    echo ""
    exec bash
else
    exec "$@"
fi
