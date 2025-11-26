#!/usr/bin/env python3
"""
Pipeline DeepStream multi-camara usando pyds (bindings tradicionales)

Este modulo usa las bindings estables de pyds en lugar de pyservicemaker
para evitar problemas de GIL con Python 3.12.

Basado en deepstream_python_apps de NVIDIA.
"""
import sys
import math
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import pyds
from typing import Dict, List, Optional
from modules.line_crossing_detector import LineCrossingDetector


# Constantes
PGIE_CLASS_ID_PERSON = 0
MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_TIMEOUT_USEC = 33000
TILED_OUTPUT_WIDTH = 1920
TILED_OUTPUT_HEIGHT = 1080


class MultiCameraCounter:
    """Maneja conteo de linea para multiples camaras"""

    def __init__(self):
        self.cameras_config: Dict[int, dict] = {}
        self.contadores: Dict[int, dict] = {}
        self.line_detectors: Dict[int, LineCrossingDetector] = {}
        self.tracked_objects: Dict[int, dict] = {}
        self.frame_counts: Dict[int, int] = {}

    def add_camera(self, source_id: int, camera_id: int, camera_name: str, line_config: dict):
        """Agrega configuracion para una camara"""
        self.cameras_config[source_id] = {
            'camera_id': camera_id,
            'camera_name': camera_name,
            'line_config': line_config
        }
        self.contadores[source_id] = {'entradas': 0, 'salidas': 0, 'dentro': 0}

        detector = LineCrossingDetector()
        start_line = tuple(line_config['start'])
        end_line = tuple(line_config['end'])
        detector.set_line(start_line, end_line)
        detector.set_direction(line_config['direccion_entrada'])
        self.line_detectors[source_id] = detector

        self.tracked_objects[source_id] = {}
        self.frame_counts[source_id] = 0

        print(f"  [Source {source_id}] Camera {camera_id}: Linea {start_line} -> {end_line}")

    def process_object(self, source_id: int, obj_meta) -> Optional[str]:
        """Procesa un objeto detectado"""
        if source_id not in self.cameras_config:
            return None

        track_id = obj_meta.object_id
        camera_id = self.cameras_config[source_id]['camera_id']

        rect = obj_meta.rect_params
        center_x = rect.left + rect.width / 2
        center_y = rect.top + rect.height / 2
        current_pos = (int(center_x), int(center_y))

        unique_id = (source_id, track_id)

        if unique_id not in self.tracked_objects[source_id]:
            self.tracked_objects[source_id][unique_id] = {'prev_pos': current_pos}
            return None

        prev_pos = self.tracked_objects[source_id][unique_id]['prev_pos']
        detector = self.line_detectors[source_id]

        cruce = None
        if detector.tiene_linea_configurada():
            cruce = detector.punto_cruza_linea(center_x, center_y, prev_pos[0], prev_pos[1])

            if cruce == "ENTRADA":
                self.contadores[source_id]['entradas'] += 1
                self.contadores[source_id]['dentro'] += 1
                print(f">> [Cam {camera_id}] ENTRADA (ID:{track_id}) | "
                      f"E:{self.contadores[source_id]['entradas']} D:{self.contadores[source_id]['dentro']}")
            elif cruce == "SALIDA":
                self.contadores[source_id]['salidas'] += 1
                self.contadores[source_id]['dentro'] = max(0, self.contadores[source_id]['dentro'] - 1)
                print(f"<< [Cam {camera_id}] SALIDA (ID:{track_id}) | "
                      f"S:{self.contadores[source_id]['salidas']} D:{self.contadores[source_id]['dentro']}")

        self.tracked_objects[source_id][unique_id]['prev_pos'] = current_pos
        return cruce

    def get_stats(self, source_id: int) -> dict:
        return self.contadores.get(source_id, {'entradas': 0, 'salidas': 0, 'dentro': 0})

    def get_all_stats(self) -> Dict[int, dict]:
        result = {}
        for source_id, config in self.cameras_config.items():
            camera_id = config['camera_id']
            result[camera_id] = self.contadores[source_id].copy()
        return result

    def get_line_points(self, source_id: int):
        if source_id in self.line_detectors:
            detector = self.line_detectors[source_id]
            return detector.line_start, detector.line_end
        return None, None


# Instancia global del contador
_counter = MultiCameraCounter()


