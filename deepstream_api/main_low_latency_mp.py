#!/usr/bin/env python3
"""
Sistema multi-cámara de detección y conteo de personas con DeepStream
VERSION LOW LATENCY CON MULTIPROCESSING

Usa multiprocessing en lugar de threading para evitar problemas de GIL
con Python 3.12 y GStreamer/GLib.

NOTA: Cada cámara corre en su propio proceso, inicializando GStreamer
independientemente para evitar conflictos de thread state.
"""
import sys
import os
import signal

# NO inicializar GStreamer aquí - cada proceso hijo lo hará
# Importar módulos
from modules.api_client import CameraAPIClient
from modules.rtsp_builder import RTSPBuilder
from modules.camera_config import CameraConfig
from modules.multiprocess_camera_low_latency import MultiprocessDeepStreamCameraLowLatency
from typing import Dict
import multiprocessing as mp


class MultiCameraManagerLowLatencyMP:
    """
    Gestor de múltiples cámaras con MULTIPROCESSING
    Optimizado para baja latencia y compatible con Python 3.12
    """

    def __init__(self, max_cameras: int = 16, headless: bool = False):
        """
        Inicializa gestor de múltiples cámaras (versión multiprocessing)

        Args:
            max_cameras: Número máximo de cámaras simultáneas
            headless: Si True, no muestra ventanas (solo terminal)
        """
        self.cameras: Dict[int, MultiprocessDeepStreamCameraLowLatency] = {}
        self.max_cameras = max_cameras
        self.headless = headless
        self._shutdown = False

    def add_camera(self, camera_id: int, camera_name: str,
                   rtsp_uri: str, line_config: dict) -> bool:
        """Agrega cámara al gestor"""
        if len(self.cameras) >= self.max_cameras:
            print(f"Máximo de cámaras ({self.max_cameras}) alcanzado")
            return False

        if camera_id in self.cameras:
            print(f"Cámara {camera_id} ya existe")
            return False

        camera = MultiprocessDeepStreamCameraLowLatency(
            camera_id=camera_id,
            camera_name=camera_name,
            rtsp_uri=rtsp_uri,
            line_config=line_config,
            headless=self.headless
        )

        self.cameras[camera_id] = camera
        print(f"Cámara {camera_id} ({camera_name}) agregada [MULTIPROCESS LOW LATENCY]")
        return True

    def start_camera(self, camera_id: int) -> bool:
        """Inicia una cámara específica"""
        camera = self.cameras.get(camera_id)
        if not camera:
            print(f"Cámara {camera_id} no encontrada")
            return False
        return camera.start()

    def start_all_cameras(self, sequential: bool = True):
        """
        Inicia todas las cámaras

        Args:
            sequential: Si True, inicia una por una (recomendado para multiprocessing)
        """
        camera_list = list(self.cameras.values())

        if not camera_list:
            print("No hay cámaras para iniciar")
            return

        print(f"\n{'='*70}")
        print(f"INICIANDO {len(camera_list)} CAMARAS [MULTIPROCESS LOW LATENCY]")
        print(f"{'='*70}\n")

        success_count = 0
        for i, camera in enumerate(camera_list, 1):
            print(f"[{i}/{len(camera_list)}] Iniciando cámara {camera.camera_id}...")
            if camera.start():
                success_count += 1
                print(f"Cámara {camera.camera_id} iniciada [MULTIPROCESS]")
            else:
                print(f"Fallo al iniciar cámara {camera.camera_id}")

        print(f"\n{'='*70}")
        print(f"{success_count}/{len(camera_list)} cámaras iniciadas exitosamente")
        print(f"{'='*70}\n")

    def stop_all_cameras(self):
        """Detiene todas las cámaras gracefully"""
        print(f"\n{'='*70}")
        print("DETENIENDO TODAS LAS CAMARAS...")
        print(f"{'='*70}\n")

        for camera in self.cameras.values():
            camera.stop()

        print(f"\n{'='*70}")
        print("TODAS LAS CAMARAS DETENIDAS")
        print(f"{'='*70}\n")

    def wait_keyboard_interrupt(self):
        """Espera Ctrl+C y maneja apagado gracefully"""
        try:
            running = [c.camera_id for c in self.cameras.values() if c.is_alive()]
            print(f"\n{len(running)} cámaras corriendo [MULTIPROCESS]: {running}")
            print("Presiona Ctrl+C para detener todas las cámaras...\n")

            # Esperar indefinidamente (hasta Ctrl+C)
            while not self._shutdown:
                # Verificar periódicamente si las cámaras siguen vivas
                alive = [c.camera_id for c in self.cameras.values() if c.is_alive()]
                if not alive:
                    print("Todas las cámaras han terminado")
                    break
                import time
                time.sleep(1.0)

        except KeyboardInterrupt:
            print("\nInterrupción de teclado detectada")
            self._shutdown = True
        finally:
            self.stop_all_cameras()

    def print_summary(self):
        """Imprime resumen de todas las cámaras y sus estadísticas"""
        print(f"\n{'='*70}")
        print("RESUMEN DE CAMARAS [MULTIPROCESS LOW LATENCY]")
        print(f"{'='*70}")

        total = len(self.cameras)
        running = sum(1 for cam in self.cameras.values() if cam.is_alive())

        print(f"Total de cámaras: {total}")
        print(f"Cámaras corriendo: {running}")
        print(f"Cámaras detenidas: {total - running}")
        print(f"{'='*70}")

        for camera_id, camera in self.cameras.items():
            stats = camera.get_stats()
            status = "ACTIVA" if camera.is_alive() else "DETENIDA"

            print(f"\nCámara {camera_id} - {status}")
            print(f"  Entradas: {stats.get('entradas', 0)}")
            print(f"  Salidas: {stats.get('salidas', 0)}")
            print(f"  Dentro: {stats.get('dentro', 0)}")

        print(f"{'='*70}\n")


