# DeepStream 8.0 + PeopleNet - Sistema de Control de Aforo

Sistema de conteo de ocupacion con DeepStream 8.0 y PeopleNet. Obtiene camaras desde API Laravel y procesa streams RTSP para contar Entry/Exit.

## Requisitos

- **GPU**: NVIDIA con soporte CUDA (RTX 3090/3080, TESLA T4/V100)
- **Drivers**: NVIDIA >= 525
- **Docker**: Docker Engine + nvidia-container-toolkit
- **API**: Endpoint Laravel que retorna lista de camaras RTSP

## Instalacion

### 1. Clonar repositorio

```bash
git clone <repo-url>
cd deepstream-peoplenet
```

### 2. Descargar modelo PeopleNet

Descarga desde NGC el modelo `nvidia/tao/peoplenet:deployable_quantized_onnx_v2.6.3`:

```bash
# Opcion A: Con NGC CLI
ngc registry model download-version nvidia/tao/peoplenet:deployable_quantized_onnx_v2.6.3 --dest ./models/

# Opcion B: Descarga manual desde https://catalog.ngc.nvidia.com/orgs/nvidia/teams/tao/models/peoplenet
```

Coloca los archivos en `models/peoplenet/`:
```
models/peoplenet/
├── resnet34_peoplenet.onnx      # Modelo ONNX (requerido)
├── resnet34_peoplenet_int8.txt  # Calibracion INT8 (opcional)
└── labels.txt                   # Se genera automaticamente
```

### 3. Configurar API URL

```bash
export API_URL=http://tu-servidor-laravel/api
```

### 4. Build y Run

```bash
# Build
docker compose -f docker-compose.peoplenet.yml build

# Run (modo daemon)
docker compose -f docker-compose.peoplenet.yml up -d

# Ver logs
docker compose -f docker-compose.peoplenet.yml logs -f

# Detener
docker compose -f docker-compose.peoplenet.yml down
```

## API Laravel

El sistema espera que la API retorne camaras en este formato:

```json
GET /api/camaras
[
  {
    "id": 1,
    "cam_nombre": "Entrada Principal",
    "cam_ip": "172.80.40.11",
    "cam_puerto": 554,
    "cam_usuario": "admin",
    "cam_contrasena": "password123",
    "cam_ruta": "/Streaming/Channels/1"
  }
]
```

## Funcionamiento

1. El sistema consulta la API para obtener lista de camaras
2. Conecta a cada stream RTSP
3. PeopleNet detecta personas en cada frame
4. nvdsanalytics cuenta cruces de linea (Entry/Exit)
5. Los conteos se muestran en logs (y pueden enviarse a la API)

## Configuracion

### Variables de Entorno

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `API_URL` | `http://172.80.20.22/api` | URL de la API Laravel |
| `HEADLESS` | `true` | Modo sin display (produccion) |

### Lineas de Cruce

Edita `configs/peoplenet/config_nvdsanalytics.txt` para configurar las lineas de Entry/Exit por camara.

## Estructura

```
.
├── Dockerfile.peoplenet          # Dockerfile
├── docker-compose.peoplenet.yml  # Docker Compose
├── configs/peoplenet/            # Configuraciones
│   ├── config_infer_peoplenet.txt
│   ├── config_nvdsanalytics.txt
│   └── config_tracker.txt
├── deepstream_api/
│   ├── main_peoplenet.py         # Aplicacion principal
│   └── modules/                  # Modulos Python
└── models/peoplenet/             # Modelo (usuario descarga)
```

## Troubleshooting

### "No se encontraron camaras"
- Verifica que `API_URL` sea correcta
- Verifica que la API retorne camaras

### "cudaErrorNoDevice"
- Verifica que nvidia-container-toolkit este instalado
- Reinicia el contenedor

### "Model file not found"
- Descarga el modelo PeopleNet y coloca en `models/peoplenet/`

---

**Version**: 3.0
