# 📁 Estructura del Proyecto - DeepStream YOLO11x Auto-Build

## 🎯 Descripción General

Proyecto completo de detección de personas con conteo bidireccional usando YOLO11x + DeepStream 8.0 con **auto-generación de engines TensorRT** optimizados para cualquier GPU NVIDIA.

---

## 📂 Estructura de Directorios

```
/app/
│
├── 📄 Archivos de Configuración
│   ├── setup_deepstream_env.sh          # Variables de entorno DeepStream 8.0
│   ├── Dockerfile                        # Imagen Docker optimizada
│   └── entrypoint.sh                     # Script inicial para Docker
│
├── 📚 Documentación (NUEVA)
│   ├── QUICKSTART.md                     # Guía rápida de inicio
│   ├── ARCHITECTURE.md                   # Documentación técnica
│   ├── INSTALL.md                        # Guía de instalación
│   ├── AUTO_BUILD_SUMMARY.txt            # Resumen del sistema auto-build
│   └── PROJECT_STRUCTURE.md              # Este archivo
│
├── 🤖 Exportación y Build de Engines (ACTUALIZADO)
│   └── export_dynamic_batch/
│       ├── auto_build_engine.py          # ⭐ Script principal AUTO-BUILD (NUEVO)
│       ├── build_trt_dynamic.sh          # Script bash alternativo
│       ├── build_trt_dynamic_fixed.sh    # Script bash para TensorRT 10.x
│       ├── build_trt_dynamic_python.py   # Build usando Python API
│       ├── export_yolo11x_dynamic.py     # Export YOLO PT → ONNX
│       ├── yolo11x.onnx                  # Modelo ONNX (si existe)
│       ├── yolo11x.pt                    # Modelo PT (descargado)
│       ├── README.md                     # Documentación de exportación
│       └── config_infer_yolo11x_dynamic.txt
│
├── 🎬 Engines de Inferencia
│   └── engines/
│       ├── tensorrt/
│       │   ├── yolo11x_b1.engine         # Engine TensorRT batch=1 (generado)
│       │   └── yolo11x_dynamic.engine    # Engine TensorRT dinámico (1-16 batch)
│       └── onnx/
│           └── yolo11x_dynamic.onnx      # Modelo ONNX
│
├── ⚙️ Configuración DeepStream
│   └── configs/deepstream/
│       ├── config_infer_primary_yolo11x_b1.txt       # Config batch=1
│       ├── config_infer_yolo11x_dynamic.txt          # Config dinámico
│       ├── tracker_config.txt                        # Config tracker
│       └── labels.txt                    # Etiquetas YOLO COCO (80 clases)
│
├── 🚀 API Principal (ACTUALIZADO)
│   └── deepstream_api/
│       ├── main.py                       # Entrada principal
│       ├── main_low_latency.py           # Entrada baja latencia (RECOMENDADO)
│       ├── main_headless.py              # Sin interfaz gráfica
│       ├── README.md                     # Documentación de la API
│       ├── README_LOW_LATENCY.md         # Info sobre baja latencia
│       ├── setup.sh                      # Setup script
│       ├── run.sh                        # Script para ejecutar
│       ├── run_headless.sh               # Script headless
│       │
│       ├── utils/
│       │   ├── calculate_coordinates.py  # ⭐ Calculadora de coordenadas (MEJORADO)
│       │   └── convert_my_coordinates.py # ⭐ Conversor personalizado (MEJORADO)
│       │
│       └── modules/
│           ├── __init__.py
│           ├── api_client.py             # Cliente API Laravel
│           ├── camera_config.py          # Gestión de config de cámaras
│           ├── rtsp_builder.py           # Construcción de URIs RTSP
│           ├── line_crossing_detector.py # Detector de cruces de línea
│           ├── deepstream_camera_sm.py                 # Camera con pyservicemaker (ACTUALIZADO)
│           ├── deepstream_camera_sm_low_latency.py     # Camera baja latencia (ACTUALIZADO)
│           ├── deepstream_camera_recorder.py           # Camera con grabación
│           ├── threaded_camera.py        # Wrapper thread-safe
│           ├── threaded_camera_headless.py
│           ├── threaded_camera_low_latency.py
│           ├── multi_camera_manager.py   # Gestor de múltiples cámaras
│           └── config/                   # Configuraciones guardadas
│
├── 📦 Librerías Compiladas
│   └── libnvdsinfer_custom_impl_Yolo.so  # Librería custom parser YOLO
│
└── 📄 Archivos Raíz
    ├── README.md                         # README principal
    ├── requirements.txt                  # Dependencias Python
    ├── .gitignore                        # Archivos ignorados por git
    └── LICENSE                           # Licencia del proyecto
```

