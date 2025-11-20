# 🏗️ Arquitectura - Auto-Build TensorRT Engine

## Descripción General

El sistema implementa una **arquitectura de auto-detección y construcción de engine TensorRT** que permite ejecutar la aplicación en cualquier PC con GPU NVIDIA, generando automáticamente un engine optimizado para ese hardware específico.

## 🎯 Problema que Resuelve

**Problema Original:**
- Los engines TensorRT son específicos para cada GPU
- No puedes usar un engine generado en una RTX 4090 en una RTX 3060
- Distribuir una aplicación con pre-built engines es inflexible

**Solución:**
- El sistema detecta automáticamente el hardware
- Genera un engine optimizado en tiempo de ejecución
- Compatible con cualquier GPU NVIDIA

## 📦 Componentes Clave

### 1. **auto_build_engine.py** - Script Principal

```python
export_dynamic_batch/auto_build_engine.py
```

**Funcionalidad:**
- Detecta GPU, CUDA, TensorRT, DeepStream
- Exporta modelo YOLO PT → ONNX (si es necesario)
- Construye engine TensorRT optimizado
- Genera configuración de DeepStream

**Clases:**
- `SystemInfo` - Detecta hardware
- `YOLOExporter` - Exporta modelos
- `EngineBuilder` - Construye engines
- `DeepStreamConfig` - Genera configuración

### 2. **entrypoint.sh** - Inicialización Docker

```bash
entrypoint.sh
```

**Flujo:**
1. Configura variables de entorno DeepStream
2. Verifica si existe engine TensorRT
3. Si no existe, ejecuta auto_build_engine.py
4. Verifica hardware
5. Ejecuta aplicación o abre terminal

### 3. **Dockerfile** - Contenedor Optimizado

```dockerfile
Dockerfile
```

**Base:** `nvcr.io/nvidia/deepstream:8.0-devel`

**Incluye:**
- CUDA 12.x
- TensorRT
- DeepStream 8.0
- Ultralytics YOLO
- pyservicemaker

## 🔄 Flujo de Ejecución

### Primera Ejecución (Sin Engine)

```
┌─────────────────────────────────────────────────────────────┐
│ Usuario ejecuta: docker run -it --gpus all deepstream-app │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ /app/entrypoint.sh carga                                   │
│ • source setup_deepstream_env.sh                           │
│ • Verifica /app/engines/tensorrt/yolo11x_b1.engine         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
        ¿Existe Engine?
             │
         NO  │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ auto_build_engine.py inicia                                │
├─────────────────────────────────────────────────────────────┤
│ 1. DETECTAR HARDWARE                                        │
│    ├─ nvidia-smi → GPU model, memory                       │
│    ├─ nvcc → CUDA version                                  │
│    ├─ tensorrt → TensorRT version                          │
│    └─ /opt/nvidia/deepstream → DeepStream version         │
│                                                             │
│ 2. BUSCAR/GENERAR ONNX                                     │
│    ├─ Busca yolo11x.onnx en rutas estándar               │
│    └─ Si no existe, descarga yolo11x.pt y lo exporta      │
│                                                             │
│ 3. CONSTRUIR ENGINE TENSORRT                               │
│    ├─ Parser ONNX → Network TensorRT                      │
│    ├─ Config batch dinámico (1-4-16)                      │
│    ├─ Habilitar FP16 si disponible                        │
│    └─ Guardar en /app/engines/tensorrt/                   │
│                                                             │
│ 4. GENERAR CONFIG DEEPSTREAM                               │
│    └─ Crear config_infer_auto_generated.txt               │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ Volver a entrypoint.sh                                      │
│ • Verificar engine generado                                │
│ • Imprimir información de sistema                          │
│ • Ejecutar aplicación (main_low_latency.py)               │
└─────────────────────────────────────────────────────────────┘
```

### Ejecuciones Posteriores (Con Engine)

```
docker run → entrypoint.sh → Verificar engine → EXISTE → main.py
```

## 📊 Detección de Hardware

### GPU

```bash
$ nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
NVIDIA RTX 3060, 12288 MB
```

**Información Capturada:**
- Modelo de GPU
- Memoria disponible
- Cantidad de GPUs

### CUDA

```bash
$ nvcc --version | grep release
release 12.2, V12.2.140
```

**Información Capturada:**
- Versión de CUDA

### TensorRT

```python
import tensorrt as trt
print(trt.__version__)  # 8.6.1
```

**Información Capturada:**
- Versión de TensorRT
- Soporte de FP16

### DeepStream

```bash
$ cat /opt/nvidia/deepstream/deepstream-8.0/version
Version: 8.0.0
```

**Información Capturada:**
- Versión de DeepStream
- Ubicación de libraries

## 🔨 Construcción del Engine

### Configuración de Batch Dinámico

```
Min shape:  (1, 3, 1280, 1280)   ← 1 cámara
Opt shape:  (4, 3, 1280, 1280)   ← 4 cámaras (optimizado)
Max shape:  (16, 3, 1280, 1280)  ← 16 cámaras máximo
```

**Ventajas:**
- Un solo engine para 1-16 cámaras
- TensorRT optimiza para 1, 4 y 16
- Sin necesidad de recompilar

### Precisión

