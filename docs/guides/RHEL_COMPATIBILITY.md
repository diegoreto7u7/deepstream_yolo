# 🔴 Compatibilidad RedHat/CentOS - DeepStream YOLO11x

## 🎯 Pregunta: ¿Funciona el Docker en RedHat?

**Respuesta Corta:**
- ❌ `Dockerfile` original: **NO** (usa `apt-get`)
- ✅ `Dockerfile.rhel`: **SÍ** (auto-detecta sistema)

---

## 📊 Comparación de Sistemas

| Aspecto | Debian/Ubuntu | RedHat/CentOS | Rocky Linux | Fedora |
|---------|---------------|---------------|-------------|--------|
| **Gestor paquetes** | `apt-get` / `apt` | `yum` / `dnf` | `dnf` | `dnf` |
| **Sistema base** | Debian | RedHat Enterprise | RedHat Enterprise | RedHat |
| **Docker disponible** | ✅ | ✅ | ✅ | ✅ |
| **NVIDIA drivers** | ✅ | ✅ | ✅ | ✅ |
| **CUDA support** | ✅ | ✅ | ✅ | ✅ |
| **DeepStream 8.0** | ✅ | ⚠️ | ⚠️ | ⚠️ |

---

## 🔴 Problema: Dockerfile Original

```dockerfile
RUN apt-get update && apt-get install -y ...
    └─ ❌ FALLA en RedHat (apt-get no existe)
```

### Error que obtendrías:

```
Step 5/20 : RUN apt-get update && apt-get install -y ...
 ---> Running in abc123def456
/bin/sh: apt-get: command not found
The command '/bin/sh -c apt-get update && apt-get install -y ...' returned a non-zero code: 127
```

---

## ✅ Solución: Dockerfile.rhel

**Archivo nuevo:** `Dockerfile.rhel`

### Características:

```dockerfile
# Auto-detecta el sistema operativo
RUN if [ -f /etc/os-release ]; then \
    . /etc/os-release; \
    if [ "$ID" = "debian" ] || [ "$ID" = "ubuntu" ]; then \
        apt-get update && apt-get install ...; \
    elif [ "$ID" = "rhel" ] || [ "$ID" = "centos" ] || [ "$ID" = "rocky" ]; then \
        yum install ...; \
    fi; \
fi
```

✅ **Auto-detecta y usa el gestor correcto**
✅ **Funciona en Debian, Ubuntu, RedHat, CentOS, Rocky**
✅ **Health check incluido**
✅ **Información de sistema al construir**

---

## 🚀 Cómo Usar en Cada Sistema

### En Ubuntu/Debian

```bash
# Opción 1: Dockerfile original
docker build -t deepstream-yolo11x .

# Opción 2: Dockerfile RHEL-compatible (también funciona)
docker build -f Dockerfile.rhel -t deepstream-yolo11x-compat .

# Ejecutar
docker run -it --gpus all deepstream-yolo11x
```

### En RedHat/CentOS/Rocky

```bash
# MUST usar Dockerfile.rhel
docker build -f Dockerfile.rhel -t deepstream-yolo11x-rhel .

# Ejecutar
docker run -it --gpus all deepstream-yolo11x-rhel
```

---

## 🔧 Diferencias en la Instalación

### Debian/Ubuntu
```bash
apt-get update
apt-get install -y python3-pip python3-dev git curl
```

### RedHat/CentOS/Rocky
```bash
yum install -y python3-pip python3-devel git curl
yum clean all
```

**Diferencias clave:**
- `apt-get` vs `yum`/`dnf`
- `python3-dev` vs `python3-devel`
- `apt-get ... && rm -rf /var/lib/apt/lists/*` vs `yum ... && yum clean all`

---

## ⚠️ Consideraciones Importantes

### 1. Versión de DeepStream

DeepStream 8.0 official images pueden estar optimizadas para:
- ✅ Ubuntu 20.04 LTS
- ✅ Ubuntu 22.04 LTS
- ⚠️ RedHat/CentOS (puede requerir GLIBC compatible)

**Verificar antes:**
```bash
docker run --rm nvcr.io/nvidia/deepstream:8.0-devel \
    cat /etc/os-release
```

### 2. GLIBC Compatibility

