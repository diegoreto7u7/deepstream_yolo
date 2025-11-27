#!/usr/bin/env python3
"""
Sistema de Control de Aforo con DeepStream 8.0 + PeopleNet
==========================================================

Usa PeopleNet (modelo preentrenado de NVIDIA) + nvdsanalytics
para deteccion y conteo de personas automatico.

Ventajas sobre YOLO:
- Modelo pre-optimizado por NVIDIA
- nvdsanalytics hace el line crossing automaticamente
- Menor complejidad, mayor estabilidad
"""
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

import pyds
from typing import Dict, Optional
from modules.api_client import CameraAPIClient
from modules.rtsp_builder import RTSPBuilder

# Constantes
PGIE_CLASS_ID_PERSON = 0
MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_TIMEOUT_USEC = 33000
TILED_OUTPUT_WIDTH = 1920
TILED_OUTPUT_HEIGHT = 1080


class OccupancyCounter:
    """Almacena conteos de ocupacion por camara"""

    def __init__(self):
        self.counts: Dict[int, dict] = {}

    def update(self, source_id: int, entry: int, exit_count: int):
        """Actualiza conteos desde nvdsanalytics"""
        if source_id not in self.counts:
            self.counts[source_id] = {'entry': 0, 'exit': 0, 'occupancy': 0}

        self.counts[source_id]['entry'] = entry
        self.counts[source_id]['exit'] = exit_count
        self.counts[source_id]['occupancy'] = max(0, entry - exit_count)

    def get_stats(self) -> Dict[int, dict]:
        return self.counts.copy()


# Global counter
occupancy_counter = OccupancyCounter()


def analytics_src_pad_buffer_probe(pad, info, u_data):
    """
    Probe callback para procesar metadata de nvdsanalytics.
    nvdsanalytics automaticamente detecta cruces de linea.
    """
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    if not batch_meta:
        return Gst.PadProbeReturn.OK

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        source_id = frame_meta.source_id

        # Buscar metadata de nvdsanalytics
        l_user = frame_meta.frame_user_meta_list
        while l_user is not None:
            try:
                user_meta = pyds.NvDsUserMeta.cast(l_user.data)
                if user_meta.base_meta.meta_type == pyds.NvDsMetaType.NVDS_USER_FRAME_META_NVDSANALYTICS:
                    analytics_meta = pyds.NvDsAnalyticsFrameMeta.cast(user_meta.user_meta_data)

                    # Obtener conteos de cruce de linea
                    entry_count = 0
                    exit_count = 0

                    # objLCCumCnt contiene conteos acumulados por label
                    if hasattr(analytics_meta, 'objLCCumCnt'):
                        lc_counts = analytics_meta.objLCCumCnt
                        if 'Entry' in lc_counts:
                            entry_count = lc_counts['Entry']
                        if 'Exit' in lc_counts:
                            exit_count = lc_counts['Exit']

                    # Actualizar contador global
                    occupancy_counter.update(source_id, entry_count, exit_count)

                    # Log periodico
                    if frame_meta.frame_num % 90 == 0:
                        stats = occupancy_counter.counts.get(source_id, {})
                        print(f"[Cam {source_id}] Entrada: {stats.get('entry', 0)} | "
                              f"Salida: {stats.get('exit', 0)} | "
                              f"Ocupacion: {stats.get('occupancy', 0)}")
            except StopIteration:
                break

            try:
                l_user = l_user.next
            except StopIteration:
                break

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK


def osd_sink_pad_buffer_probe(pad, info, u_data):
    """Probe para dibujar informacion en pantalla"""
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        return Gst.PadProbeReturn.OK

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    if not batch_meta:
        return Gst.PadProbeReturn.OK

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        source_id = frame_meta.source_id
        stats = occupancy_counter.counts.get(source_id, {'entry': 0, 'exit': 0, 'occupancy': 0})

        # Agregar texto con estadisticas
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]

        py_nvosd_text_params.display_text = (
            f"Cam{source_id} | E:{stats['entry']} S:{stats['exit']} | Ocupacion:{stats['occupancy']}"
        )
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 14
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
        py_nvosd_text_params.set_bg_clr = 1
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 0.7)

        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK


def bus_call(bus, message, loop):
    """Maneja mensajes del bus de GStreamer"""
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


