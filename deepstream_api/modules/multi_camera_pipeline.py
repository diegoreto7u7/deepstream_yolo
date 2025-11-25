#!/usr/bin/env python3
"""
Pipeline unificado multi-cámara usando pyservicemaker
Usa UN SOLO pipeline con nvstreammux para procesar múltiples cámaras

Esta es la forma CORRECTA de manejar múltiples cámaras en DeepStream:
- Un solo pipeline procesa todas las cámaras
- nvstreammux combina todos los streams en un batch
- La inferencia se hace una vez por batch (más eficiente)
- Evita problemas de GIL/threading con Python 3.12
"""

from pyservicemaker import Pipeline, Flow, BatchMetadataOperator, Probe, osd, RenderMode
from modules.line_crossing_detector import LineCrossingDetector
from typing import Dict, List, Tuple


class MultiCameraLineCrossingCounter(BatchMetadataOperator):
    """
    Operador que maneja conteo de línea para MÚLTIPLES cámaras
    Cada frame en el batch viene de una cámara diferente (identificada por pad_index)
    """

    def __init__(self, cameras_config: Dict[int, dict]):
        """
        Inicializa contador multi-cámara

        Args:
            cameras_config: Dict mapping pad_index -> {
                'camera_id': int,
                'camera_name': str,
                'line_config': dict con 'start', 'end', 'direccion_entrada'
            }
        """
        super().__init__()
        self.cameras_config = cameras_config

        # Contadores por cámara (keyed by pad_index)
        self.contadores: Dict[int, dict] = {}

        # Detectores de línea por cámara
        self.line_detectors: Dict[int, LineCrossingDetector] = {}

        # Objetos trackeados por cámara
        self.tracked_objects: Dict[int, dict] = {}

        # Frame counters por cámara
        self.frame_counts: Dict[int, int] = {}

        # Inicializar para cada cámara
        for pad_idx, config in cameras_config.items():
            camera_id = config['camera_id']
            line_config = config['line_config']

            # Contadores
            self.contadores[pad_idx] = {
                'entradas': 0,
                'salidas': 0,
                'dentro': 0
            }

            # Detector de línea
            detector = LineCrossingDetector()
            start_line = tuple(line_config['start'])
            end_line = tuple(line_config['end'])
            detector.set_line(start_line, end_line)
            detector.set_direction(line_config['direccion_entrada'])
            self.line_detectors[pad_idx] = detector

            # Tracking
            self.tracked_objects[pad_idx] = {}
            self.frame_counts[pad_idx] = 0

            print(f"  [Pad {pad_idx}] Camera {camera_id}: Linea {start_line} -> {end_line}")

        print(f"MultiCameraLineCrossingCounter inicializado para {len(cameras_config)} camaras")

    def handle_metadata(self, batch_meta):
        """
        Procesa metadatos del batch (frames de múltiples cámaras)
        """
        try:
            for frame_meta in batch_meta.frame_items:
                # pad_index identifica de qué cámara viene este frame
                pad_idx = frame_meta.pad_index

                # Verificar que tenemos config para esta cámara
                if pad_idx not in self.cameras_config:
                    continue

                camera_id = self.cameras_config[pad_idx]['camera_id']

                # Procesar detecciones de personas
                for object_meta in frame_meta.object_items:
                    if object_meta.class_id == 0:  # Solo personas
                        self._process_detection(pad_idx, object_meta)

                # Dibujar overlays
                self._draw_overlays(batch_meta, frame_meta, pad_idx)

                # Log periódico
                self.frame_counts[pad_idx] += 1
                if self.frame_counts[pad_idx] % 90 == 0:
                    stats = self.contadores[pad_idx]
                    print(f"[Cam {camera_id}] E:{stats['entradas']} S:{stats['salidas']} D:{stats['dentro']}")

        except Exception as e:
            print(f"Error en handle_metadata: {e}")

    def _process_detection(self, pad_idx: int, object_meta):
        """Procesa detección para una cámara específica"""
        try:
            track_id = object_meta.object_id
            camera_id = self.cameras_config[pad_idx]['camera_id']

            # Calcular centro
            bbox_left = object_meta.rect_params.left
            bbox_top = object_meta.rect_params.top
            bbox_width = object_meta.rect_params.width
            bbox_height = object_meta.rect_params.height

            center_x = bbox_left + bbox_width / 2
            center_y = bbox_top + bbox_height / 2
            current_pos = (int(center_x), int(center_y))

            # Track ID único por cámara
            unique_track_id = (pad_idx, track_id)

            if unique_track_id not in self.tracked_objects[pad_idx]:
                self.tracked_objects[pad_idx][unique_track_id] = {
                    'prev_pos': current_pos,
                    'crossed': False
                }
                return

            prev_pos = self.tracked_objects[pad_idx][unique_track_id]['prev_pos']
            detector = self.line_detectors[pad_idx]

            if detector.tiene_linea_configurada():
                cruce = detector.punto_cruza_linea(
                    center_x, center_y, prev_pos[0], prev_pos[1]
                )

                if cruce == "ENTRADA":
                    self.contadores[pad_idx]['entradas'] += 1
                    self.contadores[pad_idx]['dentro'] += 1
                    print(f">> [Cam {camera_id}] ENTRADA (ID:{track_id}) | "
                          f"Total E:{self.contadores[pad_idx]['entradas']} D:{self.contadores[pad_idx]['dentro']}")

                elif cruce == "SALIDA":
                    self.contadores[pad_idx]['salidas'] += 1
                    self.contadores[pad_idx]['dentro'] = max(0, self.contadores[pad_idx]['dentro'] - 1)
                    print(f"<< [Cam {camera_id}] SALIDA (ID:{track_id}) | "
                          f"Total S:{self.contadores[pad_idx]['salidas']} D:{self.contadores[pad_idx]['dentro']}")

            self.tracked_objects[pad_idx][unique_track_id]['prev_pos'] = current_pos

        except Exception as e:
            print(f"Error procesando deteccion: {e}")

    def _draw_overlays(self, batch_meta, frame_meta, pad_idx: int):
        """Dibuja overlays para una cámara específica"""
        try:
            camera_id = self.cameras_config[pad_idx]['camera_id']
            detector = self.line_detectors[pad_idx]
            stats = self.contadores[pad_idx]

            display_meta = batch_meta.acquire_display_meta()

            # Línea de cruce
            line = osd.Line()
            line.x1 = int(detector.line_start[0])
            line.y1 = int(detector.line_start[1])
            line.x2 = int(detector.line_end[0])
            line.y2 = int(detector.line_end[1])
            line.width = 3
            line.color = osd.Color(0.0, 1.0, 0.0, 1.0)
            display_meta.add_line(line)

            # Texto con contadores
            text = osd.Text()
            text.display_text = (
                f"Cam{camera_id}|E:{stats['entradas']} S:{stats['salidas']}|D:{stats['dentro']}"
            ).encode('ascii')
            text.x_offset = 10
            text.y_offset = 10
            text.font.name = osd.FontFamily.Serif
            text.font.size = 12
            text.font.color = osd.Color(1.0, 1.0, 1.0, 1.0)
            text.set_bg_color = True
            text.bg_color = osd.Color(0.0, 0.0, 0.0, 0.7)
            display_meta.add_text(text)

            frame_meta.append(display_meta)

        except Exception as e:
            print(f"Error dibujando overlays: {e}")

    def get_all_stats(self) -> Dict[int, dict]:
        """Retorna estadísticas de todas las cámaras"""
        result = {}
        for pad_idx, config in self.cameras_config.items():
            camera_id = config['camera_id']
            result[camera_id] = self.contadores[pad_idx].copy()
        return result


