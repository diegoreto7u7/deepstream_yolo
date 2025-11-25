"""
Wrapper multiprocessing para DeepStreamCamera LOW LATENCY
Usa multiprocessing en lugar de threading para evitar problemas de GIL con Python 3.12 y GStreamer

NOTA: Python 3.12 tiene manejo más estricto del GIL que causa errores fatales
con GStreamer/GLib cuando se usa threading. Multiprocessing evita este problema
al dar a cada cámara su propio proceso con su propio GIL.
"""
import multiprocessing as mp
from multiprocessing import Process, Event, Queue, Manager
import time
from typing import Dict, Optional
import os
import signal


def _camera_process_main(camera_id: int, camera_name: str, rtsp_uri: str,
                         line_config: dict, headless: bool,
                         started_event: mp.Event, error_event: mp.Event,
                         stop_event: mp.Event, stats_dict: dict):
    """
    Función principal que corre en cada proceso de cámara

    Inicializa GStreamer DENTRO del proceso para evitar problemas de GIL
    """
    # Ignorar SIGINT en procesos hijos (el padre maneja Ctrl+C)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        # Importar GStreamer DENTRO del proceso
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import Gst

        # Inicializar GStreamer EN ESTE PROCESO
        Gst.init(None)

        print(f"[Process {camera_id}] GStreamer inicializado en proceso {os.getpid()}")

        # Importar el módulo de cámara
        from modules.deepstream_camera_sm_low_latency import DeepStreamCameraServiceMakerLowLatency

        mode_str = "HEADLESS" if headless else "LOW LATENCY DISPLAY"
        print(f"[Process {camera_id}] Creando instancia DeepStreamCameraServiceMakerLowLatency [{mode_str}]...")

        # Crear instancia DeepStream
        ds_camera = DeepStreamCameraServiceMakerLowLatency(
            camera_id=camera_id,
            camera_name=camera_name,
            rtsp_uri=rtsp_uri,
            line_config=line_config,
            headless=headless
        )

        # Señalar inicio exitoso
        started_event.set()
        print(f"[Process {camera_id}] Pipeline LOW LATENCY creado exitosamente, iniciando...")

        # Ejecutar pipeline (bloqueante)
        # El pipeline se detendrá cuando stop_event se active o por error
        ds_camera.run()

        # Copiar estadísticas finales al diccionario compartido
        if hasattr(ds_camera, 'counter'):
            final_stats = ds_camera.counter.contadores
            stats_dict['entradas'] = final_stats.get('entradas', 0)
            stats_dict['salidas'] = final_stats.get('salidas', 0)
            stats_dict['dentro'] = final_stats.get('dentro', 0)

        print(f"[Process {camera_id}] Pipeline finalizado")

    except Exception as e:
        error_event.set()
        started_event.set()  # Desbloquear al padre
        print(f"[Process {camera_id}] Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print(f"[Process {camera_id}] Proceso finalizando (PID: {os.getpid()})")


class MultiprocessDeepStreamCameraLowLatency:
    """
    Wrapper basado en multiprocessing para DeepStreamCamera con baja latencia

    Cada cámara ejecuta en su propio PROCESO (no thread) para evitar
    problemas de GIL con Python 3.12 y GStreamer/GLib.
    """

    def __init__(self, camera_id: int, camera_name: str,
                 rtsp_uri: str, line_config: dict, headless: bool = False):
        """
        Inicializa wrapper de cámara con multiprocessing (versión baja latencia)

        Args:
            camera_id: ID de la cámara
            camera_name: Nombre descriptivo
            rtsp_uri: URI RTSP completa
            line_config: Configuración de línea de cruce
            headless: Si True, no muestra ventanas (solo terminal)
        """
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.rtsp_uri = rtsp_uri
        self.line_config = line_config
        self.headless = headless

        # Process management
        self.process: Optional[Process] = None
        self.started_event = Event()
        self.error_event = Event()
        self.stop_event = Event()

        # Manager para datos compartidos entre procesos
        self._manager = Manager()
        self._stats_dict = self._manager.dict({
            'entradas': 0,
            'salidas': 0,
            'dentro': 0
        })

        # Métricas locales
        self.metrics = {
            'fps': 0.0,
            'last_update': time.time()
        }

    def start(self) -> bool:
        """
        Inicia procesamiento de cámara en proceso dedicado

        Returns:
            True si se inició exitosamente
        """
        if self.process and self.process.is_alive():
            print(f"Camera {self.camera_id} ya está corriendo")
            return False

        # Reset events
        self.started_event.clear()
        self.error_event.clear()
        self.stop_event.clear()

        # Crear proceso
        self.process = Process(
            target=_camera_process_main,
            args=(
                self.camera_id,
                self.camera_name,
                self.rtsp_uri,
                self.line_config,
                self.headless,
                self.started_event,
                self.error_event,
                self.stop_event,
                self._stats_dict
            ),
            name=f"Camera-{self.camera_id}-Process",
            daemon=False
        )
        self.process.start()

        # Esperar inicio (timeout 30s)
        print(f"Esperando inicialización de cámara {self.camera_id} [LOW LATENCY MULTIPROCESS]...")
        if not self.started_event.wait(timeout=30.0):
            print(f"Camera {self.camera_id} no se inició en 30 segundos")
            self.stop()
            return False

        if self.error_event.is_set():
            print(f"Camera {self.camera_id} error durante inicialización")
            return False

        return True

    def stop(self, timeout: float = 8.0):
        """
        Detiene procesamiento de cámara gracefully

        Args:
            timeout: Tiempo máximo de espera para detener el proceso
        """
        if not self.process or not self.process.is_alive():
            print(f"[Main] Cámara {self.camera_id} ya está detenida")
            return

        print(f"[Main] Deteniendo cámara {self.camera_id}...")

        # Señalar stop
        self.stop_event.set()

        # Esperar terminación graceful
        self.process.join(timeout=timeout)

        # Si no terminó, forzar
        if self.process.is_alive():
            print(f"[Main] Forzando terminación de cámara {self.camera_id}...")
            self.process.terminate()
            self.process.join(timeout=2.0)

            if self.process.is_alive():
                print(f"[Main] Kill forzado de cámara {self.camera_id}")
                self.process.kill()

        print(f"Cámara {self.camera_id} detenida")

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas de la cámara

        Returns:
            Diccionario con contadores (copia read-only)
        """
        return dict(self._stats_dict)

    def get_fps(self) -> float:
        """
        Obtiene FPS actual (aproximado)

        Returns:
            FPS como float
        """
        return self.metrics['fps']

    def is_alive(self) -> bool:
        """
        Verifica si el proceso de cámara está vivo

        Returns:
            True si el proceso está corriendo
        """
        return self.process is not None and self.process.is_alive()
