# Sistema DeepStream con API REST

Sistema modular de detección y conteo de personas usando DeepStream + YOLO11, con configuración de cámaras desde API REST.

## 📁 Estructura del Proyecto

```
deepstream_api/
├── modules/
│   ├── __init__.py                # Exporta todos los módulos
│   ├── api_client.py              # Cliente para comunicación con API REST
│   ├── rtsp_builder.py            # Constructor de URIs RTSP
│   ├── camera_config.py           # Gestión de configuraciones de cámaras
│   └── deepstream_camera.py       # Pipeline DeepStream para cámara RTSP
├── config/                        # Configuraciones guardadas localmente
│   ├── camera_X_line.json         # Coordenadas de línea por cámara
│   └── camera_X_metadata.json     # Metadata de cámara
├── logs/                          # Logs del sistema
└── main.py                        # Script principal
```

## 🔧 Módulos

### 1. `api_client.py` - Cliente API
Gestiona la comunicación con la API REST de cámaras.

**Funciones principales:**
- `get_cameras()` - Obtiene todas las cámaras
- `get_camera_by_id(id)` - Obtiene una cámara específica
- `get_first_camera()` - Obtiene la primera cámara disponible
- `parse_coordinates(json_string)` - Parsea coordenadas de línea

**Ejemplo de uso:**
```python
from modules import CameraAPIClient

client = CameraAPIClient("http://172.80.20.22/api")
cameras = client.get_cameras()
first_camera = client.get_first_camera()
```

### 2. `rtsp_builder.py` - Constructor RTSP
Construye URIs RTSP desde datos de cámaras.

**Funciones principales:**
- `build_rtsp_uri(camera_data)` - Construye URI RTSP completa
- `validate_rtsp_uri(uri)` - Valida formato de URI
- `get_camera_info(camera_data)` - Extrae información legible

**Ejemplo de uso:**
```python
from modules import RTSPBuilder

camera = {
    "cam_ip": "172.80.40.12",
    "cam_port": 554,
    "cam_user": "admin",
    "cam_password": "Radimer01",
    "cam_rstp": "Streaming/Channels/1"
}

uri = RTSPBuilder.build_rtsp_uri(camera)
# Resultado: rtsp://admin:Radimer01@172.80.40.12:554/Streaming/Channels/1
```

### 3. `camera_config.py` - Configuración
Gestiona configuraciones locales de cámaras (líneas de conteo, metadata).

**Funciones principales:**
- `get_line_config(camera_id, api_coords)` - Obtiene config de línea (local o API)
- `save_line_config(camera_id, start, end, direction)` - Guarda línea editada
- `get_camera_metadata(camera_data)` - Extrae metadata importante
- `save_camera_metadata(camera_id, metadata)` - Guarda metadata

**Prioridad de configuración:**
1. Archivo local (si el usuario editó la línea)
2. API (coordenadas desde `cam_coordenadas`)

### 4. `deepstream_camera.py` - Pipeline DeepStream
Pipeline completo de DeepStream para procesar una cámara RTSP.

**Características:**
- Conexión a cámaras RTSP
- Detección de personas con YOLO11x
- Tracking de objetos con nvtracker
- Conteo por línea de cruce
- Visualización en tiempo real

## 🚀 Uso

### Ejecutar con primera cámara de la API

```bash
cd deepstream_api
python3 main.py
```

El sistema automáticamente:
1. Conecta a la API en `http://172.80.20.22/api/camaras`
2. Obtiene la primera cámara disponible
3. Construye la URI RTSP
4. Carga configuración de línea (API o local)
5. Inicia el pipeline DeepStream
6. Muestra video con detecciones y contadores

## 📊 Formato de Datos API

