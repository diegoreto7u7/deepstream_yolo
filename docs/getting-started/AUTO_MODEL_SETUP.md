# 📥 Auto-descarga y Configuración de Modelos

## Resumen

El script `auto_build_engine.py` ahora **descarga automáticamente** el modelo YOLO11x y genera el engine TensorRT sin necesidad de subir archivos grandes a GitHub.

## Flujo Automático

```
auto_build_engine.py ejecutado
    ↓
¿Existe ONNX local?
    ├→ SÍ: Usar directamente
    └→ NO: ¿Existe PT local?
        ├→ SÍ: Convertir a ONNX
        └→ NO: Descargar yolo11x.pt automáticamente
            ↓
        Convertir PT → ONNX
            ↓
        Generar TensorRT engine
            ↓
        Crear configuración DeepStream
```

## Ventajas

✅ **No necesitas subir modelos grandes a GitHub**
- ONNX (219 MB) y PT (257 MB) se excluyen del repositorio
- Repositorio más limpio y eficiente

✅ **Funciona en cualquier PC**
- Auto-descarga el modelo la primera vez
- Genera engine optimizado para tu GPU específica

✅ **100% automatizado**
- Solo ejecuta: `python3 auto_build_engine.py`
- Todo se configura solo

## Uso

### Opción 1: Auto-detección (Recomendado)

```bash
python3 /app/engines/auto_build_engine.py
```

El script:
1. Busca ONNX local
2. Si no existe, busca PT local
3. Si no existe, descarga yolo11x.pt automáticamente
4. Convierte a ONNX
5. Genera engine TensorRT
6. Crea configuración DeepStream

### Opción 2: Usar ONNX local

```bash
python3 /app/engines/auto_build_engine.py --onnx /ruta/a/tu/modelo.onnx
```

### Opción 3: Usar PT local

```bash
python3 /app/engines/auto_build_engine.py --pt /ruta/a/tu/modelo.pt
```

### Opción 4: Especificar salida

```bash
python3 /app/engines/auto_build_engine.py \
    --output /app/engines/tensorrt/yolo11x_custom.engine \
    --workspace 16384
```

## Parámetros

| Parámetro | Descripción | Defecto |
|-----------|-------------|---------|
| `--onnx` | Ruta a modelo ONNX | Auto-detectar |
| `--pt` | Ruta a modelo PT | Auto-detectar |
| `--output` | Ruta salida engine | `*.engine` mismo directorio |
| `--workspace` | Memoria workspace (MB) | 8192 |
| `--no-fp16` | Desabilitar FP16 | FP16 habilitado |

## Descarga Automática

### Primera Ejecución

La primera vez tarda más tiempo (10-15 minutos):

```
📥 DESCARGANDO MODELO YOLO11x
=======================================================================
📂 Directorio de destino: /app/engines/pt
⏳ Descargando modelo (5-10 minutos)...
   Tamaño: ~219 MB

... [descargando] ...

✅ Modelo descargado: /app/engines/pt/yolo11x.pt
📊 Tamaño: 257.00 MB

📦 EXPORTANDO MODELO YOLO PT A ONNX
=======================================================================
📂 Cargando modelo: /app/engines/pt/yolo11x.pt

⚙️  Configuración de exportación:
   Formato: ONNX
   Tamaño entrada: 1280x1280
   Batch: DINÁMICO (1-16)
   Opset: 17

🔄 Exportando (2-5 minutos)...

✅ ONNX exportado: /app/engines/onnx/yolo11x.onnx
```

### Ejecuciones Posteriores

Si ya existe ONNX o PT localmente, se salta la descarga:

```
✅ Modelo ONNX ya existe: /app/engines/onnx/yolo11x.onnx
   Tamaño: 219.34 MB

🚀 GENERANDO ENGINE TENSORRT
=======================================================================
... [genera engine] ...
```

## Directorios

Después de la primera ejecución:

```
/app/engines/
├── auto_build_engine.py      # Script principal
├── pt/
│   └── yolo11x.pt           # Descargado automáticamente
├── onnx/
│   └── yolo11x.onnx         # Generado automáticamente
└── tensorrt/
    └── yolo11x_b1.engine    # Engine compilado
```

## GitHub

✅ **No hay archivos grandes en el repositorio**

```
.gitignore:
*.onnx      # Excluye todos los ONNX
*.pt        # Excluye todos los PT
engines/onnx/
engines/pt/
```

Cuando clonas el repositorio:
- ✅ Obtiene `auto_build_engine.py`
- ✅ Obtiene `entrypoint.sh`
- ✅ Obtiene todo el código
- ❌ No obtiene modelos grandes (se descargan automáticamente)

## Docker

El `entrypoint.sh` ejecuta automáticamente:

```bash
python3 /app/engines/auto_build_engine.py
```

Así que cuando corres:

```bash
docker run -it deepstream-app python3 main_low_latency.py
```

El proceso completo es:
1. Descargar yolo11x.pt (si no existe)
2. Exportar a ONNX (si no existe)
3. Generar engine TensorRT (si no existe)
4. Iniciar aplicación con engine generado

## Troubleshooting

### Error: "No GPU detected"

```bash
# Verificar GPU
nvidia-smi

# Ejecutar con CPU (muy lento, no recomendado)
python3 auto_build_engine.py --no-fp16
```

### Error: "ONNX parse failed"

```bash
# Usar PT en lugar de ONNX
python3 auto_build_engine.py --pt /app/engines/pt/yolo11x.pt
```

### Error: "Out of memory"

```bash
# Reducir workspace
python3 auto_build_engine.py --workspace 4096
```

### Descarga muy lenta

La descarga de 219 MB depende de tu conexión:
- Conexión 1 Mbps: ~30 minutos
- Conexión 10 Mbps: ~3 minutos
- Conexión 100 Mbps: ~20 segundos

Usa una conexión más rápida si es posible.

## Configuración DeepStream

El script automáticamente crea configuración en:

```
/app/configs/deepstream/config_infer_primary_yolo11x_b1.txt
```

Con la ruta al engine generado listo para usar.

## Próximos Pasos

```bash
# 1. (Opcional) Generar engine manualmente
python3 /app/engines/auto_build_engine.py

# 2. Usar en Docker
docker build -t deepstream-app .
docker run -it deepstream-app python3 main_low_latency.py

# 3. O en local
python3 main_low_latency.py
```

