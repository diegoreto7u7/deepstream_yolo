# DeepStream en RedHat/Rocky Linux - Guía de Despliegue

Esta guía cubre los aspectos específicos de desplegar DeepStream + YOLO11x en sistemas **RedHat Enterprise Linux (RHEL)**, **Rocky Linux**, **CentOS**, y **AlmaLinux**.

## 🔴 Problema Crítico: SELinux y Display X11

### El Problema

En sistemas RedHat/Rocky/CentOS con **SELinux activado**, el container Docker **NO puede acceder al socket X11** (`/tmp/.X11-unix`) para mostrar ventanas gráficas.

**Error típico**:
```
cannot open display: :0
Gtk-WARNING **: cannot open display: :0
```

### La Solución

Añadir la opción de seguridad SELinux al comando `docker run`:

```bash
--security-opt label=type:container_runtime_t
```

Esta opción le dice a SELinux que permita al container acceder al socket X11 del sistema.

---

## ✅ Configuración Probada en Producción

Este es el comando exacto que funciona en sistemas RedHat con SELinux:

```bash
docker run -d -it \
  --name deepstream-yolo \
  --gpus all \
  --net=host \
  -e DISPLAY=:0 \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e GST_DEBUG=2 \
  -e API_URL=http://172.80.20.22/api \
  -e TZ=Europe/Madrid \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /home/usuario/deepstream_project/app:/app \
  --security-opt label=type:container_runtime_t \
  --workdir /app/deepstream_api \
  deepstream-yolo11:latest \
  bash
```

### Desglose del Comando

| Opción | Propósito |
|--------|-----------|
| `-d -it` | Ejecutar en background (daemon) pero con terminal interactiva |
| `--name deepstream-yolo` | Nombre del container |
| `--gpus all` | Acceso a todas las GPUs NVIDIA |
| `--net=host` | Usar la red del host (recomendado para DeepStream) |
| `-e DISPLAY=:0` | Variable de entorno para X11 display |
| `-e NVIDIA_VISIBLE_DEVICES=all` | Hacer visibles todas las GPUs al container |
| `-e NVIDIA_DRIVER_CAPABILITIES=all` | Habilitar todas las capacidades NVIDIA |
| `-e GST_DEBUG=2` | Nivel de debug de GStreamer (1-5) |
| `-e API_URL=...` | URL de tu API backend |
| `-e TZ=Europe/Madrid` | Zona horaria |
| `-v /tmp/.X11-unix:...` | Mount del socket X11 para GUI |
| `-v /home/.../app:/app` | Mount del código de la aplicación |
| `--security-opt label=type:container_runtime_t` | **CRÍTICO para SELinux** |
| `--workdir /app/deepstream_api` | Directorio de trabajo inicial |
| `bash` | Comando a ejecutar (shell interactivo) |

---

## 🚀 Uso con Scripts Automáticos

Nuestros scripts **detectan automáticamente** RedHat/Rocky y aplican la configuración de SELinux:

### Método 1: Script docker-run.sh (Recomendado)

```bash
# El script detecta SELinux automáticamente
API_URL=http://172.80.20.22/api ./scripts/docker-run.sh

# Con variables de entorno personalizadas
API_URL=http://172.80.20.22/api \
TZ=Europe/Madrid \
GST_DEBUG=2 \
./scripts/docker-run.sh
```

**El script automáticamente**:
- ✅ Detecta si estás en RedHat/Rocky/CentOS
- ✅ Verifica si SELinux está activo (`getenforce`)
- ✅ Añade `--security-opt label=type:container_runtime_t` si es necesario
- ✅ Configura DISPLAY=:0
- ✅ Monta /tmp/.X11-unix
- ✅ Aplica todas las variables de entorno

### Método 2: Docker Compose

Edita `docker-compose.yml` y descomenta la línea de SELinux:

```yaml
# En docker-compose.yml, busca esta sección:
security_opt:
  - seccomp:unconfined
  - label:type:container_runtime_t  # <-- Descomenta esta línea
```

Luego ejecuta:

```bash
API_URL=http://172.80.20.22/api docker-compose up -d
```

### Método 3: Variables de Entorno (.env)

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Edita `.env`:

```bash
# API Configuration
API_URL=http://172.80.20.22/api

# Timezone
TZ=Europe/Madrid

# GStreamer Debug Level
GST_DEBUG=2

# Display
DISPLAY=:0

# GPU
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=all
```

Ejecuta:

```bash
# Con docker-compose (lee .env automáticamente)
docker-compose up -d

# Con script
./scripts/docker-run.sh
```

---

