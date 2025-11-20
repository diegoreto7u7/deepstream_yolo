# 🚀 Quick Start - DeepStream + YOLO11x con Auto-Build

## Descripción

Este proyecto implementa un sistema de detección de personas con conteo de entradas/salidas usando:
- **YOLO11x** para detección
- **DeepStream 8.0** para procesamiento en GPU
- **TensorRT** para inferencia optimizada
- **Auto-generación de engine** optimizado para tu GPU

## 📋 Requisitos

### Hardware
- **GPU NVIDIA** (RTX 3060, RTX 4060, A100, etc.)
- **Mínimo 6GB de VRAM GPU**
- **Mínimo 8GB de RAM**
- **Docker con soporte NVIDIA**

### Software
- Docker (versión 19.03+)
- NVIDIA Container Toolkit
- nvidia-docker

## 🚀 Uso Rápido

### Opción 1: Con Docker (Recomendado)

```bash
# Construir imagen Docker
docker build -t deepstream-yolo11x .

# Ejecutar contenedor
docker run -it --gpus all \
    -e NVIDIA_VISIBLE_DEVICES=all \
    deepstream-yolo11x

# El contenedor detectará tu GPU y generará el engine automáticamente
```

### Opción 2: En el Host (Sin Docker)

```bash
# 1. Instalar dependencias
pip3 install ultralytics tensorrt pyservicemaker

# 2. Configurar DeepStream
source setup_deepstream_env.sh

# 3. Auto-generar engine
cd export_dynamic_batch
python3 auto_build_engine.py

# 4. Ejecutar aplicación
cd ..
python3 main_low_latency.py
```

## 🔧 Generación Automática de Engine

El sistema detecta automáticamente:
- ✅ GPU disponible (modelo, memoria)
- ✅ Versión de CUDA
- ✅ Versión de TensorRT
- ✅ DeepStream instalado

### Uso Manual del Script

```bash
# Auto-detectar todo y usar yolo11x.onnx por defecto
python3 auto_build_engine.py

# Usar un ONNX específico
python3 auto_build_engine.py --onnx /ruta/a/model.onnx

# Exportar de PT a ONNX y luego a engine
python3 auto_build_engine.py --pt /ruta/a/model.pt

# Con opciones personalizadas
python3 auto_build_engine.py \
    --onnx model.onnx \
    --workspace 4096 \
    --no-fp16 \
    --output custom_engine.engine
```

## 📊 Estructura del Proyecto

```
/app/
├── export_dynamic_batch/
│   ├── auto_build_engine.py          # Script principal de auto-build
│   ├── yolo11x.onnx                  # Modelo ONNX (si existe)
│   └── yolo11x.pt                    # Modelo PT (descargado)
│
├── engines/
│   ├── tensorrt/
│   │   └── yolo11x_b1.engine         # Engine generado automáticamente
│   └── onnx/
│       └── yolo11x_dynamic.onnx
│
├── configs/
│   └── deepstream/
│       ├── config_infer_*.txt        # Configuraciones de DeepStream
│       └── labels.txt
│
├── deepstream_api/
│   ├── main_low_latency.py           # Entrada principal (baja latencia)
│   ├── main.py                       # Entrada normal
│   ├── main_headless.py              # Sin interfaz gráfica
│   └── modules/
│       ├── deepstream_camera_sm.py
│       ├── line_crossing_detector.py
│       └── ...
│
├── entrypoint.sh                     # Script de inicialización Docker
├── Dockerfile                        # Dockerfile optimizado
├── setup_deepstream_env.sh           # Configuración de variables de entorno
└── QUICKSTART.md                     # Este archivo
```

## 🎯 Flujo de Ejecución

```
┌──────────────────────────┐
│ Docker run               │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ entrypoint.sh            │
│  • Load DeepStream env   │
│  • Check GPU             │
└────────────┬─────────────┘
             │
             ▼
    ¿Engine existe?
         /  \
       SÍ    NO
       │      │
       │      ▼
       │   ┌──────────────────────┐
       │   │ auto_build_engine.py │
       │   │  • Detect GPU        │
       │   │  • Build engine      │
       │   │  • Save to /engines/ │
       │   └──────────┬───────────┘
       │              │
       └──────┬───────┘
              │
              ▼
┌──────────────────────────┐
│ main_low_latency.py      │
│  • Load API cámaras      │
│  • Setup pipelines       │
│  • Run inference         │
└──────────────────────────┘
```

## 🔍 Verificación del Sistema

```bash
# Verificar GPU
nvidia-smi

# Verificar CUDA
nvcc --version

# Verificar TensorRT
python3 -c "import tensorrt; print(tensorrt.__version__)"

# Verificar DeepStream
cat /opt/nvidia/deepstream/deepstream-8.0/version

# Verificar engine
ls -lh /app/engines/tensorrt/*.engine
```

## ⚠️ Solución de Problemas

### "GPU no detectada"
```bash
# Verificar NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.0-runtime-ubuntu20.04 nvidia-smi
```

### "TensorRT no disponible"
```bash
# Instalar dentro del contenedor
pip3 install tensorrt
```

### "CUDA out of memory"
```bash
# Reducir workspace
python3 auto_build_engine.py --workspace 4096
```

### "FP16 no disponible"
```bash
# Usar FP32
python3 auto_build_engine.py --no-fp16
```

## 📝 Configuración de Cámaras

Las cámaras se configuran a través de una API Laravel. Edita `deepstream_api/main_low_latency.py`:

```python
api_url = "http://tu-laravel-api.com/api"
```

Las líneas de cruce se definen en formato:
```json
{
  "cam_coordenadas": {
    "start": [960, 540],
    "end": [1200, 540],
    "direccion_entrada": "izquierda"
  }
}
```

## 🚀 Ejecutar la Aplicación

### Modo Baja Latencia (Recomendado)
```bash
python3 main_low_latency.py
```

### Modo Normal
```bash
python3 main.py
```

### Modo Headless (Solo terminal, sin display)
```bash
python3 main_headless.py
```

## 📊 Esperado en Producción

Con RTX 3060 / RTX 4060:
- **1 cámara**: ~50-60 FPS
- **4 cámaras**: ~45-50 FPS cada una
- **8+ cámaras**: Rendimiento degradado

## 🔐 Notas de Seguridad

- El engine TensorRT es específico para cada GPU
- Cada contenedor genera su propio engine automáticamente
- Los engines no son portables entre diferentes GPUs

## 📚 Documentación Adicional

- [DeepStream Official Docs](https://docs.nvidia.com/metropolis/deepstream/dev-guide/)
- [YOLO11 Documentation](https://docs.ultralytics.com/)
- [TensorRT Developer Guide](https://docs.nvidia.com/deeplearning/tensorrt/developer-guide/)

## ✅ Checklist de Inicio

- [ ] Docker instalado con soporte NVIDIA
- [ ] Imagen construida: `docker build -t deepstream-yolo11x .`
- [ ] Contenedor ejecutándose: `docker run -it --gpus all deepstream-yolo11x`
- [ ] Engine generado automáticamente
- [ ] API Laravel configurada
- [ ] Cámaras conectadas
- [ ] Líneas de cruce definidas

## 🤝 Soporte

Para problemas, revisar los logs:
```bash
docker logs <container-id>
```

O ejecutar en el contenedor:
```bash
python3 export_dynamic_batch/auto_build_engine.py
```

---

**Última actualización**: Noviembre 2025
**DeepStream**: 8.0.0
**YOLO**: 11x