class MultiCameraPipeline:
    """
    Pipeline unificado que procesa múltiples cámaras RTSP

    Ventajas:
    - Un solo pipeline = un solo proceso = sin problemas de GIL
    - Inferencia por batch más eficiente
    - Menor uso de memoria GPU
    - Menor latencia total
    """

    def __init__(self, headless: bool = False):
        """
        Inicializa pipeline multi-cámara

        Args:
            headless: Si True, no muestra video (solo procesa)
        """
        self.headless = headless
        self.cameras: List[dict] = []
        self.pipeline = None
        self.flow = None
        self.counter = None

    def add_camera(self, camera_id: int, camera_name: str,
                   rtsp_uri: str, line_config: dict) -> int:
        """
        Agrega una cámara al pipeline

        Args:
            camera_id: ID de la cámara
            camera_name: Nombre de la cámara
            rtsp_uri: URI RTSP
            line_config: Configuración de línea

        Returns:
            pad_index asignado (0, 1, 2, ...)
        """
        pad_index = len(self.cameras)
        self.cameras.append({
            'pad_index': pad_index,
            'camera_id': camera_id,
            'camera_name': camera_name,
            'rtsp_uri': rtsp_uri,
            'line_config': line_config
        })
        print(f"Camara {camera_id} ({camera_name}) agregada como pad {pad_index}")
        return pad_index

    def build(self, config_file: str = "/app/configs/deepstream/config_infer_primary_yolo11x_b1.txt"):
        """
        Construye el pipeline con todas las cámaras agregadas
        """
        if not self.cameras:
            raise ValueError("No hay camaras agregadas")

        num_cameras = len(self.cameras)
        print(f"\n{'='*60}")
        print(f"Construyendo pipeline con {num_cameras} camaras")
        print(f"{'='*60}")

        # Lista de URIs RTSP
        uri_list = [cam['rtsp_uri'] for cam in self.cameras]

        # Configuración de cámaras para el counter
        cameras_config = {
            cam['pad_index']: {
                'camera_id': cam['camera_id'],
                'camera_name': cam['camera_name'],
                'line_config': cam['line_config']
            }
            for cam in self.cameras
        }

        # Crear pipeline
        self.pipeline = Pipeline("multi-camera-pipeline")

        # Crear counter multi-cámara
        self.counter = MultiCameraLineCrossingCounter(cameras_config)

        # Tracker config
        tracker_config = "/opt/nvidia/deepstream/deepstream-8.0/samples/configs/deepstream-app/config_tracker_IOU.yml"
        tracker_lib = "/opt/nvidia/deepstream/deepstream-8.0/lib/libnvds_nvmultiobjecttracker.so"

        # Construir flow con batch_capture para múltiples streams
        # batch-size debe ser >= número de cámaras
        base_flow = (Flow(self.pipeline)
                    .batch_capture(uri_list, **{'batch-size': num_cameras})
                    .infer(config_file)
                    .track(ll_config_file=tracker_config, ll_lib_file=tracker_lib)
                    .attach(what=Probe("multi-camera-counter", self.counter)))

        # Sink
        if not self.headless:
            # Con display - usar tiler para mostrar todas las cámaras
            self.flow = base_flow.render(
                sync=False,
                qos=False,
                async_handling=False,
                max_lateness=-1
            )
        else:
            self.flow = base_flow.render(mode=RenderMode.DISCARD)

        print(f"Pipeline construido: {num_cameras} camaras, headless={self.headless}")

    def run(self):
        """Ejecuta el pipeline (bloqueante)"""
        if not self.flow:
            raise RuntimeError("Pipeline no construido. Llamar build() primero.")

        print(f"\n{'='*60}")
        print(f"INICIANDO PIPELINE MULTI-CAMARA")
        print(f"Camaras: {[c['camera_id'] for c in self.cameras]}")
        print(f"{'='*60}\n")

        try:
            self.flow()
        except KeyboardInterrupt:
            print("\nPipeline detenido por usuario")
        except Exception as e:
            print(f"Error en pipeline: {e}")
            import traceback
            traceback.print_exc()

    def get_stats(self) -> Dict[int, dict]:
        """Retorna estadísticas de todas las cámaras"""
        if self.counter:
            return self.counter.get_all_stats()
        return {}