def create_source_bin(index: int, uri: str):
    """Crea un source bin para una fuente RTSP"""
    bin_name = f"source-bin-{index:02d}"
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        print(f"Unable to create source bin {bin_name}")
        return None

    # Crear uridecodebin
    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", f"uri-decode-bin-{index}")
    if not uri_decode_bin:
        print("Unable to create uridecodebin")
        return None

    uri_decode_bin.set_property("uri", uri)

    def decodebin_child_added(child_proxy, obj, name, user_data):
        if name.find("decodebin") != -1:
            obj.connect("child-added", decodebin_child_added, user_data)
        if name.find("nvv4l2decoder") != -1:
            obj.set_property("drop-frame-interval", 0)

    def cb_newpad(decodebin, decoder_src_pad, data):
        caps = decoder_src_pad.get_current_caps()
        gststruct = caps.get_structure(0)
        gstname = gststruct.get_name()

        if gstname.find("video") != -1:
            bin_ghost_pad = nbin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                print("Failed to set ghost pad target")

    uri_decode_bin.connect("pad-added", cb_newpad)
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)

    Gst.Bin.add(nbin, uri_decode_bin)

    # Crear ghost pad
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
    if not bin_pad:
        print("Failed to add ghost pad to source bin")
        return None

    return nbin