def osd_sink_pad_buffer_probe(pad, info, u_data):
    """Probe callback para procesar metadatos"""
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        source_id = frame_meta.source_id

        # Procesar objetos
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            if obj_meta.class_id == PGIE_CLASS_ID_PERSON:
                _counter.process_object(source_id, obj_meta)

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        # Agregar texto OSD
        if source_id in _counter.cameras_config:
            camera_id = _counter.cameras_config[source_id]['camera_id']
            stats = _counter.get_stats(source_id)

            display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
            display_meta.num_labels = 1

            py_nvosd_text_params = display_meta.text_params[0]
            py_nvosd_text_params.display_text = f"Cam{camera_id}|E:{stats['entradas']} S:{stats['salidas']}|D:{stats['dentro']}"
            py_nvosd_text_params.x_offset = 10
            py_nvosd_text_params.y_offset = 12
            py_nvosd_text_params.font_params.font_name = "Serif"
            py_nvosd_text_params.font_params.font_size = 12
            py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
            py_nvosd_text_params.set_bg_clr = 1
            py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 0.7)

            # Dibujar linea
            line_start, line_end = _counter.get_line_points(source_id)
            if line_start and line_end:
                display_meta.num_lines = 1
                py_nvosd_line_params = display_meta.line_params[0]
                py_nvosd_line_params.x1 = int(line_start[0])
                py_nvosd_line_params.y1 = int(line_start[1])
                py_nvosd_line_params.x2 = int(line_end[0])
                py_nvosd_line_params.y2 = int(line_end[1])
                py_nvosd_line_params.line_width = 3
                py_nvosd_line_params.line_color.set(0.0, 1.0, 0.0, 1.0)

            pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        # Log periodico
        _counter.frame_counts[source_id] = _counter.frame_counts.get(source_id, 0) + 1
        if _counter.frame_counts[source_id] % 90 == 0:
            if source_id in _counter.cameras_config:
                camera_id = _counter.cameras_config[source_id]['camera_id']
                stats = _counter.get_stats(source_id)
                print(f"[Cam {camera_id}] Frame {_counter.frame_counts[source_id]} | "
                      f"E:{stats['entradas']} S:{stats['salidas']} D:{stats['dentro']}")

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK


def cb_newpad(decodebin, decoder_src_pad, data):
    """Callback para nuevo pad de decodebin"""
    caps = decoder_src_pad.get_current_caps()
    if not caps:
        caps = decoder_src_pad.query_caps()
    gststruct = caps.get_structure(0)
    gstname = gststruct.get_name()
    source_bin = data
    features = caps.get_features(0)

    if gstname.find("video") != -1:
        if features.contains("memory:NVMM"):
            bin_ghost_pad = source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad\n")


def decodebin_child_added(child_proxy, Object, name, user_data):
    """Callback para child del decodebin"""
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)
    if "source" in name:
        source_element = child_proxy.get_by_name("source")
        if source_element and source_element.find_property('drop-on-latency'):
            Object.set_property("drop-on-latency", True)


def create_source_bin(index, uri):
    """Crea source bin para una URI"""
    bin_name = f"source-bin-{index:02d}"
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        return None

    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        return None

    uri_decode_bin.set_property("uri", uri)
    uri_decode_bin.connect("pad-added", cb_newpad, nbin)
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)

    Gst.Bin.add(nbin, uri_decode_bin)
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
    if not bin_pad:
        return None

    return nbin


