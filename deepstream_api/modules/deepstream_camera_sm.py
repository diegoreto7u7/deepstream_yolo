#!/usr/bin/env python3
"""
Módulo DeepStream usando pyservicemaker (DeepStream 8.0+)
Implementa detección de personas y conteo con línea de cruce
"""

from pyservicemaker import Pipeline, Flow, BatchMetadataOperator, Probe, osd, RenderMode
from modules.line_crossing_detector import LineCrossingDetector


class LineCrossingCounter(BatchMetadataOperator):
    """
    Operador personalizado para detectar cruces de línea y contar personas
    """

    def __init__(self, camera_id, camera_name, line_config):
        """
        Inicializa el contador de línea

        Args:
            camera_id: ID de la cámara
            camera_name: Nombre de la cámara
            line_config: dict con 'start', 'end', 'direccion_entrada'
        """
        super().__init__()
        self.camera_id = camera_id
        self.camera_name = camera_name

        # Configurar detector de línea SIN scaling
        # Las coordenadas de Laravel ya están en el espacio correcto
        start_line = tuple(line_config['start'])
        end_line = tuple(line_config['end'])

        self.line_detector = LineCrossingDetector()
        self.line_detector.set_line(start_line, end_line)
        self.line_detector.set_direction(line_config['direccion_entrada'])

        # Contadores
        self.contadores = {
            'entradas': 0,
            'salidas': 0,
            'dentro': 0
        }

        # Objetos trackeados
        self.tracked_objects = {}

        # Frame counter para logs periódicos
        self.frame_count = 0

        print(f"✅ LineCrossingCounter inicializado para cámara {camera_id}")
        print(f"   Línea (sin escalar): {start_line} -> {end_line}")
        print(f"   Dirección entrada: {line_config['direccion_entrada']}")

    def handle_metadata(self, batch_meta):
        """
        Procesa metadatos de cada batch
        Este método se llama por cada frame procesado
        """
        try:
            # Iterar sobre todos los frames en el batch
            for frame_meta in batch_meta.frame_items:
                # Procesar objetos detectados (solo personas, clase 0)
                for object_meta in frame_meta.object_items:
                    if object_meta.class_id == 0:  # Solo personas
                        self.process_detection(object_meta)

                # Dibujar línea y contadores en el frame
                self.draw_overlays(batch_meta, frame_meta)

            # Log periódico en consola
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                print(f"[Camera {self.camera_id}] E:{self.contadores['entradas']} "
                      f"S:{self.contadores['salidas']} D:{self.contadores['dentro']}")

        except Exception as e:
            print(f"❌ Error en handle_metadata: {e}")
            import traceback
            traceback.print_exc()

    def process_detection(self, object_meta):
        """Procesa una detección de persona y verifica cruce de línea"""
        try:
            track_id = object_meta.object_id

            # DEBUG: Imprimir atributos disponibles
            if not hasattr(self, '_debug_printed'):
                print(f"DEBUG: Atributos de object_meta: {dir(object_meta)}")
                self._debug_printed = True

            # Calcular centro del bbox - probar rect_params según DeepStream C API
            bbox_left = object_meta.rect_params.left
            bbox_top = object_meta.rect_params.top
            bbox_width = object_meta.rect_params.width
            bbox_height = object_meta.rect_params.height

            center_x = bbox_left + bbox_width / 2
            center_y = bbox_top + bbox_height / 2
            current_pos = (int(center_x), int(center_y))

            # Si es la primera vez que vemos este objeto
            if track_id not in self.tracked_objects:
                self.tracked_objects[track_id] = {
                    'prev_pos': current_pos,
                    'crossed': False
                }
                return

            # Verificar cruce de línea
            prev_pos = self.tracked_objects[track_id]['prev_pos']

            if self.line_detector.tiene_linea_configurada():
                cruce = self.line_detector.punto_cruza_linea(
                    center_x, center_y, prev_pos[0], prev_pos[1]
                )

                if cruce == "ENTRADA":
                    self.contadores['entradas'] += 1
                    self.contadores['dentro'] += 1
                    print(f"✅ [Cam {self.camera_id}] ENTRADA detectada (ID: {track_id}) "
                          f"| Total E:{self.contadores['entradas']} D:{self.contadores['dentro']}")

                elif cruce == "SALIDA":
                    self.contadores['salidas'] += 1
                    self.contadores['dentro'] = max(0, self.contadores['dentro'] - 1)
                    print(f"⬅️  [Cam {self.camera_id}] SALIDA detectada (ID: {track_id}) "
                          f"| Total S:{self.contadores['salidas']} D:{self.contadores['dentro']}")

            # Actualizar posición previa
            self.tracked_objects[track_id]['prev_pos'] = current_pos

        except Exception as e:
            print(f"❌ Error procesando detección: {e}")

    def draw_overlays(self, batch_meta, frame_meta):
        """Dibuja línea de cruce y contadores en el frame"""
        try:
            # Crear display metadata
            display_meta = batch_meta.acquire_display_meta()

            # Dibujar línea de cruce
            line = osd.Line()
            line.x1 = int(self.line_detector.line_start[0])
            line.y1 = int(self.line_detector.line_start[1])
            line.x2 = int(self.line_detector.line_end[0])
            line.y2 = int(self.line_detector.line_end[1])
            line.width = 4
            line.color = osd.Color(0.0, 1.0, 0.0, 1.0)  # Verde
            display_meta.add_line(line)

            # Dibujar texto con contadores
            text = osd.Text()
            text.display_text = (
                f"Cam {self.camera_id} | E:{self.contadores['entradas']} "
                f"S:{self.contadores['salidas']} | Dentro:{self.contadores['dentro']}"
            ).encode('ascii')
            text.x_offset = 10
            text.y_offset = 10
            text.font.name = osd.FontFamily.Serif
            text.font.size = 14
            text.font.color = osd.Color(1.0, 1.0, 1.0, 1.0)  # Blanco
            text.set_bg_color = True
            text.bg_color = osd.Color(0.0, 0.0, 0.0, 0.7)  # Negro semi-transparente
            display_meta.add_text(text)

            # Agregar display metadata al frame
            frame_meta.append(display_meta)

        except Exception as e:
            print(f"❌ Error dibujando overlays: {e}")