def main():
    """Funcion principal"""

    # Configuracion
    API_URL = "http://172.80.20.22/api"
    HEADLESS = False

    # Rutas de configuracion
    PGIE_CONFIG = "/app/configs/peoplenet/config_infer_peoplenet.txt"
    TRACKER_CONFIG = "/opt/nvidia/deepstream/deepstream-8.0/samples/configs/deepstream-app/config_tracker_NvDCF_perf.yml"
    ANALYTICS_CONFIG = "/app/configs/peoplenet/config_nvdsanalytics.txt"

    print("=" * 70)
    print("SISTEMA DE CONTROL DE AFORO - PeopleNet")
    print("DeepStream 8.0 + nvdsanalytics")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print(f"Modo: {'HEADLESS' if HEADLESS else 'CON DISPLAY'}")
    print("=" * 70)
    print()

    # Inicializar GStreamer
    Gst.init(None)

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
        num_sources = len(cameras_data)

        # 3. Crear pipeline
        print("\nCreando pipeline...")
        pipeline = Gst.Pipeline()
        if not pipeline:
            print("ERROR: No se pudo crear pipeline")
            return 1

        # 4. Crear elementos
        # Streammux
        streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
        if not streammux:
            print("ERROR: No se pudo crear nvstreammux")
            return 1

        streammux.set_property("width", MUXER_OUTPUT_WIDTH)
        streammux.set_property("height", MUXER_OUTPUT_HEIGHT)
        streammux.set_property("batch-size", num_sources)
        streammux.set_property("batched-push-timeout", MUXER_BATCH_TIMEOUT_USEC)
        streammux.set_property("live-source", 1)

        pipeline.add(streammux)

        # 5. Agregar sources
        print("\nConfigurando camaras...")
        for idx, camera_data in enumerate(cameras_data):
            camera_id = camera_data['id']
            camera_name = camera_data['cam_nombre']

            rtsp_uri = RTSPBuilder.build_rtsp_uri(camera_data)
            print(f"  [{idx}] Camara {camera_id} ({camera_name}): {rtsp_uri}")

            source_bin = create_source_bin(idx, rtsp_uri)
            if not source_bin:
                print(f"    ERROR: No se pudo crear source bin")
                continue

            pipeline.add(source_bin)

            srcpad = source_bin.get_static_pad("src")
            sinkpad = streammux.request_pad_simple(f"sink_{idx}")
            if srcpad.link(sinkpad) != Gst.PadLinkReturn.OK:
                print(f"    ERROR: No se pudo conectar source {idx}")
                continue

            print(f"    Conectada como source {idx}")

        # 6. Primary GIE (PeopleNet)
        print("\nConfigurando PeopleNet...")
        pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
        if not pgie:
            print("ERROR: No se pudo crear nvinfer")
            return 1
        pgie.set_property("config-file-path", PGIE_CONFIG)

        # 7. Tracker
        print("Configurando tracker...")
        tracker = Gst.ElementFactory.make("nvtracker", "tracker")
        if not tracker:
            print("ERROR: No se pudo crear nvtracker")
            return 1

        tracker.set_property("ll-lib-file", "/opt/nvidia/deepstream/deepstream-8.0/lib/libnvds_nvmultiobjecttracker.so")
        tracker.set_property("ll-config-file", TRACKER_CONFIG)
        tracker.set_property("tracker-width", 640)
        tracker.set_property("tracker-height", 384)
        tracker.set_property("gpu-id", 0)
        tracker.set_property("enable-batch-process", 1)

        # 8. Analytics (line crossing automatico!)
        print("Configurando nvdsanalytics...")
        analytics = Gst.ElementFactory.make("nvdsanalytics", "analytics")
        if not analytics:
            print("ERROR: No se pudo crear nvdsanalytics")
            return 1
        analytics.set_property("config-file", ANALYTICS_CONFIG)

        # 9. Converter y OSD
        nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")

        if not nvvidconv or not nvosd:
            print("ERROR: No se pudieron crear elementos de video")
            return 1

        nvosd.set_property("process-mode", 0)
        nvosd.set_property("display-text", 1)

        # 10. Tiler (para mostrar multiples camaras)
        tiler = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
        if not tiler:
            print("ERROR: No se pudo crear tiler")
            return 1

        tiler_rows = int(num_sources ** 0.5)
        tiler_cols = int((num_sources + tiler_rows - 1) / tiler_rows)
        tiler.set_property("rows", tiler_rows)
        tiler.set_property("columns", tiler_cols)
        tiler.set_property("width", TILED_OUTPUT_WIDTH)
        tiler.set_property("height", TILED_OUTPUT_HEIGHT)

        # 11. Sink
        if HEADLESS:
            sink = Gst.ElementFactory.make("fakesink", "fakesink")
        else:
            sink = Gst.ElementFactory.make("nv3dsink", "nv3d-sink")
            if not sink:
                sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
            if not sink:
                sink = Gst.ElementFactory.make("xvimagesink", "xvimagesink")

        if not sink:
            print("ERROR: No se pudo crear sink")
            return 1

        sink.set_property("sync", 0)
        sink.set_property("qos", 0)

        # 12. Agregar elementos al pipeline
        print("\nAgregando elementos al pipeline...")
        pipeline.add(pgie)
        pipeline.add(tracker)
        pipeline.add(analytics)
        pipeline.add(tiler)
        pipeline.add(nvvidconv)
        pipeline.add(nvosd)
        pipeline.add(sink)

        # 13. Enlazar elementos
        print("Enlazando elementos...")
        if not streammux.link(pgie):
            print("ERROR: streammux -> pgie")
            return 1
        if not pgie.link(tracker):
            print("ERROR: pgie -> tracker")
            return 1
        if not tracker.link(analytics):
            print("ERROR: tracker -> analytics")
            return 1
        if not analytics.link(tiler):
            print("ERROR: analytics -> tiler")
            return 1
        if not tiler.link(nvvidconv):
            print("ERROR: tiler -> nvvidconv")
            return 1
        if not nvvidconv.link(nvosd):
            print("ERROR: nvvidconv -> nvosd")
            return 1
        if not nvosd.link(sink):
            print("ERROR: nvosd -> sink")
            return 1

        # 14. Agregar probes
        analytics_src_pad = analytics.get_static_pad("src")
        if analytics_src_pad:
            analytics_src_pad.add_probe(
                Gst.PadProbeType.BUFFER,
                analytics_src_pad_buffer_probe,
                0
            )

        osd_sink_pad = nvosd.get_static_pad("sink")
        if osd_sink_pad:
            osd_sink_pad.add_probe(
                Gst.PadProbeType.BUFFER,
                osd_sink_pad_buffer_probe,
                0
            )

        # 15. Crear loop y bus
        loop = GLib.MainLoop()
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)

        # 16. Iniciar pipeline
        print("\n" + "=" * 70)
        print("INICIANDO PIPELINE")
        print("=" * 70)
        print("Presiona Ctrl+C para detener...\n")

        pipeline.set_state(Gst.State.PLAYING)

        try:
            loop.run()
        except KeyboardInterrupt:
            print("\nInterrupcion por teclado")

        # 17. Cleanup
        pipeline.set_state(Gst.State.NULL)

        # 18. Estadisticas finales
        print("\n" + "=" * 70)
        print("ESTADISTICAS FINALES")
        print("=" * 70)
        for source_id, stats in occupancy_counter.get_stats().items():
            print(f"Camara {source_id}:")
            print(f"  Entradas: {stats['entry']}")
            print(f"  Salidas: {stats['exit']}")
            print(f"  Ocupacion actual: {stats['occupancy']}")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