---

## 🔄 Flujo de Archivos

### 1️⃣ Inicialización (Docker)

```
entrypoint.sh
  ├─ source setup_deepstream_env.sh
  ├─ Verifica /app/engines/tensorrt/yolo11x_b1.engine
  └─ Si NO existe:
      └─ python3 export_dynamic_batch/auto_build_engine.py
         ├─ Detecta GPU
         ├─ Exporta YOLO11x PT → ONNX
         ├─ Construye engine TensorRT
         └─ Guarda en /app/engines/tensorrt/
```

### 2️⃣ Ejecución Principal

```
main_low_latency.py
  ├─ Cargar API client → api_client.py
  ├─ Obtener cámaras desde Laravel
  ├─ Para cada cámara:
  │   ├─ rtsp_builder.py → Construir URI RTSP
  │   ├─ camera_config.py → Cargar config de línea
  │   └─ deepstream_camera_sm_low_latency.py
  │       ├─ line_crossing_detector.py
  │       ├─ Cargar config: configs/deepstream/config_infer_*.txt
  │       ├─ Cargar engine: engines/tensorrt/yolo11x_b1.engine
  │       └─ Procesar stream RTSP
  │
  └─ multi_camera_manager.py → Coordinar todas las cámaras
```

### 3️⃣ Procesamiento de Detecciones

```
deepstream_camera_sm_low_latency.py
  ├─ Recibe frames de RTSP
  ├─ Pasa por YOLO (via engine TensorRT)
  ├─ Para cada persona detectada:
  │   ├─ line_crossing_detector.py → Detectar cruce
  │   ├─ Actualizar contadores
  │   └─ Dibujar línea (1280x720)
  │
  └─ Enviar a pantalla o archivo
```

---

## 📊 Archivos Clave por Funcionalidad

### Auto-Build Engine (NUEVO) ⭐

| Archivo | Propósito |
|---------|-----------|
| `export_dynamic_batch/auto_build_engine.py` | Script principal de detección y construcción |
| `entrypoint.sh` | Verificación automática e inicialización |
| `Dockerfile` | Imagen Docker optimizada |
| `setup_deepstream_env.sh` | Variables de entorno (ACTUALIZADO a 8.0) |

### Coordinación de Cámaras

| Archivo | Propósito |
|---------|-----------|
| `deepstream_api/main_low_latency.py` | Entrada principal |
| `deepstream_api/modules/multi_camera_manager.py` | Gestor de múltiples streams |
| `deepstream_api/modules/api_client.py` | Comunicación con Laravel API |
| `deepstream_api/modules/camera_config.py` | Gestión de configuración |

### Detección y Cruce

| Archivo | Propósito |
|---------|-----------|
| `deepstream_api/modules/deepstream_camera_sm_low_latency.py` | Pipeline con baja latencia (ACTUALIZADO) |
| `deepstream_api/modules/line_crossing_detector.py` | Lógica de cruce de línea |
| `deepstream_api/modules/rtsp_builder.py` | Construcción de URIs RTSP |

### Configuración de DeepStream

| Archivo | Propósito |
|---------|-----------|
| `configs/deepstream/config_infer_primary_yolo11x_b1.txt` | Config YOLO batch=1 |
| `configs/deepstream/config_infer_yolo11x_dynamic.txt` | Config YOLO dinámico |
| `configs/deepstream/labels.txt` | Etiquetas COCO (80 clases) |

### Herramientas de Coordenadas (ACTUALIZADO) ⭐

| Archivo | Propósito |
|---------|-----------|
| `deepstream_api/utils/calculate_coordinates.py` | Calculadora de escalado (con round()) |
| `deepstream_api/utils/convert_my_coordinates.py` | Conversor personalizado (con round()) |

### Documentación (NUEVA) 📚

| Archivo | Propósito |
|---------|-----------|
| `QUICKSTART.md` | Inicio rápido en 5 minutos |
| `ARCHITECTURE.md` | Documentación técnica detallada |
| `INSTALL.md` | Guía de instalación paso a paso |
| `AUTO_BUILD_SUMMARY.txt` | Resumen del sistema |
| `PROJECT_STRUCTURE.md` | Este archivo |

---

## 🔧 Archivos Modificados en Esta Sesión

### Cambios Realizados

1. **setup_deepstream_env.sh** (Actualizado)
   - Cambio: DeepStream 7.1 → DeepStream 8.0
   - Razón: Versión actual instalada es 8.0.0

2. **deepstream_camera_sm.py** (Actualizado)
   - Cambio: Eliminado escalado de coordenadas (int() a round())
   - Razón: Laravel envía coordenadas ya en el espacio correcto
   - Ahora: Usa coordenadas directamente sin transformación

