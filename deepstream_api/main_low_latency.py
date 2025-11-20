#!/usr/bin/env python3
"""
Sistema multi-cámara de detección y conteo de personas con DeepStream
VERSIÓN LOW LATENCY - Optimizada para baja latencia de video
Conecta a API REST para obtener configuración de múltiples cámaras RTSP
Ejecuta múltiples cámaras en paralelo usando threading

OPTIMIZACIONES APLICADAS:
- Tracker IOU (más ligero que NvDCF)
- Menos overhead en OSD
- Parámetros optimizados para latencia
"""
import sys
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Importar módulos
from modules.api_client import CameraAPIClient
from modules.rtsp_builder import RTSPBuilder
from modules.camera_config import CameraConfig
from modules.threaded_camera_low_latency import ThreadedDeepStreamCameraLowLatency
from typing import Dict
import threading


class MultiCameraManagerLowLatency:
    """
    Gestor de múltiples cámaras con threading OPTIMIZADO PARA BAJA LATENCIA
    """

    def __init__(self, max_cameras: int = 16, headless: bool = False):
        """
        Inicializa gestor de múltiples cámaras (versión baja latencia)

        Args:
            max_cameras: Número máximo de cámaras simultáneas
            headless: Si True, no muestra ventanas (solo terminal)
        """
        self.cameras: Dict[int, ThreadedDeepStreamCameraLowLatency] = {}
        self.max_cameras = max_cameras
        self.headless = headless
        self.shutdown_event = threading.Event()
        self._cameras_lock = threading.Lock()

    def add_camera(self, camera_id: int, camera_name: str,
                   rtsp_uri: str, line_config: dict) -> bool:
        """Agrega cámara al gestor"""
        with self._cameras_lock:
            if len(self.cameras) >= self.max_cameras:
                print(f"❌ Máximo de cámaras ({self.max_cameras}) alcanzado")
                return False

            if camera_id in self.cameras:
                print(f"❌ Cámara {camera_id} ya existe")
                return False

            camera = ThreadedDeepStreamCameraLowLatency(
                camera_id=camera_id,
                camera_name=camera_name,
                rtsp_uri=rtsp_uri,
                line_config=line_config,
                headless=self.headless
            )

            self.cameras[camera_id] = camera
            print(f"✅ Cámara {camera_id} ({camera_name}) agregada al gestor [LOW LATENCY]")
            return True

    def start_camera(self, camera_id: int) -> bool:
        """Inicia una cámara específica"""
        with self._cameras_lock:
            camera = self.cameras.get(camera_id)

        if not camera:
            print(f"❌ Cámara {camera_id} no encontrada")
            return False

        return camera.start()

    def start_all_cameras(self, sequential: bool = False):
        """Inicia todas las cámaras"""
        with self._cameras_lock:
            camera_list = list(self.cameras.values())

        if not camera_list:
            print("⚠️  No hay cámaras para iniciar")
            return

        print(f"\n{'='*70}")
        print(f"🚀 INICIANDO {len(camera_list)} CÁMARAS [LOW LATENCY MODE] "
              f"({'SECUENCIAL' if sequential else 'PARALELO'})")
        print(f"{'='*70}\n")

        if sequential:
            success_count = 0
            for i, camera in enumerate(camera_list, 1):
                print(f"[{i}/{len(camera_list)}] Iniciando cámara {camera.camera_id}...")
                if camera.start():
                    success_count += 1
                    print(f"✅ Cámara {camera.camera_id} iniciada [LOW LATENCY]")
                else:
                    print(f"❌ Fallo al iniciar cámara {camera.camera_id}")

            print(f"\n{'='*70}")
            print(f"✅ {success_count}/{len(camera_list)} cámaras iniciadas exitosamente")
            print(f"{'='*70}\n")

    def stop_all_cameras(self):
        """Detiene todas las cámaras gracefully"""
        print(f"\n{'='*70}")
        print("🛑 DETENIENDO TODAS LAS CÁMARAS...")
        print(f"{'='*70}\n")

        self.shutdown_event.set()

        with self._cameras_lock:
            camera_list = list(self.cameras.values())

        for camera in camera_list:
            camera.stop()

        print(f"\n{'='*70}")
        print("✅ TODAS LAS CÁMARAS DETENIDAS")
        print(f"{'='*70}\n")

    def wait_keyboard_interrupt(self):
        """Espera Ctrl+C y maneja apagado gracefully"""
        try:
            running = [c.camera_id for c in self.cameras.values() if c.is_alive()]
            print(f"\n✅ {len(running)} cámaras corriendo [LOW LATENCY]: {running}")
            print("Presiona Ctrl+C para detener todas las cámaras...\n")
            self.shutdown_event.wait()
        except KeyboardInterrupt:
            print("\n⚠️  Interrupción de teclado detectada")
        finally:
            self.stop_all_cameras()

    def print_summary(self):
        """Imprime resumen de todas las cámaras y sus estadísticas"""
        print(f"\n{'='*70}")
        print("📊 RESUMEN DE CÁMARAS [LOW LATENCY MODE]")
        print(f"{'='*70}")

        with self._cameras_lock:
            total = len(self.cameras)
            running = sum(1 for cam in self.cameras.values() if cam.is_alive())

        print(f"Total de cámaras: {total}")
        print(f"Cámaras corriendo: {running}")
        print(f"Cámaras detenidas: {total - running}")
        print(f"{'='*70}")

        for camera_id, camera in self.cameras.items():
            stats = camera.get_stats()
            fps = camera.get_fps()
            status = "🟢 ACTIVA" if camera.is_alive() else "🔴 DETENIDA"

            print(f"\nCámara {camera_id} - {status} [LOW LATENCY]")
            print(f"  FPS: {fps:.1f}")
            print(f"  Entradas: {stats['entradas']}")
            print(f"  Salidas: {stats['salidas']}")
            print(f"  Dentro: {stats['dentro']}")

        print(f"{'='*70}\n")


def main():
    """Función principal para sistema multi-cámara LOW LATENCY"""

    # Configuración de la API
    API_URL = "http://172.80.20.22/api"

    print("=" * 70)
    print("🎥 SISTEMA MULTI-CÁMARA DE CONTEO DE PERSONAS [LOW LATENCY]")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print("Optimizaciones: Tracker IOU, Baja latencia de display")
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

        # 3. Crear gestor de múltiples cámaras LOW LATENCY
        manager = MultiCameraManagerLowLatency(max_cameras=16, headless=False)
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
                print(f"   ✅ Cámara {camera_id} agregada [LOW LATENCY]")
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
