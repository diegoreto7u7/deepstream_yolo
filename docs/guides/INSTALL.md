# 📥 Guía de Instalación - DeepStream + YOLO11x Auto-Build

## ⚙️ Requisitos Previos

### Hardware
```
✅ GPU NVIDIA moderna (RTX 30/40 series, A100, L40S, etc)
✅ Mínimo 6 GB VRAM GPU
✅ Mínimo 8 GB RAM sistema
✅ Mínimo 50 GB espacio disco (para Docker y models)
```

### Software
```
✅ Docker CE 19.03+
✅ NVIDIA Container Toolkit
✅ nvidia-docker (para soporte GPU)
✅ Linux kernel 5.4+ (preferiblemente 6.x)
```

## 🐧 Instalación en Linux (Ubuntu 20.04 / 22.04)

### 1. Instalar NVIDIA Drivers

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar drivers NVIDIA
sudo apt install -y nvidia-driver-550

# Verificar
nvidia-smi
```

**Versión recomendada:** 550+ (soporta CUDA 12.x)

### 2. Instalar CUDA Toolkit

```bash
# Descargar CUDA 12.2
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-repo-ubuntu2204_12.2.0-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204_12.2.0-1_amd64.deb
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub
sudo apt update
sudo apt install -y cuda-toolkit-12-2

# Agregar a PATH
echo 'export PATH=$PATH:/usr/local/cuda-12.2/bin' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda-12.2/lib64' >> ~/.bashrc
source ~/.bashrc

# Verificar
nvcc --version
```

### 3. Instalar Docker

```bash
# Desinstalar versiones antiguas
sudo apt remove -y docker docker-engine docker.io containerd runc

# Instalar Docker CE
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
```

### 4. Instalar NVIDIA Container Toolkit

```bash
# Repositorio
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Instalar
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verificar
docker run --rm --gpus all nvidia/cuda:12.2.0-runtime-ubuntu22.04 nvidia-smi
```

### 5. Descargar el Proyecto

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/deepstream-yolo11x.git
cd deepstream-yolo11x

# O descargar ZIP
wget https://github.com/tu-usuario/deepstream-yolo11x/archive/main.zip
unzip main.zip
cd deepstream-yolo11x-main
```

## 🐳 Uso con Docker (Recomendado)

### Build de la Imagen

```bash
# Construir imagen (una sola vez)
docker build -t deepstream-yolo11x .

# Esto descargará:
# - DeepStream 8.0 (700 MB)
# - CUDA 12.x
# - TensorRT
# - Ultralytics YOLO
# - Dependencias Python
# Tiempo: 10-15 minutos

# Tamaño final: ~3-4 GB
```

### Ejecutar Contenedor

```bash
# Primera ejecución (genera engine)
docker run -it --gpus all \
    --name deepstream-app \
    deepstream-yolo11x

# Primera vez tarda:
# - 5-12 min (construcción del engine)
# - Luego inicia la aplicación

# Ejecuciones posteriores (< 10 seg)
docker start -a deepstream-app
```

### Opciones Avanzadas de Docker

```bash
# Con volumen persistente para engines
docker run -it --gpus all \
    -v ./engines:/app/engines \
    -v ./configs:/app/configs \
    deepstream-yolo11x

# Con múltiples GPUs
docker run -it --gpus all \
    -e CUDA_VISIBLE_DEVICES=0,1 \
    deepstream-yolo11x

# Con puerto para API (si la aplicación expone)
docker run -it --gpus all \
    -p 5000:5000 \
    deepstream-yolo11x

# En modo detached (sin terminal)
docker run -d --gpus all \
    --name deepstream-bg \
    deepstream-yolo11x python3 main_headless.py
```

## 💻 Instalación Local (Sin Docker)

Si prefieres no usar Docker:

### 1. Clonar Proyecto

```bash
git clone https://github.com/tu-usuario/deepstream-yolo11x.git
cd deepstream-yolo11x
```

### 2. Instalar DeepStream

```bash
# Descargar DeepStream 8.0
cd /tmp
wget https://developer.nvidia.com/downloads/deepstream-8.0-x86-64-ubuntu-deb-package

# Instalar
sudo apt install ./deepstream-8.0_8.0_amd64.deb

# Verificar
ls /opt/nvidia/deepstream/
```

### 3. Instalar TensorRT

```bash
# Python API
pip3 install tensorrt

# O desde tar si es necesario
wget https://developer.nvidia.com/downloads/tensorrt
tar -xzf TensorRT-8.6.1.6.Linux.x86_64-gnu.cuda-12.0.tar.gz
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pwd)/TensorRT-8.6.1.6/lib
```

### 4. Instalar Dependencias Python

```bash
# Crear virtual environment (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip3 install -r requirements.txt

# O manualmente
pip3 install \
    ultralytics \
    opencv-python \
    numpy \
    requests \
    tensorrt \
    pyservicemaker
```

### 5. Generar Engine

