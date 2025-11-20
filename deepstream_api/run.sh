#!/bin/bash
#
# Script de ejecución CON DISPLAY
# Ejecuta el sistema de conteo con ventanas de video
#

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

export DEEPSTREAM_DIR="$PROJECT_DIR/deepstream_extracted/opt/nvidia/deepstream/deepstream-7.1"
export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$DEEPSTREAM_DIR/lib/gst-plugins
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DEEPSTREAM_DIR/lib
export PYTHONPATH=$PYTHONPATH:$DEEPSTREAM_DIR/lib

echo "🚀 Ejecutando CON DISPLAY (ventanas de video) con entorno DeepStream 7.1..."
echo "   DEEPSTREAM_DIR: $DEEPSTREAM_DIR"

python3 main.py "$@"