```python
if builder.platform_has_fast_fp16:
    config.set_flag(trt.BuilderFlag.FP16)  # Más rápido, menos preciso
else:
    # Usa FP32 por defecto
```

**Decisión Automática:**
- FP16 si la GPU lo soporta (2x más rápido)
- FP32 como fallback

### Workspace

```python
config.set_memory_pool_limit(
    trt.MemoryPoolType.WORKSPACE,
    8192 * (1 << 20)  # 8 GB
)
```

**Ajuste Automático:**
- Por defecto: 8192 MB
- Reducible con `--workspace 4096` si hay problemas de memoria

## 📋 Configuración de DeepStream Generada

```ini
[property]
gpu-id=0
model-engine-file=/app/engines/tensorrt/yolo11x_b1.engine
batch-size=1
infer-dims=3;1280;1280
network-mode=0  # FP32
num-detected-classes=80

[class-attrs-0]
pre-cluster-threshold=0.25
topk=300
```

**Generada Automáticamente:**
- Ruta correcta del engine
- Configuración de batch
- Dimensiones del modelo

## 🚀 Flujo de Docker a Host

```
┌─────────────────────────────────────────────────────────┐
│ Host                                                    │
├─────────────────────────────────────────────────────────┤
│ $ docker build -t deepstream-yolo11x .                 │
│ $ docker run -it --gpus all deepstream-yolo11x         │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ Contenedor                                              │
├─────────────────────────────────────────────────────────┤
│ • NVIDIA_VISIBLE_DEVICES=all                           │
│ • /dev/nvidia0 (GPU física)                            │
│ • /app/engines/tensorrt (volumen)                      │
│                                                         │
│ ✅ Puede acceder a GPU del host                        │
│ ✅ Genera engine optimizado para esa GPU              │
│ ✅ Guarda engine en volumen persistente               │
└─────────────────────────────────────────────────────────┘
```

## 🔐 Ventajas de la Arquitectura

| Aspecto | Sin Auto-Build | Con Auto-Build |
|---------|---|---|
| **Portabilidad** | ❌ Engine GPU-específico | ✅ Genera para cada GPU |
| **Setup** | ⚠️ Manual 30+ minutos | ✅ Automático 5 min |
| **Compatibilidad** | ❌ RTX 3060 ≠ RTX 4090 | ✅ Compatible con cualquiera |
| **Distribución** | ❌ Múltiples engines | ✅ Un Dockerfile |
| **Mantenimiento** | ⚠️ Actualizar cada GPU | ✅ Auto-actualizable |

## 🎯 Casos de Uso

### Caso 1: Desarrollo Local
```bash
cd /app/export_dynamic_batch
python3 auto_build_engine.py --pt yolo11x.pt
```
✅ Rápido, sin Docker

### Caso 2: Producción en GPU Desconocida
```bash
docker run -it --gpus all deepstream-yolo11x
```
✅ Automático, seguro

### Caso 3: Múltiples Servidores
```bash
# Server 1: GPU A
docker run -it --gpus all deepstream-yolo11x
# Server 2: GPU B (diferente)
docker run -it --gpus all deepstream-yolo11x
```
✅ Cada uno genera su engine

## 🔍 Monitoreo y Debugging

### Ver GPU Detectada
```bash
docker exec <container> nvidia-smi
```

### Ver Engine Generado
```bash
docker exec <container> ls -lh /app/engines/tensorrt/
```

### Ver Logs de Construcción
```bash
docker logs <container> | grep "TensorRT"
```

### Reconstruir Engine
```bash
docker exec <container> python3 auto_build_engine.py --workspace 4096
```

## 📈 Rendimiento Esperado

**Tiempos de Construcción (Primera Ejecución):**

| GPU | FP32 | FP16 |
|-----|------|------|
| RTX 3060 | 8-12 min | 5-8 min |
| RTX 4060 | 6-10 min | 4-6 min |
| RTX 4090 | 3-5 min | 2-3 min |
| A100 | 2-3 min | 1-2 min |

**Inferencia (Por Frame):**

| # Cámaras | RTX 3060 | RTX 4060 | RTX 4090 |
|-----------|----------|----------|----------|
| 1 | 50-60 FPS | 60-70 FPS | 90-100 FPS |
| 4 | 45-50 FPS | 55-65 FPS | 80-90 FPS |
| 8 | 35-40 FPS | 45-55 FPS | 70-80 FPS |

## ⚠️ Limitaciones

1. **Engine no es portable** - Debe regenerarse en cada GPU
2. **CUDA debe estar disponible** - Se requiere nvidia-docker
3. **Primera ejecución es lenta** - Tiempo de compilación normal

## 🔄 Actualizar Modelo

Para usar un modelo diferente:

```bash
# Opción 1: Con ONNX existente
docker run -it --gpus all deepstream-yolo11x \
    python3 auto_build_engine.py --onnx /path/to/custom.onnx

# Opción 2: Con PT
docker run -it --gpus all deepstream-yolo11x \
    python3 auto_build_engine.py --pt /path/to/custom.pt
```

---

**Arquitectura Diseñada Para:** Máxima flexibilidad y portabilidad
**Fecha:** Noviembre 2025
**DeepStream:** 8.0.0