```bash
# Configurar DeepStream
source setup_deepstream_env.sh

# Generar engine automáticamente
cd export_dynamic_batch
python3 auto_build_engine.py

# El script automáticamente:
# 1. Detecta GPU
# 2. Exporta YOLO11x PT → ONNX
# 3. Construye engine TensorRT
# 4. Crea config de DeepStream
```

### 6. Ejecutar Aplicación

```bash
# Volver al directorio raíz
cd ..

# Ejecutar (baja latencia - recomendado)
python3 deepstream_api/main_low_latency.py

# O modo normal
python3 deepstream_api/main.py

# O sin interfaz gráfica
python3 deepstream_api/main_headless.py
```

## 🔍 Verificación de Instalación

### Verificar GPU

```bash
# Debe mostrar tu GPU NVIDIA
nvidia-smi

# Debe mostrar CUDA
nvcc --version

# Debe mostrar TensorRT
python3 -c "import tensorrt; print(tensorrt.__version__)"

# Debe mostrar DeepStream
cat /opt/nvidia/deepstream/deepstream-8.0/version
```

### Verificar Engine

```bash
# Después de ejecutar auto_build_engine.py
ls -lh /app/engines/tensorrt/yolo11x_b1.engine

# Debe existir y ser > 100 MB
```

### Ejecutar Test

```bash
# Verificar sistema automáticamente
cd export_dynamic_batch
python3 auto_build_engine.py

# Debe imprimir:
# ✅ GPU detectada
# ✅ CUDA disponible
# ✅ TensorRT detectado
# ✅ DeepStream detectado
```

## 🚨 Solución de Problemas

### Error: "GPU not detected"

```bash
# Verificar drivers
nvidia-smi

# Reinstalar NVIDIA Container Toolkit
sudo apt remove nvidia-docker2
sudo apt install nvidia-docker2

# Reiniciar Docker
sudo systemctl restart docker

# Verificar
docker run --rm --gpus all nvidia/cuda:12.2-runtime nvidia-smi
```

### Error: "CUDA out of memory"

```bash
# Reducir workspace del engine
python3 auto_build_engine.py --workspace 4096

# O reducir aún más
python3 auto_build_engine.py --workspace 2048
```

### Error: "TensorRT not found"

```bash
# Instalar en el contenedor
docker exec <container-id> pip3 install tensorrt

# O reinstalar localmente
pip3 install --upgrade tensorrt
```

### Error: "DeepStream version mismatch"

```bash
# Verificar versión esperada
cat /opt/nvidia/deepstream/deepstream-8.0/version

# Debe ser 8.0.0 o superior

# Si no:
sudo apt remove deepstream
wget <url-a-deepstream-8.0-deb>
sudo apt install ./deepstream-8.0*.deb
```

### Error: "cuDNN not found"

```bash
# cuDNN normalmente viene con CUDA
# Si falta:
wget https://developer.nvidia.com/cudnn

# O en el Dockerfile se instala automáticamente
```

## 📊 Requisitos de Espacio

| Componente | Tamaño |
|-----------|--------|
| DeepStream 8.0 | ~700 MB |
| CUDA 12.x | ~3 GB |
| TensorRT | ~500 MB |
| YOLO11x PT | ~100 MB |
| YOLO11x ONNX | ~220 MB |
| Engine TensorRT | ~115 MB |
| **Total mínimo** | **~5 GB** |

## ✅ Checklist de Instalación

### Hardware
- [ ] GPU NVIDIA detectada (`nvidia-smi`)
- [ ] Mínimo 6 GB VRAM
- [ ] Mínimo 8 GB RAM sistema
- [ ] Mínimo 50 GB espacio disco

### Drivers
- [ ] NVIDIA Driver 550+ (`nvidia-smi`)
- [ ] CUDA 12.x (`nvcc --version`)
- [ ] nvidia-docker funcional

### Docker (Opcional)
- [ ] Docker CE instalado
- [ ] NVIDIA Container Toolkit
- [ ] Imagen construida
- [ ] GPU visible en Docker

### Aplicación
- [ ] DeepStream 8.0 detectado
- [ ] TensorRT funcional
- [ ] Engine generado
- [ ] Config de DeepStream creada
- [ ] API Laravel configurada

## 🎯 Próximos Pasos

1. ✅ Seguir instalación según tu plataforma (Docker o Local)
2. ✅ Ejecutar `auto_build_engine.py` para generar engine
3. ✅ Verificar logs de construcción
4. ✅ Configurar cámaras en API Laravel
5. ✅ Definir líneas de cruce
6. ✅ Iniciar aplicación

## 📞 Soporte

Si encuentras problemas:

1. Revisar logs: `docker logs <container>` o consola
2. Ejecutar verificación: `python3 auto_build_engine.py`
3. Revisar archivo ARCHITECTURE.md para más detalles técnicos
4. Revisar QUICKSTART.md para ejemplos

---

**Última actualización:** Noviembre 2025
**DeepStream:** 8.0.0
**CUDA:** 12.2+
**TensorRT:** 8.6+