La API debe retornar este formato en `/api/camaras`:

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "zonas_id": 1,
            "cam_nombre": "Oficina Garunia Esquina",
            "cam_ip": "172.80.40.12",
            "cam_port": 554,
            "cam_user": "admin",
            "cam_password": "Radimer01",
            "cam_coordenadas": "{\"end\": [1380, 642], \"start\": [1093, 1083], \"direccion_entrada\": \"derecha\"}",
            "cam_rstp": "Streaming/Channels/1"
        }
    ]
}
```

### Campos requeridos:
- `id` - ID único de la cámara
- `cam_nombre` - Nombre descriptivo
- `cam_ip` - IP de la cámara
- `cam_port` - Puerto RTSP (default: 554)
- `cam_user` - Usuario de autenticación
- `cam_password` - Contraseña
- `cam_rstp` - Path del stream (ej: "Streaming/Channels/1")
- `cam_coordenadas` - JSON string con coordenadas de línea

### Formato de `cam_coordenadas`:
```json
{
    "start": [x1, y1],
    "end": [x2, y2],
    "direccion_entrada": "izquierda" | "derecha"
}
```

## 🎛️ Controles

- **Q** - Salir del programa
- **Ctrl+C** - Interrupción segura

## 📝 Configuraciones Guardadas

El sistema guarda configuraciones en `config/`:

### `camera_X_line.json`
```json
{
  "start": [1093, 1083],
  "end": [1380, 642],
  "direccion_entrada": "derecha"
}
```

### `camera_X_metadata.json`
```json
{
  "id": 1,
  "nombre": "Oficina Garunia Esquina",
  "zona_id": 1,
  "ip": "172.80.40.12"
}
```

## 🔍 Logs y Debug

El sistema muestra información detallada:
- ✅ Conexión exitosa a API
- 📹 Cámara seleccionada
- 🔗 URI RTSP construida
- 📐 Configuración de línea cargada
- 🔍 Detecciones en tiempo real
- ✅/⬅️ Eventos de entrada/salida

## 🛠️ Requisitos

- Python 3.8+
- GStreamer 1.0
- DeepStream 7.1
- NVIDIA GPU
- OpenCV
- requests

## 📦 Dependencias Python

```bash
pip install requests opencv-python numpy
```

## 🏗️ Arquitectura

```
API REST → CameraAPIClient → RTSPBuilder → DeepStreamCamera
                ↓
         CameraConfig → LineCrossingDetector
                ↓
           GStreamer Pipeline
                ↓
         YOLO11 + Tracker → Conteo
```

## 🔐 Seguridad

- Las credenciales se URL-encodean automáticamente
- Las contraseñas no se muestran en logs (se ocultan con ***)
- Las configuraciones locales sobreescriben las de API (permite personalización)

## 📈 Performance (Procesamiento en GPU)

**DeepStream aprovecha la GPU al máximo:**

| Componente | Procesamiento | Uso |
|------------|---------------|-----|
| **Decoder** | GPU | H.264 → RAW |
| **YOLO Inference** | GPU (TensorRT) | Detección |
| **Tracking** | GPU | nvtracker |
| **Video Convert** | GPU | Formatos |
| **Control Pipeline** | CPU | <10% |

### Métricas Esperadas

- **GPU Usage**: 80-95% ✅ (Correcto - procesamiento completo)
- **CPU Usage**: <10% ✅ (Solo control del pipeline)
- **FPS**: 25-30 (depende de red RTSP)
- **Latencia**: ~30ms por frame
- **VRAM**: 2-3GB (modelo + buffers)

### ⚠️ Indicadores de Problemas

| Síntoma | Causa | Solución |
|---------|-------|----------|
| CPU >50% | No usa GPU | Verificar decoder/pipeline |
| GPU <20% | Pipeline incorrecto | Revisar configuración |
| FPS <15 | Red lenta o GPU saturada | Verificar conexión/recursos |

**Recuerda**: DeepStream está diseñado para GPU. CPU baja es NORMAL y CORRECTO.

---

## 🎯 Próximas Funcionalidades

- [ ] Soporte para múltiples cámaras simultáneas
- [ ] Envío de eventos a API
- [ ] Dashboard web con estadísticas
- [ ] Reconexión automática si se cae el stream
- [ ] Grabación de eventos
