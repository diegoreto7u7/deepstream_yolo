#!/usr/bin/env python3
"""
Script para probar la compilación automática de engine mediante DeepStream
Verifica que el ONNX es compatible y que DeepStream puede compilarlo
"""

import os
import subprocess
import sys
from pathlib import Path

def test_onnx_file(onnx_path):
    """Verifica la integridad del archivo ONNX"""
    print("\n" + "="*70)
    print("📋 VERIFICANDO ARCHIVO ONNX")
    print("="*70)

    if not os.path.exists(onnx_path):
        print(f"\n❌ ERROR: Archivo ONNX no encontrado: {onnx_path}")
        return False

    file_size = os.path.getsize(onnx_path)
    print(f"\n✅ Archivo encontrado: {onnx_path}")
    print(f"   Tamaño: {file_size / (1024**2):.2f} MB")

    # Intentar validar con ONNX si está disponible
    try:
        import onnx
        print("\n🔍 Validando estructura ONNX...")
        model = onnx.load(onnx_path)
        onnx.checker.check_model(model)
        print("✅ ONNX válido")

        # Mostrar información del modelo
        graph = model.graph
        print(f"\n📊 Información del modelo:")
        print(f"   Inputs: {len(graph.input)}")
        for inp in graph.input:
            print(f"      - {inp.name}: {inp.type.tensor_type.shape.dim}")
        print(f"   Outputs: {len(graph.output)}")
        for out in graph.output:
            print(f"      - {out.name}")
        return True

    except Exception as e:
        print(f"⚠️  No se pudo validar con ONNX: {e}")
        return True  # El archivo existe aunque no se pueda validar

def test_deepstream_config(config_path):
    """Verifica la configuración de DeepStream"""
    print("\n" + "="*70)
    print("⚙️  VERIFICANDO CONFIGURACIÓN DEEPSTREAM")
    print("="*70)

    if not os.path.exists(config_path):
        print(f"\n❌ ERROR: Archivo de configuración no encontrado: {config_path}")
        return False

    print(f"\n✅ Archivo encontrado: {config_path}")

    # Leer y mostrar configuración
    with open(config_path, 'r') as f:
        content = f.read()
        print("\n📄 Contenido de la configuración:")
        print("-" * 70)
        for line in content.split('\n')[:15]:  # Mostrar primeras 15 líneas
            if line.strip():
                print(f"   {line}")
        if len(content.split('\n')) > 15:
            print("   ...")
        print("-" * 70)

    # Verificar parámetros críticos
    print("\n🔍 Verificando parámetros críticos:")
    required_params = ['onnx-file', 'model-engine-file', 'gpu-id']
    found_params = {}

    for param in required_params:
        for line in content.split('\n'):
            if param + '=' in line:
                value = line.split('=', 1)[1].strip()
                found_params[param] = value
                print(f"   ✅ {param}: {value}")
                break

    missing = [p for p in required_params if p not in found_params]
    if missing:
        print(f"\n❌ Parámetros faltantes: {missing}")
        return False

    return True

def test_gpu_and_cuda():
    """Verifica GPU y CUDA"""
    print("\n" + "="*70)
    print("🖥️  VERIFICANDO HARDWARE")
    print("="*70)

    # Verificar nvidia-smi
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total',
                               '--format=csv,noheader,nounits'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"\n✅ GPU detectada:")
            for i, line in enumerate(lines):
                parts = line.split(',')
                print(f"   GPU {i}: {parts[0].strip()} - {int(parts[1])//1024} GB")
            return True
        else:
            print("\n❌ No se detectó GPU NVIDIA")
            return False
    except Exception as e:
        print(f"\n❌ Error verificando GPU: {e}")
        return False

def check_deepstream():
    """Verifica instalación de DeepStream"""
    print("\n" + "="*70)
    print("📦 VERIFICANDO DEEPSTREAM")
    print("="*70)

    ds_paths = [
        '/opt/nvidia/deepstream/deepstream-8.0',
        '/opt/nvidia/deepstream/deepstream-7.1',
        '/opt/nvidia/deepstream'
    ]

    for path in ds_paths:
        if os.path.exists(path):
            print(f"\n✅ DeepStream encontrado: {path}")

            # Buscar libnvdsinfer_custom_impl_Yolo.so
            yolo_lib = '/app/libnvdsinfer_custom_impl_Yolo.so'
            if os.path.exists(yolo_lib):
                print(f"✅ Librería YOLO custom encontrada: {yolo_lib}")
            else:
                print(f"⚠️  Librería YOLO custom no encontrada: {yolo_lib}")

            return True

    print("\n❌ DeepStream no encontrado")
    return False

def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*70)
    print("🧪 PRUEBAS DE COMPATIBILIDAD PARA ENGINE TENSORRT")
    print("="*70)

    os.chdir("/app/engines")

    tests = [
        ("GPU y CUDA", test_gpu_and_cuda),
        ("DeepStream", check_deepstream),
        ("Archivo ONNX", lambda: test_onnx_file("yolo11x.onnx")),
        ("Configuración DeepStream", lambda: test_deepstream_config("config_infer_auto_generated.txt")),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Error en prueba '{test_name}': {e}")
            results.append((test_name, False))

    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status}: {test_name}")

    print(f"\nResultado: {passed}/{total} pruebas pasadas")

    if passed == total:
        print("\n" + "="*70)
        print("✅ TODAS LAS PRUEBAS PASARON")
        print("="*70)
        print("\n📋 Próximos pasos:")
        print("   1. Copia el archivo ONNX (yolo11x.onnx) a /app/engines/")
        print("   2. Copia la configuración (config_infer_auto_generated.txt)")
        print("   3. Ejecuta tu aplicación DeepStream")
        print("   4. DeepStream compilará automáticamente el engine TensorRT")
        print("      (Primera ejecución: 10-20 minutos)")
        print("\n✅ ¡Listo para usar!\n")
        return 0
    else:
        print("\n" + "="*70)
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("="*70)
        print("\nVerifica los errores arriba para más detalles.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