class DeepStreamMultiCameraPipeline:
    """Pipeline DeepStream multi-camara usando pyds"""

    def __init__(self, config_file: str = "/app/configs/deepstream/config_infer_primary_yolo11x_b1.txt",
                 headless: bool = False):
        self.config_file = config_file
        self.headless = headless
        self.cameras: List[dict] = []
        self.pipeline = None
        self.loop = None

        # Inicializar GStreamer
        Gst.init(None)

    def add_camera(self, camera_id: int, camera_name: str, rtsp_uri: str, line_config: dict) -> int:
        """Agrega una camara"""
        source_id = len(self.cameras)
        self.cameras.append({
            'source_id': source_id,
            'camera_id': camera_id,
            'camera_name': camera_name,
            'rtsp_uri': rtsp_uri,
            'line_config': line_config
        })
        _counter.add_camera(source_id, camera_id, camera_name, line_config)
        print(f"Camara {camera_id} ({camera_name}) agregada como source {source_id}")
        return source_id

    def build(self):
        """Construye el pipeline"""
        if not self.cameras:
            raise ValueError("No hay camaras agregadas")

        num_sources = len(self.cameras)
        print(f"\n{'='*60}")
        print(f"Construyendo pipeline con {num_sources} camaras (pyds)")
        print(f"{'='*60}")

        self.pipeline = Gst.Pipeline()
        if not self.pipeline:
            raise RuntimeError("No se pudo crear Pipeline")

        # Streammux
        streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
        if not streammux:
            raise RuntimeError("No se pudo crear NvStreamMux")

        streammux.set_property('width', MUXER_OUTPUT_WIDTH)
        streammux.set_property('height', MUXER_OUTPUT_HEIGHT)
        streammux.set_property('batch-size', num_sources)
        streammux.set_property('batched-push-timeout', MUXER_BATCH_TIMEOUT_USEC)
        self.pipeline.add(streammux)

        # Source bins
        for cam in self.cameras:
            source_id = cam['source_id']
            uri = cam['rtsp_uri']

            source_bin = create_source_bin(source_id, uri)
            if not source_bin:
                raise RuntimeError(f"No se pudo crear source bin para {uri}")

            self.pipeline.add(source_bin)
            padname = f"sink_{source_id}"
            sinkpad = streammux.request_pad_simple(padname)
            srcpad = source_bin.get_static_pad("src")
            srcpad.link(sinkpad)
            print(f"  Source {source_id} conectado al mux")

        # PGIE
        pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
        if not pgie:
            raise RuntimeError("No se pudo crear nvinfer")
        pgie.set_property('config-file-path', self.config_file)

        # Tracker
        tracker = Gst.ElementFactory.make("nvtracker", "tracker")
        if not tracker:
            raise RuntimeError("No se pudo crear nvtracker")

        tracker_config = "/opt/nvidia/deepstream/deepstream-8.0/samples/configs/deepstream-app/config_tracker_IOU.yml"
        tracker_lib = "/opt/nvidia/deepstream/deepstream-8.0/lib/libnvds_nvmultiobjecttracker.so"
        tracker.set_property('tracker-width', 640)
        tracker.set_property('tracker-height', 480)
        tracker.set_property('ll-lib-file', tracker_lib)
        tracker.set_property('ll-config-file', tracker_config)

        # Tiler
        tiler = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
        if not tiler:
            raise RuntimeError("No se pudo crear tiler")

        tiler_rows = int(math.sqrt(num_sources))
        tiler_columns = int(math.ceil(num_sources / tiler_rows))
        tiler.set_property("rows", tiler_rows)
        tiler.set_property("columns", tiler_columns)
        tiler.set_property("width", TILED_OUTPUT_WIDTH)
        tiler.set_property("height", TILED_OUTPUT_HEIGHT)

        # Convertor
        nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        if not nvvidconv:
            raise RuntimeError("No se pudo crear nvvideoconvert")

        # OSD
        nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
        if not nvosd:
            raise RuntimeError("No se pudo crear nvdsosd")

        # Sink
        if self.headless:
            sink = Gst.ElementFactory.make("fakesink", "fakesink")
        else:
            sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
            if not sink:
                sink = Gst.ElementFactory.make("xvimagesink", "video-renderer")

        if not sink:
            raise RuntimeError("No se pudo crear sink")

        if not self.headless:
            sink.set_property('sync', False)
            sink.set_property('async', False)

        # Agregar elementos
        self.pipeline.add(pgie)
        self.pipeline.add(tracker)
        self.pipeline.add(tiler)
        self.pipeline.add(nvvidconv)
        self.pipeline.add(nvosd)
        self.pipeline.add(sink)

        # Linkear
        streammux.link(pgie)
        pgie.link(tracker)
        tracker.link(tiler)
        tiler.link(nvvidconv)
        nvvidconv.link(nvosd)
        nvosd.link(sink)

        # Agregar probe
        osdsinkpad = nvosd.get_static_pad("sink")
        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

        print(f"Pipeline construido: {num_sources} camaras")

    def run(self):
        """Ejecuta el pipeline"""
        if not self.pipeline:
            raise RuntimeError("Pipeline no construido")

        print(f"\n{'='*60}")
        print("INICIANDO PIPELINE MULTI-CAMARA (pyds)")
        print(f"{'='*60}\n")

        self.loop = GLib.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._bus_call, self.loop)

        self.pipeline.set_state(Gst.State.PLAYING)

        try:
            self.loop.run()
        except KeyboardInterrupt:
            print("\nDeteniendo pipeline...")
        finally:
            self.pipeline.set_state(Gst.State.NULL)

    def _bus_call(self, bus, message, loop):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            print(f"Warning: {err}: {debug}")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}: {debug}")
            loop.quit()
        return True

    def get_stats(self) -> Dict[int, dict]:
        return _counter.get_all_stats()
