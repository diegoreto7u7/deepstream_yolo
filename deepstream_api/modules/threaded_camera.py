"""
Wrapper thread-safe para DeepStreamCamera
Permite ejecutar múltiples cámaras en paralelo usando threading
"""
import threading
import queue
import time
from typing import Dict, Optional
import gi

gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst

from .deepstream_camera_sm import DeepStreamCameraServiceMaker


class ThreadedDeepStreamCamera:
    """
    Wrapper thread-safe para DeepStreamCamera

    Cada cámara ejecuta en su propio thread con GLib.MainLoop dedicado
    """

    def __init__(self, camera_id: int, camera_name: str,
                 rtsp_uri: str, line_config: dict, headless: bool = False):
        """
        Inicializa wrapper de cámara con threading

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

        # Thread management
        self.thread: Optional[threading.Thread] = None
        self.command_queue: queue.Queue = queue.Queue()
        self.is_running = threading.Event()
        self.started = threading.Event()
        self.error_event = threading.Event()
        self.error_msg: Optional[str] = None

        # DeepStream instance (creado en el thread)
        self.deepstream_instance = None

        # Thread-local GLib context
        self._glib_context = None

        # Métricas de rendimiento
        self.metrics = {
            'fps': 0.0,
            'frame_count': 0,
            'last_update': time.time()
        }
        self.metrics_lock = threading.Lock()

    def start(self) -> bool:
        """
        Inicia procesamiento de cámara en thread dedicado

        Returns:
            True si se inició exitosamente
        """
        if self.thread and self.thread.is_alive():
            print(f"⚠️  Camera {self.camera_id} ya está corriendo")
            return False

        self.is_running.set()
        self.thread = threading.Thread(
            target=self._run_camera_thread,
            name=f"Camera-{self.camera_id}-Thread",
            daemon=False
        )
        self.thread.start()

        # Esperar a que el thread se inicialice (timeout 30s - suficiente para RTSP lento)
        print(f"⏳ Esperando inicialización de cámara {self.camera_id}...")
        if not self.started.wait(timeout=30.0):
            print(f"❌ Camera {self.camera_id} no se inició en 30 segundos")
            self.is_running.clear()
            return False

        if self.error_event.is_set():
            print(f"❌ Camera {self.camera_id} error: {self.error_msg}")
            return False

        return True

    def _run_camera_thread(self):
        """
        Función principal del thread - ejecuta GLib.MainLoop
        """
        try:
            # Establecer nombre del thread para debugging
            threading.current_thread().name = f"Camera-{self.camera_id}"

            # Inicializar GStreamer en este thread
            Gst.init(None)

            # Crear contexto GLib thread-local
            # Esto asegura que GLib.MainLoop no interfiera con otros threads
            self._glib_context = GLib.MainContext.new()
            GLib.MainContext.push_thread_default(self._glib_context)

            print(f"[Thread {self.camera_id}] Iniciando thread de cámara...")

            # Crear instancia DeepStream con Service Maker
            mode_str = "HEADLESS (solo terminal)" if self.headless else "DISPLAY (con ventanas)"
            print(f"[Thread {self.camera_id}] 📹 Creando instancia DeepStreamCameraServiceMaker [{mode_str}]...")
            self.deepstream_instance = DeepStreamCameraServiceMaker(
                camera_id=self.camera_id,
                camera_name=self.camera_name,
                rtsp_uri=self.rtsp_uri,
                line_config=self.line_config,
                headless=self.headless
            )

            # Señalar inicio exitoso antes de bloquear
            self.started.set()
            print(f"[Thread {self.camera_id}] ✅ Pipeline creado exitosamente, iniciando...")

            # LLAMADA BLOQUEANTE - Service Maker maneja todo internamente
            # Esto ejecuta el pipeline hasta que se detenga
            self.deepstream_instance.run()

            print(f"[Thread {self.camera_id}] Pipeline finalizado")

        except Exception as e:
            self.error_msg = str(e)
            self.error_event.set()
            self.started.set()  # Desbloquear llamador de start()
            print(f"❌ [Thread {self.camera_id}] Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Limpieza
            self._cleanup_thread()
            self.is_running.clear()
            print(f"[Thread {self.camera_id}] Thread finalizando")

    def _check_commands(self) -> bool:
        """
        Verifica cola de comandos y los maneja
        NOTA: Con Service Maker esto no se usa actualmente,
        ya que run() es bloqueante y maneja el loop internamente.

        Returns:
            True para continuar verificando, False para detener
        """
        return True  # Placeholder

    def _update_metrics(self) -> bool:
        """
        Actualiza métricas de rendimiento (FPS)
        NOTA: Con Service Maker, las métricas se manejan en el operador LineCrossingCounter

        Returns:
            True para continuar actualizando
        """
        if not self.deepstream_instance:
            return False

        with self.metrics_lock:
            now = time.time()
            elapsed = now - self.metrics['last_update']

            if elapsed >= 1.0:
                # Service Maker maneja el frame_count internamente en LineCrossingCounter
                # Aproximamos FPS basado en el frame_count del contador
                if hasattr(self.deepstream_instance, 'counter'):
                    frame_count = self.deepstream_instance.counter.frame_count
                    self.metrics['fps'] = frame_count / elapsed if elapsed > 0 else 0.0
                    # No podemos resetear porque no tenemos control directo

                self.metrics['last_update'] = now

        return True

    def stop(self, timeout: float = 8.0):
        """
        Detiene procesamiento de cámara gracefully

        Args:
            timeout: Tiempo máximo de espera para detener el thread
        """
        if not self.is_running.is_set() and not (self.thread and self.thread.is_alive()):
            print(f"[Main] Cámara {self.camera_id} ya está detenida")
            return

        print(f"[Main] Deteniendo cámara {self.camera_id}...")

        # Marcar como no running
        self.is_running.clear()

        # Detener el pipeline de Service Maker
        if self.deepstream_instance and hasattr(self.deepstream_instance, 'pipeline'):
            try:
                # Acceder al pipeline interno de pyservicemaker y detenerlo
                self.deepstream_instance.pipeline.pipeline.set_state(Gst.State.NULL)
            except Exception as e:
                print(f"⚠️  Error deteniendo pipeline: {e}")

        # Esperar a que el thread finalice
        if self.thread:
            self.thread.join(timeout=timeout)
            if self.thread.is_alive():
                print(f"⚠️  Thread de cámara {self.camera_id} no se detuvo en {timeout}s")
            else:
                print(f"✅ Cámara {self.camera_id} detenida correctamente")

    def _cleanup_thread(self):
        """
        Limpia recursos en el thread de cámara
        Debe ejecutarse en el thread de cámara
        """
        try:
            if self.deepstream_instance:
                # Detener pipeline de Service Maker
                if hasattr(self.deepstream_instance, 'pipeline') and self.deepstream_instance.pipeline:
                    try:
                        self.deepstream_instance.pipeline.pipeline.set_state(Gst.State.NULL)
                    except:
                        pass

            # Pop thread-local GLib context solo si existe
            if self._glib_context:
                try:
                    GLib.MainContext.pop_thread_default(self._glib_context)
                except:
                    # Ignorar errores de GLib context en cleanup
                    pass

        except Exception as e:
            print(f"⚠️  Error durante limpieza: {e}")

    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas de la cámara

        Returns:
            Diccionario con contadores (copia read-only)
        """
        if self.deepstream_instance and hasattr(self.deepstream_instance, 'counter'):
            return self.deepstream_instance.counter.contadores.copy()
        return {'entradas': 0, 'salidas': 0, 'dentro': 0}

    def get_fps(self) -> float:
        """
        Obtiene FPS actual

        Returns:
            FPS como float
        """
        with self.metrics_lock:
            return self.metrics['fps']

    def is_alive(self) -> bool:
        """
        Verifica si el thread de cámara está vivo

        Returns:
            True si el thread está corriendo
        """
        return self.thread is not None and self.thread.is_alive()