3. **deepstream_camera_sm_low_latency.py** (Actualizado)
   - Cambio: Eliminado escalado de coordenadas
   - Cambio: Ventana 1280x720 (no pantalla completa)
   - Cambio: Agregados parámetros de baja latencia

4. **calculate_coordinates.py** (Creado/Actualizado)
   - Cambio: int() → round() para mayor precisión
   - Cambio: Documentación mejorada
   - Nuevo: Tabla de referencia completa

5. **convert_my_coordinates.py** (Creado)
   - Nuevo: Script personalizado para conversiones
   - Función: Facilitar cálculos de coordenadas específicas

### Archivos Nuevos

1. **auto_build_engine.py** (⭐ Principal)
   - 600+ líneas
   - Detección automática de hardware
   - Construcción de engines TensorRT
   - Generación de configuración

2. **entrypoint.sh**
   - Inicialización Docker automática
   - Verificación de engine
   - Ejecución de auto_build_engine.py si necesario

3. **Dockerfile**
   - Base: nvidia/deepstream:8.0-devel
   - Instalación automática de dependencias
   - Listo para cualquier GPU

4. **QUICKSTART.md**
   - Guía rápida
   - 3 opciones de uso
   - Solución de problemas

5. **ARCHITECTURE.md**
   - Documentación técnica
   - Flujos de ejecución
   - Especificaciones técnicas

6. **INSTALL.md**
   - Instalación paso a paso
   - Ubuntu 20.04/22.04
   - Solución de problemas específicos

---

## 📈 Tamaños Aproximados

| Componente | Tamaño |
|-----------|--------|
| Código fuente Python | ~500 KB |
| Configuraciones | ~50 KB |
| YOLO11x PT | ~100 MB |
| YOLO11x ONNX | ~220 MB |
| Engine TensorRT | ~115 MB |
| DeepStream (Docker) | ~700 MB |
| CUDA (Docker) | ~3 GB |
| **Total mínimo (host)** | **~5 GB** |
| **Docker imagen** | **~3-4 GB** |

---

## 🔐 Dependencias Críticas

### Python Packages

```
tensorrt>=8.6
ultralytics>=8.0
opencv-python>=4.8
numpy>=1.24
requests>=2.31
pyservicemaker>=0.1
```

### Librerías del Sistema

```
CUDA 12.x
TensorRT 8.6+
DeepStream 8.0.0
GStreamer 1.20+
NVIDIA Drivers 550+
```

---

## 🚀 Cómo Usar Este Proyecto

### Opción 1: Docker (Recomendado)

```bash
docker build -t deepstream-yolo11x .
docker run -it --gpus all deepstream-yolo11x
# Auto-genera engine y comienza
```

### Opción 2: Host Local

```bash
source setup_deepstream_env.sh
cd export_dynamic_batch
python3 auto_build_engine.py
cd ..
python3 deepstream_api/main_low_latency.py
```

### Opción 3: Personalizado

```bash
python3 export_dynamic_batch/auto_build_engine.py \
    --onnx custom_model.onnx \
    --workspace 4096 \
    --no-fp16
```

---

## 📞 Archivos de Referencia Rápida

| Necesito... | Ver archivo... |
|-----------|---------|
| Inicio rápido | QUICKSTART.md |
| Instalar software | INSTALL.md |
| Entender arquitectura | ARCHITECTURE.md |
| Ver estructura completa | PROJECT_STRUCTURE.md (este) |
| Ajustar coordenadas | utils/convert_my_coordinates.py |
| Agregar nueva cámara | deepstream_api/main_low_latency.py |
| Cambiar modelo YOLO | export_dynamic_batch/auto_build_engine.py |

---

## ✅ Checklist de Archivos

Core Functionality:
- [x] entrypoint.sh
- [x] setup_deepstream_env.sh
- [x] Dockerfile

Auto-Build:
- [x] auto_build_engine.py
- [x] Detección de GPU
- [x] Construcción de engine
- [x] Generación de config

API y Cámaras:
- [x] main_low_latency.py
- [x] deepstream_camera_sm_low_latency.py
- [x] multi_camera_manager.py
- [x] line_crossing_detector.py

Utilidades:
- [x] calculate_coordinates.py
- [x] convert_my_coordinates.py
- [x] api_client.py
- [x] rtsp_builder.py

Documentación:
- [x] QUICKSTART.md
- [x] ARCHITECTURE.md
- [x] INSTALL.md
- [x] AUTO_BUILD_SUMMARY.txt
- [x] PROJECT_STRUCTURE.md

---

**Última actualización:** Noviembre 2025
**DeepStream:** 8.0.0
**YOLO:** 11x
**Estado:** ✅ Completamente funcional

