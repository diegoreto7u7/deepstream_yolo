#!/bin/bash
# Script para configurar variables de entorno de DeepStream 8.0

# Directorio de DeepStream 8.0
export DEEPSTREAM_DIR=/opt/nvidia/deepstream/deepstream-8.0

# Agregar plugins de GStreamer de DeepStream
export GST_PLUGIN_PATH=$GST_PLUGIN_PATH:$DEEPSTREAM_DIR/lib/gst-plugins

# Agregar librerías de DeepStream
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DEEPSTREAM_DIR/lib

# Python bindings
export PYTHONPATH=$PYTHONPATH:$DEEPSTREAM_DIR/lib

echo "✅ Variables de entorno de DeepStream 8.0 configuradas"
echo "GST_PLUGIN_PATH=$GST_PLUGIN_PATH"
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"
