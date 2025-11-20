#!/bin/bash
#
# Script de ejecución HEADLESS (sin display)
# Ejecuta el sistema de conteo sin ventanas de video
# Perfecto para servidores sin display
#

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

export DEEPSTREAM_DIR="$PROJECT_DIR/deepstream_extracted/opt/nvidia/deepstream/deepstream-7.1"
export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$DEEPSTREAM_DIR/lib/gst-plugins
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DEEPSTREAM_DIR/lib
export PYTHONPATH=$PYTHONPATH:$DEEPSTREAM_DIR/lib

echo "🚀 Ejecutando HEADLESS (sin display) con entorno DeepStream 7.1..."
echo "   DEEPSTREAM_DIR: $DEEPSTREAM_DIR"

python3 main_headless.py "$@"
