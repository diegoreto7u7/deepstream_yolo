"""
Gestor de múltiples cámaras con threading
Coordina el ciclo de vida de múltiples cámaras DeepStream
"""
import threading
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .threaded_camera import ThreadedDeepStreamCamera


class MultiCameraManager:
    """
    Gestor de múltiples cámaras con threading

    Thread-Safety Guarantees:
    - Gestión thread-safe del ciclo de vida de cámaras
    - Apagado coordinado de todas las cámaras
    - Sin race conditions en operaciones start/stop
    """

    def __init__(self, max_cameras: int = 16, headless: bool = False):
        """
        Inicializa gestor de múltiples cámaras

        Args:
            max_cameras: Número máximo de cámaras simultáneas
            headless: Si True, no muestra ventanas (solo terminal)
        """
        self.cameras: Dict[int, ThreadedDeepStreamCamera] = {}
        self.max_cameras = max_cameras
        self.headless = headless
        self.shutdown_event = threading.Event()

        # Lock para modificaciones del dict de cámaras
        self._cameras_lock = threading.Lock()

    def add_camera(self, camera_id: int, camera_name: str,
                   rtsp_uri: str, line_config: dict) -> bool:
        """
        Agrega cámara al gestor

        Args:
            camera_id: ID único de la cámara
            camera_name: Nombre descriptivo
            rtsp_uri: URI RTSP completa
            line_config: Configuración de línea de cruce

        Returns:
            True si se agregó exitosamente
        """
        with self._cameras_lock:
            if len(self.cameras) >= self.max_cameras:
                print(f"❌ Máximo de cámaras ({self.max_cameras}) alcanzado")
                return False

            if camera_id in self.cameras:
                print(f"❌ Cámara {camera_id} ya existe")
                return False

            camera = ThreadedDeepStreamCamera(
                camera_id=camera_id,
                camera_name=camera_name,
                rtsp_uri=rtsp_uri,
                line_config=line_config,
                headless=self.headless
            )

            self.cameras[camera_id] = camera
            print(f"✅ Cámara {camera_id} ({camera_name}) agregada al gestor")
            return True

    def remove_camera(self, camera_id: int) -> bool:
        """
        Remueve cámara del gestor (debe estar detenida)

        Args:
            camera_id: ID de la cámara a remover

        Returns:
            True si se removió exitosamente
        """
        with self._cameras_lock:
            camera = self.cameras.get(camera_id)

            if not camera:
                print(f"❌ Cámara {camera_id} no encontrada")
                return False

            if camera.is_alive():
                print(f"❌ Cámara {camera_id} aún está corriendo. Deténgala primero.")
                return False

            del self.cameras[camera_id]
            print(f"✅ Cámara {camera_id} removida del gestor")
            return True

    def start_camera(self, camera_id: int) -> bool:
        """
        Inicia una cámara específica

        Args:
            camera_id: ID de la cámara a iniciar

        Returns:
            True si se inició exitosamente
        """
        with self._cameras_lock:
            camera = self.cameras.get(camera_id)

        if not camera:
            print(f"❌ Cámara {camera_id} no encontrada")
            return False

        return camera.start()

    def start_all_cameras(self, sequential: bool = False):
        """
        Inicia todas las cámaras

        Args:
            sequential: Si True, inicia una por una. Si False, inicia en paralelo

        Sequential (secuencial):
            - Más seguro y fácil de debugear
            - Menor carga inicial en CPU/GPU
            - Tiempo: 2-3s por cámara
            - Recomendado para desarrollo

        Parallel (paralelo):
            - Más rápido
            - Alta carga inicial en CPU/GPU
            - Tiempo: 5-10s total para todas
            - Recomendado para producción con hardware adecuado
        """
        with self._cameras_lock:
            camera_list = list(self.cameras.values())

        if not camera_list:
            print("⚠️  No hay cámaras para iniciar")
            return

        print(f"\n{'='*70}")
        print(f"🚀 INICIANDO {len(camera_list)} CÁMARAS "
              f"({'SECUENCIAL' if sequential else 'PARALELO'})")
        print(f"{'='*70}\n")

        if sequential:
            # Iniciar cámaras una por una (más seguro, más lento)
            success_count = 0
            for i, camera in enumerate(camera_list, 1):
                print(f"[{i}/{len(camera_list)}] Iniciando cámara {camera.camera_id}...")
                if camera.start():
                    success_count += 1
                    print(f"✅ Cámara {camera.camera_id} iniciada")
                else:
                    print(f"❌ Fallo al iniciar cámara {camera.camera_id}")

            print(f"\n{'='*70}")
            print(f"✅ {success_count}/{len(camera_list)} cámaras iniciadas exitosamente")
            print(f"{'='*70}\n")

        else:
            # Iniciar cámaras en paralelo (más rápido, mayor carga inicial)
            success_count = 0
            failed_cameras = []

            with ThreadPoolExecutor(max_workers=len(camera_list)) as executor:
                futures = {
                    executor.submit(camera.start): camera
                    for camera in camera_list
                }

                for future in as_completed(futures):
                    camera = futures[future]
                    try:
                        success = future.result(timeout=20.0)
                        if success:
                            success_count += 1
                            print(f"✅ Cámara {camera.camera_id} iniciada")
                        else:
                            failed_cameras.append(camera.camera_id)
                            print(f"❌ Cámara {camera.camera_id} falló")
                    except Exception as e:
                        failed_cameras.append(camera.camera_id)
                        print(f"❌ Cámara {camera.camera_id} error: {e}")

            print(f"\n{'='*70}")
            print(f"✅ {success_count}/{len(camera_list)} cámaras iniciadas exitosamente")
            if failed_cameras:
                print(f"❌ Cámaras fallidas: {failed_cameras}")
            print(f"{'='*70}\n")

    def stop_camera(self, camera_id: int, timeout: float = 5.0):
        """
        Detiene una cámara específica

        Args:
            camera_id: ID de la cámara a detener
            timeout: Tiempo máximo de espera
        """
        with self._cameras_lock:
            camera = self.cameras.get(camera_id)

        if camera:
            camera.stop(timeout=timeout)
        else:
            print(f"❌ Cámara {camera_id} no encontrada")

    def stop_all_cameras(self):
        """
        Detiene todas las cámaras gracefully
        """
        print(f"\n{'='*70}")
        print("🛑 DETENIENDO TODAS LAS CÁMARAS...")
        print(f"{'='*70}\n")

        self.shutdown_event.set()

        with self._cameras_lock:
            camera_list = list(self.cameras.values())

        if not camera_list:
            print("⚠️  No hay cámaras corriendo")
            return

        # Detener todas las cámaras en paralelo
        with ThreadPoolExecutor(max_workers=len(camera_list)) as executor:
            futures = {
                executor.submit(camera.stop): camera
                for camera in camera_list
            }

            for future in as_completed(futures):
                camera = futures[future]
                try:
                    future.result(timeout=10.0)
                    print(f"✅ Cámara {camera.camera_id} detenida")
                except Exception as e:
                    print(f"⚠️  Error deteniendo cámara {camera.camera_id}: {e}")

        print(f"\n{'='*70}")
        print("✅ TODAS LAS CÁMARAS DETENIDAS")
        print(f"{'='*70}\n")

    def get_camera_stats(self, camera_id: int) -> Dict:
        """
        Obtiene estadísticas de una cámara específica

        Args:
            camera_id: ID de la cámara

        Returns:
            Diccionario con estadísticas
        """
        with self._cameras_lock:
            camera = self.cameras.get(camera_id)

        if camera:
            return camera.get_stats()
        return {'entradas': 0, 'salidas': 0, 'dentro': 0}

    def get_all_stats(self) -> Dict[int, Dict]:
        """
        Obtiene estadísticas de todas las cámaras

        Returns:
            Diccionario {camera_id: stats}
        """
        stats = {}
        with self._cameras_lock:
            for camera_id, camera in self.cameras.items():
                stats[camera_id] = camera.get_stats()
        return stats

    def get_all_fps(self) -> Dict[int, float]:
        """
        Obtiene FPS de todas las cámaras

        Returns:
            Diccionario {camera_id: fps}
        """
        fps_data = {}
        with self._cameras_lock:
            for camera_id, camera in self.cameras.items():
                fps_data[camera_id] = camera.get_fps()
        return fps_data

    def get_running_cameras(self) -> List[int]:
        """
        Obtiene lista de IDs de cámaras corriendo

        Returns:
            Lista de camera_ids
        """
        running = []
        with self._cameras_lock:
            for camera_id, camera in self.cameras.items():
                if camera.is_alive():
                    running.append(camera_id)
        return running

    def get_camera_count(self) -> int:
        """
        Obtiene número total de cámaras en el gestor

        Returns:
            Número de cámaras
        """
        with self._cameras_lock:
            return len(self.cameras)

    def wait_keyboard_interrupt(self):
        """
        Espera Ctrl+C y maneja apagado gracefully
        Debe ejecutarse en el thread principal
        """
        try:
            running = self.get_running_cameras()
            print(f"\n✅ {len(running)} cámaras corriendo: {running}")
            print("Presiona Ctrl+C para detener todas las cámaras...\n")
            self.shutdown_event.wait()
        except KeyboardInterrupt:
            print("\n⚠️  Interrupción de teclado detectada")
        finally:
            self.stop_all_cameras()

    def print_summary(self):
        """
        Imprime resumen de todas las cámaras y sus estadísticas
        """
        print(f"\n{'='*70}")
        print("📊 RESUMEN DE CÁMARAS")
        print(f"{'='*70}")

        with self._cameras_lock:
            total = len(self.cameras)
            running = sum(1 for cam in self.cameras.values() if cam.is_alive())

        print(f"Total de cámaras: {total}")
        print(f"Cámaras corriendo: {running}")
        print(f"Cámaras detenidas: {total - running}")
        print(f"{'='*70}")

        # Estadísticas por cámara
        all_stats = self.get_all_stats()
        all_fps = self.get_all_fps()

        for camera_id, stats in all_stats.items():
            fps = all_fps.get(camera_id, 0.0)
            with self._cameras_lock:
                camera = self.cameras[camera_id]
                status = "🟢 ACTIVA" if camera.is_alive() else "🔴 DETENIDA"

            print(f"\nCámara {camera_id} - {status}")
            print(f"  FPS: {fps:.1f}")
            print(f"  Entradas: {stats['entradas']}")
            print(f"  Salidas: {stats['salidas']}")
            print(f"  Dentro: {stats['dentro']}")

        print(f"{'='*70}\n")