## 🔧 Instalación en RedHat/Rocky (Sistema Nuevo)

### Paso 1: Instalar Prerequisites

Usa nuestro script automático:

```bash
sudo ./scripts/install-nvidia-prerequisites.sh
```

Este script:
1. Detecta que estás en RedHat/Rocky/CentOS
2. Instala repositorios EPEL
3. Instala drivers NVIDIA desde repositorio CUDA
4. Instala nvidia-container-toolkit
5. Configura Docker para usar NVIDIA runtime

### Paso 2: Reiniciar

```bash
sudo reboot
```

### Paso 3: Verificar Instalación

```bash
# Verificar driver NVIDIA
nvidia-smi

# Verificar Docker + GPU
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Verificar SELinux
getenforce
# Debe mostrar: Enforcing
```

### Paso 4: Construir Imagen

```bash
cd /home/usuario/deepstream_project/app
./scripts/docker-build.sh
```

### Paso 5: Ejecutar

```bash
# Interactivo
API_URL=http://172.80.20.22/api ./scripts/docker-run.sh

# O en background
docker run -d -it \
  --name deepstream-yolo \
  --gpus all \
  --net=host \
  -e DISPLAY=:0 \
  -e API_URL=http://172.80.20.22/api \
  -e TZ=Europe/Madrid \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd):/app \
  --security-opt label=type:container_runtime_t \
  deepstream-yolo11:latest \
  bash
```

---

## 🐛 Troubleshooting RedHat/Rocky

### Problema 1: "cannot open display :0"

**Causa**: SELinux bloqueando acceso a X11

**Solución**:
```bash
# Añadir opción SELinux
--security-opt label=type:container_runtime_t
```

**O temporalmente deshabilitar SELinux** (solo para testing):
```bash
sudo setenforce 0
```

Para volver a habilitar:
```bash
sudo setenforce 1
```

### Problema 2: "Error response from daemon: could not select device driver"

**Causa**: nvidia-container-toolkit no instalado

**Solución**:
```bash
# Instalar nvidia-container-toolkit
sudo dnf install -y nvidia-container-toolkit

# Configurar Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Problema 3: "nvidia-smi: command not found"

**Causa**: Drivers NVIDIA no instalados

**Solución**:
```bash
# Usar script automático
sudo ./scripts/install-nvidia-prerequisites.sh

# O manual
sudo dnf config-manager --add-repo \
  https://developer.download.nvidia.com/compute/cuda/repos/rhel8/x86_64/cuda-rhel8.repo
sudo dnf clean all
sudo dnf -y module install nvidia-driver:latest-dkms
sudo reboot
```

### Problema 4: Container arranca pero no muestra GUI

**Verificar DISPLAY**:
```bash
# En el host
echo $DISPLAY
# Debe ser :0 o :1

# Ejecutar container con DISPLAY correcto
docker run ... -e DISPLAY=${DISPLAY} ...
```

**Verificar X11 forwarding**:
```bash
# En el host, permitir acceso local
xhost +local:docker

# O permitir todo (menos seguro)
xhost +
```

### Problema 5: "Permission denied" en /tmp/.X11-unix

**Causa**: SELinux bloqueando mount

**Solución**:
```bash
# Añadir opción SELinux
--security-opt label=type:container_runtime_t

# Y mount con :rw
-v /tmp/.X11-unix:/tmp/.X11-unix:rw
```

### Problema 6: Firewall bloqueando conexiones

Si usas API externa:

```bash
# Verificar firewall
sudo firewall-cmd --list-all

# Permitir tráfico (si es necesario)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 📊 Comparación: RedHat vs Ubuntu

| Aspecto | Ubuntu/Debian | RedHat/Rocky/CentOS |
|---------|---------------|---------------------|
| **Package Manager** | `apt` | `dnf` / `yum` |
| **SELinux** | Disabled (AppArmor) | **Enabled** |
| **X11 en Docker** | Funciona directo | **Necesita `--security-opt`** |
| **NVIDIA Repo** | PPA | CUDA repo |
| **Driver Install** | `ubuntu-drivers` | `dnf module install` |
| **nvidia-docker** | Mismo paquete | Mismo paquete |
| **Container OS** | Ubuntu 24.04 | Ubuntu 24.04 (igual) |

**Punto clave**: El container SIEMPRE es Ubuntu 24.04, solo cambia la configuración del host.

---

## ✅ Checklist de Despliegue RedHat

Antes de desplegar en producción en RedHat:

- [ ] NVIDIA drivers instalados (`nvidia-smi` funciona)
- [ ] Docker instalado (`docker --version`)
- [ ] nvidia-container-toolkit instalado
- [ ] SELinux configurado correctamente
- [ ] `getenforce` muestra "Enforcing" (si quieres SELinux activo)
- [ ] Imagen Docker construida (`docker images | grep deepstream`)
- [ ] Variables de entorno configuradas (API_URL, TZ, etc.)
- [ ] Mounts de volúmenes preparados
- [ ] Firewall configurado (si usas red externa)
- [ ] X11 forwarding habilitado (`xhost +local:docker`)
- [ ] Probado en background (`docker run -d -it ...`)

---

## 🔐 Seguridad en Producción

### Opción 1: SELinux Activo (Recomendado)

```bash
# Mantener SELinux en modo Enforcing
sudo setenforce 1

# Usar security-opt correcto
docker run ... \
  --security-opt label=type:container_runtime_t \
  ...
```

### Opción 2: SELinux Permisivo (Menos Seguro)

```bash
# Solo para development/testing
sudo setenforce 0

# En producción, editar /etc/selinux/config
SELINUX=permissive
```

### Opción 3: Política SELinux Custom (Avanzado)

Crear política SELinux específica para el container:

```bash
# Requiere conocimientos de SELinux
# Ver: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/using_selinux/writing-a-custom-selinux-policy_using-selinux
```

---

## 📝 Ejemplo Completo: Despliegue Producción

```bash
#!/bin/bash
# deploy_redhat.sh - Script de despliegue para RedHat/Rocky

set -e

# Configuración
API_URL="http://172.80.20.22/api"
TIMEZONE="Europe/Madrid"
PROJECT_DIR="/home/usuario/deepstream_project/app"
IMAGE_NAME="deepstream-yolo11:latest"
CONTAINER_NAME="deepstream-yolo-prod"

# Verificar prerequisitos
echo "Verificando prerequisitos..."
nvidia-smi > /dev/null || { echo "Error: NVIDIA drivers no encontrados"; exit 1; }
docker --version > /dev/null || { echo "Error: Docker no instalado"; exit 1; }

# Habilitar X11 forwarding
echo "Habilitando X11 forwarding..."
xhost +local:docker

# Detener container anterior si existe
if docker ps -a | grep -q ${CONTAINER_NAME}; then
    echo "Deteniendo container anterior..."
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
fi

# Ejecutar container
echo "Iniciando DeepStream container..."
docker run -d -it \
  --name ${CONTAINER_NAME} \
  --gpus all \
  --net=host \
  --restart unless-stopped \
  -e DISPLAY=:0 \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  -e GST_DEBUG=2 \
  -e API_URL=${API_URL} \
  -e TZ=${TIMEZONE} \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v ${PROJECT_DIR}:/app \
  --security-opt label=type:container_runtime_t \
  --workdir /app/deepstream_api \
  ${IMAGE_NAME} \
  bash

# Verificar container
echo "Verificando container..."
sleep 5
docker ps | grep ${CONTAINER_NAME} || { echo "Error: Container no está corriendo"; exit 1; }

echo "✅ DeepStream desplegado correctamente en ${CONTAINER_NAME}"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:     docker logs -f ${CONTAINER_NAME}"
echo "  Acceder:      docker exec -it ${CONTAINER_NAME} bash"
echo "  Detener:      docker stop ${CONTAINER_NAME}"
echo "  Reiniciar:    docker restart ${CONTAINER_NAME}"
```

Dar permisos y ejecutar:

```bash
chmod +x deploy_redhat.sh
./deploy_redhat.sh
```

---

## 📚 Referencias

- **SELinux Docker**: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html/building_running_and_managing_containers/assembly_starting-with-containers_building-running-and-managing-containers
- **NVIDIA Container Toolkit**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
- **DeepStream on Docker**: https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_docker_containers.html

---

## 🎯 Resumen

### Para RedHat/Rocky/CentOS necesitas:

1. **En el host**:
   - ✅ NVIDIA drivers
   - ✅ Docker
   - ✅ nvidia-container-toolkit
   - ✅ SELinux configurado

2. **En docker run**:
   - ✅ `--security-opt label=type:container_runtime_t` (CRÍTICO)
   - ✅ `-v /tmp/.X11-unix:/tmp/.X11-unix:rw`
   - ✅ `-e DISPLAY=:0`
   - ✅ `--net=host`

3. **Nuestros scripts automáticos**:
   - ✅ Detectan RedHat automáticamente
   - ✅ Aplican configuración SELinux
   - ✅ Configuran todas las variables

**Comando más simple**:
```bash
API_URL=http://172.80.20.22/api ./scripts/docker-run.sh
```

El script hace todo lo demás automáticamente! 🎉