def main():
    """Función principal para sistema multi-cámara LOW LATENCY con MULTIPROCESSING"""

    # Configuración de la API
    API_URL = "http://172.80.20.22/api"

    print("=" * 70)
    print("SISTEMA MULTI-CAMARA DE CONTEO DE PERSONAS")
    print("VERSION: LOW LATENCY + MULTIPROCESSING (Python 3.12 compatible)")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print("Optimizaciones: Tracker IOU, Baja latencia, Multiprocessing")
    print("=" * 70)
    print()

    # NO inicializar GStreamer aquí - cada proceso hijo lo hará

    try:
        # 1. Conectar a la API
        print("Conectando a la API...")
        api_client = CameraAPIClient(API_URL)

        # 2. Obtener TODAS las cámaras
        print("Obteniendo cámaras desde la API...")
        cameras_data = api_client.get_cameras()

        if not cameras_data:
            print("ERROR: No se encontraron cámaras en la API")
            return 1

        print(f"Se encontraron {len(cameras_data)} cámaras")
        print()

        # 3. Crear gestor de múltiples cámaras MULTIPROCESSING
        manager = MultiCameraManagerLowLatencyMP(max_cameras=16, headless=False)
        config_manager = CameraConfig()

        # 4. Agregar TODAS las cámaras
        print("Configurando cámaras...")
        print("=" * 70)
        print(f"PROCESANDO TODAS LAS CAMARAS ({len(cameras_data)} cámaras)")
        print("=" * 70)

        cameras_added = 0
        for idx, camera_data in enumerate(cameras_data, 1):
            camera_id = camera_data['id']
            camera_name = camera_data['cam_nombre']
            camera_ip = camera_data['cam_ip']

            print(f"\n[{idx}/{len(cameras_data)}] Configurando cámara ID {camera_id}:")
            print(f"   Nombre: {camera_name}")
            print(f"   IP: {camera_ip}")

            # Construir URI RTSP
            rtsp_uri = RTSPBuilder.build_rtsp_uri(camera_data)

            if not RTSPBuilder.validate_rtsp_uri(rtsp_uri):
                print(f"   URI RTSP inválida, omitiendo...")
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
                print(f"   Cámara {camera_id} agregada [MULTIPROCESS]")
            else:
                print(f"   Error agregando cámara {camera_id}")

        print("\n" + "=" * 70)
        print(f"{cameras_added}/{len(cameras_data)} cámaras configuradas exitosamente")
        print("=" * 70)
        print()

        if cameras_added == 0:
            print("ERROR: No se agregó ninguna cámara")
            return 1

        # 5. Iniciar todas las cámaras
        manager.start_all_cameras(sequential=True)

        # 6. Esperar interrupción de teclado (Ctrl+C)
        manager.wait_keyboard_interrupt()

        # 7. Mostrar estadísticas finales
        manager.print_summary()

        return 0

    except KeyboardInterrupt:
        print("\nInterrupción por teclado")
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    # Usar 'spawn' para multiprocessing (recomendado para compatibilidad)
    mp.set_start_method('spawn', force=True)
    sys.exit(main())