class DeepStreamCameraServiceMaker:
    """
    Wrapper para cámara usando pyservicemaker
    """

    def __init__(self, camera_id, camera_name, rtsp_uri, line_config,
                 config_file="/app/configs/deepstream/config_infer_primary_yolo11x_b1.txt",
                 headless=False):
        """
        Inicializa la cámara con pyservicemaker

        Args:
            camera_id: ID de la cámara
            camera_name: Nombre de la cámara
            rtsp_uri: URI RTSP de la cámara
            line_config: dict con configuración de línea
            config_file: Ruta al archivo de configuración de inferencia
            headless: Si True, no renderiza video (mejor rendimiento)
        """
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.rtsp_uri = rtsp_uri
        self.line_config = line_config
        self.config_file = config_file
        self.headless = headless

        # Crear pipeline y flow
        self.pipeline = Pipeline(f"camera-{camera_id}")

        # Crear operador personalizado
        self.counter = LineCrossingCounter(camera_id, camera_name, line_config)

        # Construir flow CON tracker para IDs persistentes
        # El OSD se agrega automáticamente con render()
        tracker_config = "/opt/nvidia/deepstream/deepstream-8.0/samples/configs/deepstream-app/config_tracker_NvDCF_perf.yml"
        tracker_lib = "/opt/nvidia/deepstream/deepstream-8.0/lib/libnvds_nvmultiobjecttracker.so"

        base_flow = (Flow(self.pipeline)
                    .batch_capture([rtsp_uri])
                    .infer(config_file)
                    .track(ll_config_file=tracker_config, ll_lib_file=tracker_lib)
                    .attach(what=Probe("line-crossing", self.counter)))

        # Agregar sink según modo
        # render() automáticamente agrega OSD antes del sink
        if not headless:
            # Modo normal: mostrar video en ventana de 1280x720
            # Esto asegura que la línea dibujada coincida con la posición visual
            self.flow = base_flow.render(
                window_width=1280,
                window_height=720,
                force_aspect_ratio=True
            )
        else:
            # Modo headless: usar fakesink (descarta los frames sin mostrarlos)
            self.flow = base_flow.render(mode=RenderMode.DISCARD)

        print(f"✅ DeepStreamCameraServiceMaker creado para cámara {camera_id}")
        print(f"   Modo: {'HEADLESS (sin display)' if headless else 'NORMAL (con display)'}")

    def run(self):
        """Ejecuta el pipeline (blocking)"""
        print(f"🚀 Iniciando cámara {self.camera_id} ({self.camera_name})...")
        try:
            self.flow()  # Blocking call
        except KeyboardInterrupt:
            print(f"\n⚠️  Cámara {self.camera_id} detenida por usuario")
        except Exception as e:
            print(f"❌ Error en cámara {self.camera_id}: {e}")
            import traceback
            traceback.print_exc()

    def get_counters(self):
        """Retorna contadores actuales"""
        return self.counter.contadores.copy()
