#!/usr/bin/env python3
"""
Sistema multi-camara de deteccion y conteo de personas con DeepStream
VERSION: PYDS (bindings tradicionales estables)

Usa pyds en lugar de pyservicemaker para evitar problemas de GIL con Python 3.12.
"""
import sys
from modules.api_client import CameraAPIClient
from modules.rtsp_builder import RTSPBuilder
from modules.camera_config import CameraConfig
from modules.deepstream_multi_camera_pyds import DeepStreamMultiCameraPipeline


def main():
    """Funcion principal"""

    API_URL = "http://172.80.20.22/api"
    HEADLESS = False

    print("=" * 70)
    print("SISTEMA MULTI-CAMARA DE CONTEO DE PERSONAS")
    print("VERSION: PYDS (Python bindings tradicionales)")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print(f"Modo: {'HEADLESS' if HEADLESS else 'CON DISPLAY'}")
    print("=" * 70)
    print()

    try:
        # 1. Conectar a la API
        print("Conectando a la API...")
        api_client = CameraAPIClient(API_URL)

        # 2. Obtener camaras
        print("Obteniendo camaras desde la API...")
        cameras_data = api_client.get_cameras()

        if not cameras_data:
            print("ERROR: No se encontraron camaras en la API")
            return 1

        print(f"Se encontraron {len(cameras_data)} camaras")
        print()

        # 3. Crear pipeline
        pipeline = DeepStreamMultiCameraPipeline(headless=HEADLESS)
        config_manager = CameraConfig()

        # 4. Agregar camaras
        print("Configurando camaras...")
        print("=" * 70)

        cameras_added = 0
        for idx, camera_data in enumerate(cameras_data):
            camera_id = camera_data['id']
            camera_name = camera_data['cam_nombre']
            camera_ip = camera_data['cam_ip']

            print(f"\n[{idx + 1}/{len(cameras_data)}] Configurando camara ID {camera_id}:")
            print(f"   Nombre: {camera_name}")
            print(f"   IP: {camera_ip}")

            rtsp_uri = RTSPBuilder.build_rtsp_uri(camera_data)
            if not RTSPBuilder.validate_rtsp_uri(rtsp_uri):
                print(f"   URI RTSP invalida, omitiendo...")
                continue

            line_config = config_manager.get_line_config(
                camera_id,
                camera_data['cam_coordenadas']
            )

            print(f"   Linea: {line_config['start']} -> {line_config['end']}")
            print(f"   Direccion: {line_config['direccion_entrada']}")

            source_id = pipeline.add_camera(
                camera_id=camera_id,
                camera_name=camera_name,
                rtsp_uri=rtsp_uri,
                line_config=line_config
            )
            cameras_added += 1
            print(f"   Agregada como source {source_id}")

        print("\n" + "=" * 70)
        print(f"{cameras_added}/{len(cameras_data)} camaras configuradas")
        print("=" * 70)

        if cameras_added == 0:
            print("ERROR: No se agrego ninguna camara")
            return 1

        # 5. Construir pipeline
        print("\nConstruyendo pipeline...")
        pipeline.build()

        # 6. Ejecutar
        print("\nPresiona Ctrl+C para detener...\n")
        pipeline.run()

        # 7. Estadisticas finales
        print("\n" + "=" * 70)
        print("ESTADISTICAS FINALES")
        print("=" * 70)
        stats = pipeline.get_stats()
        for camera_id, camera_stats in stats.items():
            print(f"Camara {camera_id}:")
            print(f"  Entradas: {camera_stats['entradas']}")
            print(f"  Salidas: {camera_stats['salidas']}")
            print(f"  Dentro: {camera_stats['dentro']}")
        print("=" * 70)

        return 0

    except KeyboardInterrupt:
        print("\nInterrupcion por teclado")
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
