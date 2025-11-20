#!/bin/bash
# Script inteligente para construir Docker - Elige Dockerfile correcto automáticamente

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🐳 CONSTRUCTOR INTELIGENTE DE DOCKER - DeepStream YOLO11x"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parámetros por defecto
IMAGE_NAME="deepstream-yolo11x"
TAG="latest"
DOCKERFILE=""
SYSTEM_TYPE=""

# Función para mostrar ayuda
show_help() {
    cat << EOF
Uso: ./build.sh [OPCIONES]

Opciones:
  -h, --help              Mostrar esta ayuda
  -n, --name NAME         Nombre de la imagen (default: deepstream-yolo11x)
  -t, --tag TAG           Tag de la imagen (default: latest)
  -d, --dockerfile FILE   Especificar Dockerfile (auto-detecta si no se especifica)
  -s, --system SYSTEM     Sistema: debian, rhel (auto-detecta si no se especifica)
  --no-cache              Compilar sin cache
  --push                  Subir a registro después de compilar

Ejemplos:
  ./build.sh                                    # Auto-detecta sistema
  ./build.sh --name myapp --tag v1.0           # Con nombre y tag personalizados
  ./build.sh --system rhel                      # Forzar RedHat
  ./build.sh --system debian --tag ubuntu       # Forzar Debian con tag específico
  ./build.sh --no-cache                         # Sin cache Docker
  ./build.sh --push                             # Subir después de compilar

EOF
    exit 0
}

# Detectar sistema operativo del HOST
detect_host_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
            echo "debian"
        elif [[ "$ID" == "rhel" || "$ID" == "centos" || "$ID" == "rocky" || "$ID" == "fedora" ]]; then
            echo "rhel"
        else
            echo "debian"  # Default
        fi
    else
        echo "debian"  # Default
    fi
}

# Procesar argumentos
DOCKER_BUILD_ARGS=""
PUSH_IMAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -d|--dockerfile)
            DOCKERFILE="$2"
            shift 2
            ;;
        -s|--system)
            SYSTEM_TYPE="$2"
            shift 2
            ;;
        --no-cache)
            DOCKER_BUILD_ARGS="$DOCKER_BUILD_ARGS --no-cache"
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        *)
            echo "Opción desconocida: $1"
            show_help
            ;;
    esac
done

# Auto-detectar sistema si no se especificó
if [ -z "$SYSTEM_TYPE" ]; then
    SYSTEM_TYPE=$(detect_host_os)
fi

echo -e "${BLUE}📋 Detectando Configuración...${NC}"
echo ""

# Validar sistema
case $SYSTEM_TYPE in
    debian)
        echo -e "${GREEN}✅ Sistema: Debian/Ubuntu${NC}"
        if [ -z "$DOCKERFILE" ]; then
            DOCKERFILE="Dockerfile"
        fi
        ;;
    rhel)
        echo -e "${RED}✅ Sistema: RedHat/CentOS/Rocky${NC}"
        if [ -z "$DOCKERFILE" ]; then
            DOCKERFILE="Dockerfile.rhel"
        fi
        ;;
    *)
        echo -e "${YELLOW}⚠️  Sistema desconocido: $SYSTEM_TYPE${NC}"
        echo "    Usando Dockerfile.rhel (compatible con ambos)"
        DOCKERFILE="Dockerfile.rhel"
        ;;
esac

# Validar que el Dockerfile existe
if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}❌ ERROR: Dockerfile no encontrado: $DOCKERFILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Dockerfile: $DOCKERFILE${NC}"
echo ""

# Información de construcción
echo -e "${BLUE}🔨 Información de Construcción:${NC}"
echo "  Imagen: $IMAGE_NAME:$TAG"
echo "  Dockerfile: $DOCKERFILE"
echo "  Sistema: $SYSTEM_TYPE"
echo ""

# Mostrar tamaño del Dockerfile
DOCKERFILE_SIZE=$(du -h "$DOCKERFILE" | cut -f1)
echo -e "  Tamaño del Dockerfile: $DOCKERFILE_SIZE"
echo ""

# Verificar requisitos previos
echo -e "${BLUE}🔍 Verificando Requisitos Previos...${NC}"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker instalado${NC}"

# Verificar NVIDIA Docker para GPU
if [ "$SYSTEM_TYPE" == "rhel" ]; then
    if ! command -v nvidia-docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  nvidia-docker no encontrado (se usará docker --gpus all)${NC}"
    else
        echo -e "${GREEN}✅ nvidia-docker disponible${NC}"
    fi
fi

echo ""

# Construir imagen
echo -e "${BLUE}🚀 Iniciando Construcción...${NC}"
echo ""

BUILD_CMD="docker build $DOCKER_BUILD_ARGS -f $DOCKERFILE -t $IMAGE_NAME:$TAG ."

echo -e "${BLUE}Ejecutando:${NC}"
echo "  $BUILD_CMD"
echo ""

# Ejecutar build
if eval "$BUILD_CMD"; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ ¡IMAGEN CONSTRUIDA EXITOSAMENTE!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Mostrar tamaño de la imagen
    IMAGE_SIZE=$(docker images --no-trunc --quiet $IMAGE_NAME:$TAG | xargs docker inspect --format='{{.Size}}' | numfmt --to=iec 2>/dev/null || echo "desconocido")
    echo "📦 Información de la Imagen:"
    echo "   Nombre: $IMAGE_NAME:$TAG"
    echo "   Tamaño: $IMAGE_SIZE"
    echo ""

    # Mostrar comando para ejecutar
    echo "🚀 Para ejecutar:"
    echo ""
    if [ "$SYSTEM_TYPE" == "rhel" ]; then
        echo "  docker run -it --gpus all \\"
        echo "      -e NVIDIA_VISIBLE_DEVICES=all \\"
        echo "      $IMAGE_NAME:$TAG"
    else
        echo "  docker run -it --gpus all $IMAGE_NAME:$TAG"
    fi
    echo ""

    # Push si se solicitó
    if [ "$PUSH_IMAGE" = true ]; then
        echo -e "${BLUE}📤 Subiendo imagen al registro...${NC}"
        if docker push $IMAGE_NAME:$TAG; then
            echo -e "${GREEN}✅ Imagen subida exitosamente${NC}"
        else
            echo -e "${RED}❌ Error al subir imagen${NC}"
            exit 1
        fi
    fi

    echo ""
    echo -e "${GREEN}¡Listo para usar!${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}❌ ERROR: Fallo la construcción${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
fi
