#!/usr/bin/env python3
"""
Sistema multi-cámara de detección y conteo de personas con DeepStream
Conecta a API REST para obtener configuración de múltiples cámaras RTSP
Ejecuta múltiples cámaras en paralelo usando threading
"""
import sys
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Importar módulos
from modules.api_client import CameraAPIClient
from modules.rtsp_builder import RTSPBuilder
from modules.camera_config import CameraConfig
from modules.multi_camera_manager import MultiCameraManager


def main():
    """Función principal para sistema multi-cámara"""

    # Configuración de la API
    API_URL = "http://172.80.20.22/api"

    print("=" * 70)
    print("🎥 SISTEMA MULTI-CÁMARA DE CONTEO DE PERSONAS")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print("=" * 70)
    print()

    # Inicializar GStreamer (UNA VEZ en thread principal)
    Gst.init(None)

    try:
        # 1. Conectar a la API
        print("🔌 Conectando a la API...")
        api_client = CameraAPIClient(API_URL)

        # 2. Obtener TODAS las cámaras
        print("📡 Obteniendo cámaras desde la API...")
        cameras_data = api_client.get_cameras()

        if not cameras_data:
            print("❌ ERROR: No se encontraron cámaras en la API")
            return 1

        print(f"✅ Se encontraron {len(cameras_data)} cámaras")
        print()

        # 3. Crear gestor de múltiples cámaras
        manager = MultiCameraManager(max_cameras=16)
        config_manager = CameraConfig()

        # 4. Agregar TODAS las cámaras
        print("📋 Configurando cámaras...")
        print("=" * 70)
        print(f"🎥 PROCESANDO TODAS LAS CÁMARAS ({len(cameras_data)} cámaras)")
        print("=" * 70)

        # Procesar cada cámara
        cameras_added = 0
        for idx, camera_data in enumerate(cameras_data, 1):
            camera_id = camera_data['id']
            camera_name = camera_data['cam_nombre']
            camera_ip = camera_data['cam_ip']

            print(f"\n[{idx}/{len(cameras_data)}] 📹 Configurando cámara ID {camera_id}:")
            print(f"   Nombre: {camera_name}")
            print(f"   IP: {camera_ip}")

            # Construir URI RTSP
            rtsp_uri = RTSPBuilder.build_rtsp_uri(camera_data)

            if not RTSPBuilder.validate_rtsp_uri(rtsp_uri):
                print(f"   ❌ URI RTSP inválida, omitiendo...")
                continue

            # Obtener configuración de línea
            line_config = config_manager.get_line_config(
                camera_id,
                camera_data['cam_coordenadas']
            )

            print(f"   Línea: {line_config['start']} -> {line_config['end']}")
            print(f"   Dirección: {line_config['direccion_entrada']}")

            # Guardar metadata
            metadata = config_manager.get_camera_metadata(camera_data)
            config_manager.save_camera_metadata(camera_id, metadata)

            # Agregar al gestor
            if manager.add_camera(
                camera_id=camera_id,
                camera_name=camera_name,
                rtsp_uri=rtsp_uri,
                line_config=line_config
            ):
                cameras_added += 1
                print(f"   ✅ Cámara {camera_id} agregada")
            else:
                print(f"   ❌ Error agregando cámara {camera_id}")

        print("\n" + "=" * 70)
        print(f"✅ {cameras_added}/{len(cameras_data)} cámaras configuradas exitosamente")
        print("=" * 70)
        print()

        if cameras_added == 0:
            print("❌ ERROR: No se agregó ninguna cámara")
            return 1

        # 5. Iniciar todas las cámaras
        # sequential=True: Inicia una por una (más seguro, debugging fácil)
        # sequential=False: Inicia en paralelo (más rápido, mayor carga inicial)
        manager.start_all_cameras(sequential=True)

        # 6. Esperar interrupción de teclado (Ctrl+C)
        manager.wait_keyboard_interrupt()

        # 7. Mostrar estadísticas finales
        manager.print_summary()

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Interrupción por teclado")
        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
