#!/bin/bash
# Script de configuración rápida

echo "=========================================="
echo "🚀 Configuración DeepStream 7.1 API System"
echo "=========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado"
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"

# Instalar dependencias
echo ""
echo "📦 Instalando dependencias Python..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencias instaladas"
else
    echo "❌ Error instalando dependencias"
    exit 1
fi

# Crear directorios si no existen
echo ""
echo "📁 Creando directorios..."
mkdir -p config logs
echo "✅ Directorios creados"

# Verificar DeepStream
echo ""
echo "🔍 Verificando DeepStream..."
if [ -d "/opt/nvidia/deepstream/deepstream-7.1" ]; then
    echo "✅ DeepStream 7.1 encontrado"
else
    echo "⚠️  DeepStream 7.1 no encontrado en /opt/nvidia/deepstream/deepstream-7.1"
    echo "   Asegúrate de tener DeepStream 7.1 instalado"
fi

# Verificar engines
echo ""
echo "🔍 Verificando engines TensorRT..."
if [ -f "../engines/tensorrt/yolo11x_b1.engine" ]; then
    echo "✅ Engine yolo11x_b1.engine encontrado"
else
    echo "⚠️  Engine yolo11x_b1.engine no encontrado"
    echo "   Ruta esperada: ../engines/tensorrt/yolo11x_b1.engine"
fi

# Verificar librerías personalizadas
echo ""
echo "🔍 Verificando librería personalizada YOLO..."
if [ -f "../libnvdsinfer_custom_impl_Yolo.so" ]; then
    echo "✅ libnvdsinfer_custom_impl_Yolo.so encontrado"
else
    echo "⚠️  libnvdsinfer_custom_impl_Yolo.so no encontrado"
    echo "   Ruta esperada: ../libnvdsinfer_custom_impl_Yolo.so"
fi

echo ""
echo "=========================================="
echo "✅ Configuración completada"
echo "=========================================="
echo ""
echo "Para ejecutar:"
echo "  python3 main.py"
echo ""
echo "Para más información:"
echo "  cat README.md"
echo ""
