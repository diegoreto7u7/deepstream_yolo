#!/usr/bin/env python3
"""
Script para compilar un engine TensorRT de prueba desde ONNX
Esto sirve para verificar que TensorRT funciona correctamente
"""

import os
import sys
import tensorrt as trt

def build_trt_engine(onnx_path, engine_path, workspace_mb=8192, fp16=True):
    """Construye un engine TensorRT a partir de un archivo ONNX"""

    print("\n" + "="*70)
    print("🚀 COMPILANDO ENGINE TENSORRT DE PRUEBA")
    print("="*70)

    if not os.path.exists(onnx_path):
        print(f"\n❌ ERROR: Archivo ONNX no encontrado: {onnx_path}")
        return False

    try:
        print(f"\n📦 Archivo ONNX: {onnx_path}")
        print(f"   Tamaño: {os.path.getsize(onnx_path) / (1024**2):.2f} MB")
        print(f"🎯 Archivo de salida: {engine_path}")

        # Crear logger de TensorRT
        logger = trt.Logger(trt.Logger.WARNING)
        builder = trt.Builder(logger)

        print(f"\n⚙️  Configuración:")
        print(f"   Workspace: {workspace_mb} MB")
        print(f"   Precisión: {'FP16' if fp16 else 'FP32'}")
        print(f"   Batch: 1 (dinámico)")

        # Crear network desde ONNX
        network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
        parser = trt.OnnxParser(network, logger)

        print(f"\n📖 Parseando ONNX...")
        with open(onnx_path, 'rb') as f:
            success = parser.parse(f.read())
            if not success:
                print("❌ Error parseando ONNX:")
                for i in range(parser.num_errors):
                    print(f"   Error {i}: {parser.get_error(i)}")
                return False

        print("✅ ONNX parseado correctamente")

        # Configurar builder
        config = builder.create_builder_config()
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace_mb * (1 << 20))

        # Habilitar FP16
        if fp16 and builder.platform_has_fast_fp16:
            config.set_flag(trt.BuilderFlag.FP16)
            print("✅ FP16 habilitado")
        else:
            if fp16:
                print("⚠️  FP16 no disponible en esta plataforma, usando FP32")

        # Configurar perfil de optimización dinámico
        profile = builder.create_optimization_profile()
        input_name = network.get_input(0).name

        min_shape = (1, 3, 1280, 1280)
        opt_shape = (1, 3, 1280, 1280)
        max_shape = (1, 3, 1280, 1280)

        profile.set_shape(input_name, min_shape, opt_shape, max_shape)
        config.add_optimization_profile(profile)

        print(f"\n⚙️  Perfil de optimización:")
        print(f"   Entrada: {input_name}")
        print(f"   Shape: {min_shape}")

        # Construir engine
        print(f"\n⏳ Compilando engine TensorRT...")
        print(f"   Esto puede tomar 5-15 minutos...")

        serialized_engine = builder.build_serialized_network(network, config)

        if serialized_engine is None:
            print("❌ Error: Fallo la construcción del engine")
            return False

        # Guardar engine
        print(f"\n💾 Guardando engine...")
        with open(engine_path, 'wb') as f:
            f.write(serialized_engine)

        if os.path.exists(engine_path):
            size_mb = os.path.getsize(engine_path) / (1024 * 1024)
            print(f"\n✅ ENGINE TENSORRT COMPILADO EXITOSAMENTE")
            print(f"   Archivo: {engine_path}")
            print(f"   Tamaño: {size_mb:.2f} MB")
            return True
        else:
            print("❌ Error: No se generó el archivo del engine")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    onnx_file = "yolo11x.onnx"
    engine_file = "yolo11x_test.engine"

    # Cambiar a directorio de engines
    os.chdir("/app/engines")

    success = build_trt_engine(onnx_file, engine_file)

    if success:
        print("\n" + "="*70)
        print("✅ PRUEBA EXITOSA")
        print("="*70)
        print(f"\nEl engine fue compilado correctamente.")
        print(f"Puedes usar este engine en DeepStream.")
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("❌ PRUEBA FALLIDA")
        print("="*70)
        sys.exit(1)
