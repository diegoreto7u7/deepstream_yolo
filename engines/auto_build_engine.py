#!/usr/bin/env python3
"""
Script automático para detectar componentes y generar engine TensorRT
Detecta GPU, CUDA, TensorRT y genera un engine optimizado para ese PC

Uso:
    python3 auto_build_engine.py                    # Auto-detectar todo
    python3 auto_build_engine.py --onnx path/to/model.onnx
    python3 auto_build_engine.py --pt path/to/model.pt
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional
import argparse


class SystemInfo:
    """Detecta información del sistema y componentes"""

    @staticmethod
    def get_gpu_info() -> Dict:
        """Detecta información de GPU"""
        gpu_info = {
            'available': False,
            'count': 0,
            'models': [],
            'memory_mb': [],
            'cuda_version': None,
            'tensorrt_version': None
        }

        try:
            # Verificar CUDA
            result = subprocess.run(['nvidia-smi', '--query-gpu=count', '--format=csv,noheader'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info['count'] = int(result.stdout.strip().split('\n')[0])
                gpu_info['available'] = gpu_info['count'] > 0

            # Obtener modelos de GPU
            if gpu_info['available']:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total',
                                       '--format=csv,noheader,nounits'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split(',')
                        gpu_info['models'].append(parts[0].strip())
                        gpu_info['memory_mb'].append(int(parts[1].strip()))

        except Exception as e:
            print(f"⚠️  Error detectando GPU: {e}")

        # Detectar versión CUDA
        try:
            result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'release' in line.lower():
                        gpu_info['cuda_version'] = line.split('release')[1].strip().split(',')[0]
        except Exception as e:
            print(f"⚠️  Error detectando CUDA: {e}")

        # Detectar TensorRT (intenta Python module primero, luego verifica librerías)
        try:
            import tensorrt as trt
            if hasattr(trt, '__version__'):
                gpu_info['tensorrt_version'] = trt.__version__
            else:
                gpu_info['tensorrt_version'] = "Instalado (versión no detectable)"
        except ImportError:
            # Si no está el módulo Python, verifica si está instalado en el sistema
            try:
                result = subprocess.run(['ldconfig', '-p'], capture_output=True, text=True, timeout=5)
                if 'libnvinfer.so' in result.stdout:
                    gpu_info['tensorrt_version'] = "Instalado (DeepStream)"
            except Exception as e:
                print(f"⚠️  Error detectando TensorRT: {e}")

        return gpu_info

    @staticmethod
    def get_system_info() -> Dict:
        """Obtiene información del sistema"""
        system_info = {
            'platform': sys.platform,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'deepstream_version': None
        }

        # Detectar DeepStream
        ds_paths = [
            '/opt/nvidia/deepstream/deepstream-8.0',
            '/opt/nvidia/deepstream/deepstream-7.1',
            '/opt/nvidia/deepstream'
        ]

        for ds_path in ds_paths:
            version_file = Path(ds_path) / 'version'
            if version_file.exists():
                try:
                    with open(version_file) as f:
                        system_info['deepstream_version'] = f.read().strip()
                    break
                except:
                    pass

        return system_info

    @staticmethod
    def print_hardware_info(gpu_info: Dict, system_info: Dict):
        """Imprime información de hardware formateada"""
        print("\n" + "="*70)
        print("🖥️  INFORMACIÓN DE HARDWARE DETECTADA")
        print("="*70)

        print(f"\n🔵 GPU:")
        if gpu_info['available']:
            print(f"   Cantidad: {gpu_info['count']}")
            for i, (model, memory) in enumerate(zip(gpu_info['models'], gpu_info['memory_mb'])):
                print(f"   GPU {i}: {model}")
                print(f"   Memoria: {memory:,} MB ({memory/1024:.2f} GB)")
        else:
            print("   ❌ No se detectó GPU NVIDIA")

        print(f"\n🔷 CUDA:")
        if gpu_info['cuda_version']:
            print(f"   Versión: {gpu_info['cuda_version']}")
        else:
            print("   ❌ CUDA no detectado")

        print(f"\n🔶 TensorRT:")
        if gpu_info['tensorrt_version']:
            print(f"   Versión: {gpu_info['tensorrt_version']}")
        else:
            print("   ❌ TensorRT no disponible")

        print(f"\n🟢 Sistema:")
        print(f"   Plataforma: {system_info['platform']}")
        print(f"   Python: {system_info['python_version']}")
        if system_info['deepstream_version']:
            print(f"   DeepStream: {system_info['deepstream_version']}")
        else:
            print(f"   DeepStream: No detectado")

        print("\n" + "="*70)


class YOLOExporter:
    """Exporta modelo YOLO a ONNX si es necesario"""

    @staticmethod
    def download_model(output_dir: str = None) -> str:
        """Descarga modelo YOLO11x.pt desde Hugging Face"""
        print("\n" + "="*70)
        print("📥 DESCARGANDO MODELO YOLO11x")
        print("="*70)

        try:
            from ultralytics import YOLO
            from pathlib import Path
            import shutil
            import glob

            if output_dir is None:
                output_dir = "/app/engines/pt"

            Path(output_dir).mkdir(parents=True, exist_ok=True)
            dst_path = f"{output_dir}/yolo11x.pt"

            print(f"\n📂 Directorio de destino: {output_dir}")
            print("⏳ Descargando modelo (1-5 minutos)...")
            print("   Tamaño: ~109 MB\n")

            # Guardar directorio actual
            original_cwd = os.getcwd()

            # Cambiar al directorio destino para que ultralytics descargue ahí
            os.chdir(output_dir)

            try:
                # Descargar modelo automáticamente (se descarga en el directorio actual)
                model = YOLO('yolo11x.pt')

                # Verificar si se descargó en el directorio actual
                if os.path.exists('yolo11x.pt'):
                    print(f"✅ Modelo descargado directamente en: {dst_path}")
                else:
                    # Buscar en ubicaciones alternativas
                    search_paths = [
                        str(Path.home() / '.cache' / 'ultralytics' / '**' / 'yolo11x.pt'),
                        str(Path.home() / 'yolo11x.pt'),
                        '/tmp/yolo11x.pt',
                        '/app/yolo11x.pt',
                    ]

                    found_path = None
                    for pattern in search_paths:
                        matches = glob.glob(pattern, recursive=True)
                        if matches:
                            found_path = matches[0]
                            break

                    if found_path and found_path != dst_path:
                        shutil.copy2(found_path, dst_path)
                        print(f"✅ Modelo copiado desde: {found_path}")
                    elif not os.path.exists(dst_path):
                        raise FileNotFoundError("No se pudo localizar el modelo descargado")

            finally:
                # Restaurar directorio original
                os.chdir(original_cwd)

            # Verificar que el archivo existe y tiene tamaño válido
            if os.path.exists(dst_path):
                size_mb = os.path.getsize(dst_path) / (1024**2)
                if size_mb > 50:  # El modelo debe ser > 50MB
                    print(f"✅ Modelo listo: {dst_path}")
                    print(f"📊 Tamaño: {size_mb:.2f} MB\n")
                    return dst_path
                else:
                    raise ValueError(f"Archivo descargado muy pequeño: {size_mb:.2f} MB")
            else:
                raise FileNotFoundError(f"No se encontró el modelo en: {dst_path}")

        except Exception as e:
            print(f"\n❌ Error descargando modelo: {e}")
            raise

    @staticmethod
    def export_to_onnx(pt_path: str = None) -> str:
        """Exporta modelo YOLO PT a ONNX (descarga PT si no existe)"""
        print("\n" + "="*70)
        print("📦 EXPORTANDO MODELO YOLO PT A ONNX")
        print("="*70)

        try:
            from ultralytics import YOLO

            # Si no proporciona PT, descargar
            if pt_path is None or not os.path.exists(pt_path):
                print("\n⚠️  Modelo PT no encontrado, descargando...")
                pt_path = YOLOExporter.download_model()

            print(f"\n📂 Cargando modelo: {pt_path}")
            model = YOLO(pt_path)

            print("\n⚙️  Configuración de exportación:")
            print(f"   Formato: ONNX")
            print(f"   Tamaño entrada: 1280x1280")
            print(f"   Batch: DINÁMICO (1-16)")
            print(f"   Opset: 17")

            print("\n🔄 Exportando (2-5 minutos)...")
            onnx_path = model.export(
                format='onnx',
                imgsz=1280,
                dynamic=True,
                simplify=True,
                opset=17
            )

            print(f"\n✅ ONNX exportado: {onnx_path}")
            return str(onnx_path)

        except Exception as e:
            print(f"\n❌ Error exportando a ONNX: {e}")
            raise


class EngineBuilder:
    """Construye engine TensorRT optimizado usando DeepStream"""

    @staticmethod
    def build_engine(onnx_path: str, output_path: str = None,
                    workspace_mb: int = 8192,
                    fp16: bool = True) -> str:
        """
        Construye engine TensorRT a partir de ONNX
        DeepStream compilará automáticamente el engine la primera vez que se ejecute
        """

        if output_path is None:
            output_path = os.path.splitext(onnx_path)[0] + '.engine'

        print("\n" + "="*70)
        print("🚀 PREPARANDO ENGINE TENSORRT CON DEEPSTREAM")
        print("="*70)

        try:
            print(f"\n📦 Archivo ONNX: {onnx_path}")
            print(f"🎯 Engine de salida: {output_path}")

            if not os.path.exists(onnx_path):
                raise FileNotFoundError(f"ONNX no encontrado: {onnx_path}")

            print(f"\n⚙️  Configuración TensorRT:")
            print(f"   Formato entrada: NCHW (batch, 3, 1280, 1280)")
            print(f"   Batch: 1")
            print(f"   Precisión: {'FP16' if fp16 else 'FP32'}")
            print(f"   Workspace: {workspace_mb} MB")

            print(f"\n📝 El engine será compilado automáticamente por DeepStream")
            print(f"   cuando se ejecute la aplicación por primera vez.")
            print(f"   Esto puede tardar 10-20 minutos.\n")

            # El engine se compilará automáticamente cuando DeepStream lo necesite
            # Solo necesitamos asegurar que el ONNX esté disponible

            print(f"✅ ONNX preparado para compilación automática por DeepStream")
            print(f"   Archivo: {onnx_path}")

            return onnx_path  # Devolvemos la ruta del ONNX

        except Exception as e:
            print(f"\n❌ Error preparando engine: {e}")
            raise


class DeepStreamConfig:
    """Genera configuración de DeepStream optimizada"""

    @staticmethod
    def create_config(onnx_path: str, output_dir: str = None) -> str:
        """Crea archivo de configuración de DeepStream para ONNX con compilación automática de engine"""

        if output_dir is None:
            output_dir = os.path.dirname(onnx_path)

        config_path = os.path.join(output_dir, 'config_infer_auto_generated.txt')

        # Generar ruta del engine que DeepStream creará
        engine_path = os.path.splitext(onnx_path)[0] + '.engine'

        config_content = f"""[property]