RedHat puede usar versiones diferentes de GLIBC:
```bash
# En el contenedor
ldd --version
# Debe ser >= 2.29 para TensorRT 8.x
```

### 3. GStreamer

RedHat puede tener versiones diferentes:
```bash
# Verificar
gst-inspect-1.0 --version
```

---

## 📋 Checklist para RedHat

- [ ] Docker instalado (versión 19.03+)
- [ ] NVIDIA Container Toolkit configurado
- [ ] nvidia-docker funcional
- [ ] GPU visible: `docker run --rm --gpus all nvidia/cuda:12.2-runtime nvidia-smi`
- [ ] Usar `Dockerfile.rhel` (no el original)
- [ ] Build: `docker build -f Dockerfile.rhel -t deepstream-yolo11x-rhel .`
- [ ] Run: `docker run -it --gpus all deepstream-yolo11x-rhel`

---

## 🔍 Verificar Compatibilidad

```bash
# 1. Verificar sistema dentro del contenedor
docker run -it --rm nvcr.io/nvidia/deepstream:8.0-devel \
    cat /etc/os-release

# 2. Verificar GLIBC
docker run -it --rm nvcr.io/nvidia/deepstream:8.0-devel \
    ldd --version

# 3. Verificar GStreamer
docker run -it --rm nvcr.io/nvidia/deepstream:8.0-devel \
    gst-inspect-1.0 --version

# 4. Verificar TensorRT
docker run -it --rm --gpus all nvcr.io/nvidia/deepstream:8.0-devel \
    python3 -c "import tensorrt; print(f'TensorRT: {tensorrt.__version__}')"
```

---

## 🛠️ Si hay problemas en RedHat

### Error: "GLIBC_2.X.X not found"

**Causa:** Versión de GLIBC incompatible
**Solución:**
```bash
# Actualizar GLIBC en el contenedor (en Dockerfile.rhel)
RUN yum install -y glibc
```

### Error: "libcrypto.so.1.1 not found"

**Causa:** OpenSSL incompatible
**Solución:**
```bash
# En Dockerfile.rhel agregar:
RUN yum install -y openssl-libs
```

### Error: "Can't locate GStreamer plugin"

**Causa:** GStreamer plugins no encontrados
**Solución:**
```bash
# En Dockerfile.rhel agregar:
RUN yum install -y gstreamer1-plugins-good gstreamer1-plugins-bad
```

---

## 📊 Rendimiento en RedHat vs Debian

**No hay diferencia de rendimiento** si:
- ✅ NVIDIA Drivers correctamente instalados
- ✅ CUDA funcionando
- ✅ TensorRT disponible
- ✅ GPU visible en el contenedor

Diferencias esperadas:
- Compilación puede ser 5-10% más lenta en RedHat
- Inferencia: **Idéntica** (mismo engine TensorRT)

---

## 🚀 Recomendación Final

### Para Máquina Ubuntu/Debian
```bash
docker build -t deepstream-yolo11x .
docker run -it --gpus all deepstream-yolo11x
```

### Para Máquina RedHat/CentOS/Rocky
```bash
docker build -f Dockerfile.rhel -t deepstream-yolo11x-rhel .
docker run -it --gpus all deepstream-yolo11x-rhel
```

### Para Máquinas Mixtas (ambos tipos)
```bash
docker build -f Dockerfile.rhel -t deepstream-yolo11x-universal .
# Funciona en cualquier sistema Linux con Docker
```

---

## 📝 Resumen

| Pregunta | Respuesta |
|----------|-----------|
| ¿Funciona el Dockerfile original en RedHat? | ❌ NO |
| ¿Funciona Dockerfile.rhel en RedHat? | ✅ SÍ |
| ¿Funciona Dockerfile.rhel en Ubuntu? | ✅ SÍ |
| ¿Qué debo usar en RedHat? | `docker build -f Dockerfile.rhel` |
| ¿Hay diferencia de rendimiento? | ❌ NO (mismo engine TensorRT) |
| ¿Es más fácil usar Dockerfile.rhel? | ✅ SÍ (auto-detecta) |

---

**Última actualización:** Noviembre 2025
**DeepStream:** 8.0.0
**Sistemas Soportados:** Debian, Ubuntu, RedHat, CentOS, Rocky, Fedora
