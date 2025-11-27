#!/bin/bash
# ==============================================================================
# Entrypoint para DeepStream + PeopleNet
# Sistema de Control de Aforo
# ==============================================================================

set -e

echo "======================================================================"
echo "  SISTEMA DE CONTROL DE AFORO"
echo "  DeepStream 8.0 + PeopleNet"
echo "======================================================================"
echo ""

# Verificar GPU
echo "[1/4] Verificando GPU..."
if nvidia-smi &>/dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader | head -1)
    echo "  GPU: $GPU_NAME ($GPU_MEM)"
else
    echo "  ERROR: No se detecta GPU NVIDIA"
    exit 1
fi

# Verificar PyDS
echo "[2/4] Verificando PyDS..."
if python3 -c "import pyds; print(f'  Version: {pyds.__version__}')" 2>/dev/null; then
    echo "  OK"
else
    echo "  ERROR: PyDS no disponible"
    exit 1
fi

# Verificar modelo PeopleNet
echo "[3/4] Verificando modelo PeopleNet..."
MODEL_PATH="/app/models/peoplenet/resnet34_peoplenet.onnx"
if [ -f "$MODEL_PATH" ]; then
    MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
    echo "  Modelo: $MODEL_PATH ($MODEL_SIZE)"
else
    echo "  ERROR: Modelo no encontrado en $MODEL_PATH"
    echo "  Descarga manualmente desde NGC: nvidia/tao/peoplenet:deployable_quantized_onnx_v2.6.3"
    exit 1
fi

# Verificar GStreamer
echo "[4/4] Verificando DeepStream..."
if gst-inspect-1.0 nvstreammux &>/dev/null; then
    DS_VERSION=$(cat /opt/nvidia/deepstream/deepstream-8.0/version 2>/dev/null | head -1)
    echo "  DeepStream: $DS_VERSION"
else
    echo "  ERROR: DeepStream no disponible"
    exit 1
fi

echo ""
echo "======================================================================"
echo "  SISTEMA LISTO"
echo "======================================================================"
echo ""

# Ejecutar comando
if [ $# -eq 0 ]; then
    echo "Uso:"
    echo "  python3 /app/deepstream_api/main_peoplenet.py"
    echo ""
    exec bash
else
    exec "$@"
fi