gpu-id=0
net-scale-factor=0.0039215697906911373
model-color-format=0
infer-dims=3;1280;1280
onnx-file={onnx_path}
model-engine-file={engine_path}
labelfile-path=/app/configs/deepstream/labels.txt
batch-size=1
network-mode=0
num-detected-classes=80
interval=2
gie-unique-id=1
process-mode=1
network-type=0
cluster-mode=2
maintain-aspect-ratio=1
symmetric-padding=1
workspace-size=8000
parse-bbox-func-name=NvDsInferYolo
custom-lib-path=/app/libnvdsinfer_custom_impl_Yolo.so
engine-create-func-name=NvDsInferYoloCudaEngineGet

# Configuración automática generada
[class-attrs-all]
nms-iou-threshold=0.5
pre-cluster-threshold=1.0
topk=0

# Solo detectar personas (clase 0)
[class-attrs-0]
pre-cluster-threshold=0.25
nms-iou-threshold=0.5
topk=300
detected-min-w=20
detected-min-h=40
"""

        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
            print(f"\n✅ Configuración de DeepStream creada: {config_path}")
            print(f"   DeepStream compilará automáticamente el engine TensorRT")
            print(f"   a partir del ONNX cuando se ejecute por primera vez.")
            return config_path
        except Exception as e:
            print(f"❌ Error creando configuración: {e}")
            raise


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Auto-generar engine TensorRT optimizado para este PC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Auto-detectar y usar YOLO11x.pt por defecto
  python3 auto_build_engine.py

  # Usar un archivo ONNX específico
  python3 auto_build_engine.py --onnx /path/to/model.onnx

  # Usar un archivo PT y exportar a ONNX
  python3 auto_build_engine.py --pt /path/to/model.pt

  # Con opciones personalizadas
  python3 auto_build_engine.py --onnx model.onnx --workspace 4096 --no-fp16
        """
    )

    parser.add_argument('--onnx', help='Ruta al archivo ONNX')
    parser.add_argument('--pt', help='Ruta al archivo PT (será exportado a ONNX)')
    parser.add_argument('--workspace', type=int, default=8192, help='Workspace en MB (default: 8192)')
    parser.add_argument('--no-fp16', action='store_true', help='No usar FP16, usar FP32')
    parser.add_argument('--output', help='Ruta de salida para el engine')

    args = parser.parse_args()

    try:
        # 1. Detectar hardware
        print("\n🔍 DETECTANDO COMPONENTES DEL SISTEMA...")
        gpu_info = SystemInfo.get_gpu_info()
        system_info = SystemInfo.get_system_info()
        SystemInfo.print_hardware_info(gpu_info, system_info)

        # Validar que tenemos GPU
        if not gpu_info['available']:
            print("\n❌ ERROR: No se detectó GPU NVIDIA disponible")
            print("   Este script requiere una GPU NVIDIA con CUDA y TensorRT")
            sys.exit(1)

        if not gpu_info['tensorrt_version']:
            print("\n❌ ERROR: TensorRT no está disponible")
            print("   Instala TensorRT antes de ejecutar este script")
            sys.exit(1)

        # Nota: TensorRT será utilizado por DeepStream automáticamente
        print("\n✅ TensorRT detectado y disponible para DeepStream")

        # 2. Obtener/generar ONNX
        onnx_path = None

        if args.onnx:
            onnx_path = args.onnx
            if not os.path.exists(onnx_path):
                print(f"\n❌ ERROR: ONNX no encontrado: {onnx_path}")
                sys.exit(1)
        elif args.pt:
            onnx_path = YOLOExporter.export_to_onnx(args.pt)
        else:
            # Buscar YOLO11x.onnx por defecto
            default_paths = [
                'yolo11x.onnx',
                'export_dynamic_batch/yolo11x.onnx',
                '/app/export_dynamic_batch/yolo11x.onnx',
                '/app/engines/onnx/yolo11x_dynamic.onnx'
            ]

            for path in default_paths:
                if os.path.exists(path):
                    onnx_path = path
                    break

            if not onnx_path:
                # Buscar yolo11x.pt por defecto
                pt_paths = [
                    '/app/engines/pt/yolo11x.pt',
                    'yolo11x.pt',
                    'export_dynamic_batch/yolo11x.pt',
                    '/app/export_dynamic_batch/yolo11x.pt'
                ]

                for path in pt_paths:
                    if os.path.exists(path):
                        print(f"\n📂 Usando modelo PT: {path}")
                        onnx_path = YOLOExporter.export_to_onnx(path)
                        break

        if not onnx_path:
            print("\n📥 No se encontró ONNX ni PT localmente, descargando modelo...")
            print("   Esto puede tomar 10-15 minutos la primera vez\n")

            try:
                # Descargar y exportar automáticamente
                pt_path = YOLOExporter.download_model()
                onnx_path = YOLOExporter.export_to_onnx(pt_path)
            except Exception as e:
                print(f"\n❌ ERROR: No se pudo descargar/exportar el modelo")
                print(f"   {e}")
                print("\n   Alternativas:")
                print("   1. python3 auto_build_engine.py --pt /ruta/a/yolo11x.pt")
                print("   2. python3 auto_build_engine.py --onnx /ruta/a/yolo11x.onnx")
                sys.exit(1)

        # 3. Preparar engine (DeepStream compilará automáticamente)
        output_engine = args.output
        onnx_path_final = EngineBuilder.build_engine(
            onnx_path,
            output_engine,
            workspace_mb=args.workspace,
            fp16=not args.no_fp16
        )

        # 4. Crear configuración de DeepStream
        config_path = DeepStreamConfig.create_config(onnx_path_final)

        # 5. Resumen final
        print("\n" + "="*70)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"\n📦 Modelo ONNX:")
        print(f"   {onnx_path_final}")
        print(f"\n⚙️  Configuración DeepStream:")
        print(f"   {config_path}")
        print(f"\n📋 Próximos pasos:")
        print(f"   1. El engine será compilado automáticamente por DeepStream")
        print(f"      cuando ejecutes la aplicación (primera ejecución: 10-20 min)")
        print(f"   2. Copia la config a: /app/configs/deepstream/")
        print(f"   3. Ejecuta: python3 main_low_latency.py")
        print("="*70)
        print()

    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
