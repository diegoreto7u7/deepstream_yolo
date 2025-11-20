#!/usr/bin/env python3
"""
DeepStream Camera con grabación de video
Versión modificada de deepstream_camera_headless que graba el video con detecciones
"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os

# Paths de DeepStream
DEEPSTREAM_DIR = os.environ.get('DEEPSTREAM_DIR', '/opt/nvidia/deepstream/deepstream')
TRACKER_LIB = f'{DEEPSTREAM_DIR}/lib/libnvds_nvmultiobjecttracker.so'

class DeepStreamCameraRecorder:
    """
    Cámara DeepStream que graba video con detecciones y OSD
    Similar a headless pero con encoder H264 y filesink
    """

    def __init__(self, camera_id, camera_name, rtsp_url,
                 line_coords, line_direction="derecha",
                 output_dir="/app/logs/videos"):
        """
        Args:
            camera_id: ID único de la cámara
            camera_name: Nombre descriptivo
            rtsp_url: URL RTSP completa
            line_coords: Tupla ((x1,y1), (x2,y2)) de la línea de conteo
            line_direction: "izquierda" o "derecha" (entrada desde ese lado)
            output_dir: Directorio donde guardar videos
        """
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.rtsp_url = rtsp_url
        self.line_coords = line_coords
        self.line_direction = line_direction
        self.output_dir = output_dir

        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)

        # Nombre del archivo de video
        self.output_file = os.path.join(
            output_dir,
            f"camera_{camera_id}_{camera_name.replace(' ', '_')}.mp4"
        )

        self.pipeline = None
        self.loop = None
        self.is_running = False

        # Contadores
        self.count_in = 0
        self.count_out = 0

        print(f"✓ DeepStreamCameraRecorder inicializado")
        print(f"   ID: {camera_id}")
        print(f"   Nombre: {camera_name}")
        print(f"   Output: {self.output_file}")
        print()

    def create_tracker_config(self):
        """Crea archivo de configuración del tracker"""
        config_content = """[tracker]
tracker-width=640
tracker-height=384
gpu-id=0
ll-lib-file=/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so
ll-config-file=tracker_config.yml
enable-batch-process=1
enable-past-frame=1
display-tracking-id=1

[property]
tracker-surface-type=1
"""
        with open('tracker_config.txt', 'w') as f:
            f.write(config_content.strip())

    def create_pipeline(self):
        """Crea el pipeline GStreamer con grabación de video"""

        print("[Camera Recorder] 🔧 Creando pipeline con grabación...")

        # Crear pipeline
        self.pipeline = Gst.Pipeline.new(f"camera-recorder-{self.camera_id}")

        # ===== SOURCE (RTSP) =====
        rtspsrc = Gst.ElementFactory.make("rtspsrc", "source")
        rtspsrc.set_property('location', self.rtsp_url)
        rtspsrc.set_property('latency', 100)
        rtspsrc.set_property('drop-on-latency', True)
        print(f"   📡 RTSP source: {self.rtsp_url}")

        # ===== DEPAY =====
        depay = Gst.ElementFactory.make("rtph264depay", "depay")

        # ===== H264 PARSE =====
        h264parse = Gst.ElementFactory.make("h264parse", "h264parse")

        # ===== DECODER (NVIDIA) =====
        decoder = Gst.ElementFactory.make("nvv4l2decoder", "decoder")
        decoder.set_property('gpu-id', 0)

        # ===== NVIDIA VIDEO CONVERT (post-decoder) =====
        nvvidconv_pre = Gst.ElementFactory.make("nvvideoconvert", "nvvidconv_pre")
        nvvidconv_pre.set_property('gpu-id', 0)

        # ===== CAPS para NVMM =====
        caps_nvmm = Gst.ElementFactory.make("capsfilter", "caps_nvmm")
        caps_nvmm.set_property('caps',
            Gst.Caps.from_string("video/x-raw(memory:NVMM), format=NV12"))

        # ===== STREAM MUX =====
        streammux = Gst.ElementFactory.make("nvstreammux", "streammux")
        streammux.set_property('gpu-id', 0)
        streammux.set_property('batch-size', 1)
        streammux.set_property('width', 1280)
        streammux.set_property('height', 720)
        streammux.set_property('batched-push-timeout', 40000)
        streammux.set_property('live-source', True)

        # ===== INFERENCE (YOLO) =====
        nvinfer = Gst.ElementFactory.make("nvinfer", "nvinfer")
        nvinfer.set_property('config-file-path',
            '/app/configs/deepstream/config_infer_primary_yolo11x_b1.txt')
        nvinfer.set_property('gpu-id', 0)
        print("   🤖 YOLO inference configurado")

        # ===== TRACKER =====
        nvtracker = Gst.ElementFactory.make("nvtracker", "nvtracker")
        nvtracker.set_property('gpu-id', 0)
        nvtracker.set_property('tracker-width', 640)
        nvtracker.set_property('tracker-height', 384)
        nvtracker.set_property('ll-lib-file', TRACKER_LIB)
        self.create_tracker_config()
        nvtracker.set_property('ll-config-file', 'tracker_config.yml')
        print("   🎯 Tracker configurado")

        # ===== ON-SCREEN DISPLAY (OSD) =====
        nvdsosd = Gst.ElementFactory.make("nvdsosd", "nvosd")
        nvdsosd.set_property('process-mode', 1)  # GPU mode
        nvdsosd.set_property('display-text', True)
        nvdsosd.set_property('display-bbox', True)
        print("   🎨 OSD configurado (bboxes + IDs)")

        # ===== NVIDIA VIDEO CONVERT (post-OSD) =====
        nvvidconv_post = Gst.ElementFactory.make("nvvideoconvert", "nvvidconv_post")
        nvvidconv_post.set_property('gpu-id', 0)

        # ===== CAPS FILTER (output format) =====
        caps_out = Gst.ElementFactory.make("capsfilter", "caps_out")
        caps_out.set_property('caps',
            Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

        # ===== ENCODER H264 (NVIDIA) =====
        encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
        encoder.set_property('bitrate', 4000000)  # 4 Mbps
        encoder.set_property('insert-sps-pps', True)
        encoder.set_property('iframeinterval', 30)
        print("   🎥 Encoder H264 configurado (4 Mbps)")

        # ===== H264 PARSE (post-encoder) =====
        h264parse_out = Gst.ElementFactory.make("h264parse", "h264parse_out")

        # ===== MP4 MUX =====
        mp4mux = Gst.ElementFactory.make("mp4mux", "mp4mux")

        # ===== FILE SINK =====
        filesink = Gst.ElementFactory.make("filesink", "filesink")
        filesink.set_property('location', self.output_file)
        filesink.set_property('sync', False)
        filesink.set_property('async', False)
        print(f"   💾 Grabando a: {self.output_file}")

        # Agregar todos los elementos
        elements = [
            rtspsrc, depay, h264parse, decoder,
            nvvidconv_pre, caps_nvmm, streammux, nvinfer, nvtracker,
            nvdsosd, nvvidconv_post, caps_out, encoder, h264parse_out,
            mp4mux, filesink
        ]

        for elem in elements:
            self.pipeline.add(elem)

        # Conectar elementos
        rtspsrc.connect("pad-added", self.on_rtspsrc_pad_added, depay)

        # Enlaces estáticos
        if not depay.link(h264parse):
            print("❌ Error: depay -> h264parse")
            return False
        if not h264parse.link(decoder):
            print("❌ Error: h264parse -> decoder")
            return False
        if not decoder.link(nvvidconv_pre):
            print("❌ Error: decoder -> nvvidconv_pre")
            return False
        if not nvvidconv_pre.link(caps_nvmm):
            print("❌ Error: nvvidconv_pre -> caps_nvmm")
            return False

        # Conectar a streammux (sink pad)
        sinkpad = streammux.get_request_pad("sink_0")
        if not sinkpad:
            print("❌ Error: No se pudo obtener sink pad de streammux")
            return False
        srcpad = caps_nvmm.get_static_pad("src")
        if srcpad.link(sinkpad) != Gst.PadLinkReturn.OK:
            print("❌ Error: caps_nvmm -> streammux")
            return False

        # Resto del pipeline
        if not streammux.link(nvinfer):
            print("❌ Error: streammux -> nvinfer")
            return False
        if not nvinfer.link(nvtracker):
            print("❌ Error: nvinfer -> nvtracker")
            return False
        if not nvtracker.link(nvdsosd):
            print("❌ Error: nvtracker -> nvdsosd")
            return False
        if not nvdsosd.link(nvvidconv_post):
            print("❌ Error: nvdsosd -> nvvidconv_post")
            return False
        if not nvvidconv_post.link(caps_out):
            print("❌ Error: nvvidconv_post -> caps_out")
            return False
        if not caps_out.link(encoder):
            print("❌ Error: caps_out -> encoder")
            return False
        if not encoder.link(h264parse_out):
            print("❌ Error: encoder -> h264parse_out")
            return False
        if not h264parse_out.link(mp4mux):
            print("❌ Error: h264parse_out -> mp4mux")
            return False
        if not mp4mux.link(filesink):
            print("❌ Error: mp4mux -> filesink")
            return False

        print("✅ Pipeline con grabación creado exitosamente")
        return True

    def on_rtspsrc_pad_added(self, src, new_pad, depay):
        """Callback cuando rtspsrc agrega un pad"""
        sink_pad = depay.get_static_pad("sink")
        if not sink_pad.is_linked():
            new_pad.link(sink_pad)

    def start(self):
        """Inicia el pipeline"""
        if not self.create_pipeline():
            return False

        print(f"[Camera Recorder {self.camera_id}] ▶️  Iniciando grabación...")

        # Establecer pipeline a PLAYING
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print(f"❌ Error: No se pudo iniciar pipeline de cámara {self.camera_id}")
            return False

        self.is_running = True
        print(f"✅ Cámara {self.camera_id} grabando")
        return True

    def stop(self):
        """Detiene el pipeline y cierra el video"""
        if self.pipeline:
            print(f"[Camera Recorder {self.camera_id}] ⏹️  Deteniendo grabación...")

            # Enviar EOS para cerrar el archivo correctamente
            self.pipeline.send_event(Gst.Event.new_eos())

            # Esperar un momento para que se procese el EOS
            import time
            time.sleep(2)

            # Detener pipeline
            self.pipeline.set_state(Gst.State.NULL)
            self.is_running = False

            print(f"✅ Video guardado: {self.output_file}")

            # Mostrar tamaño del archivo
            if os.path.exists(self.output_file):
                size_mb = os.path.getsize(self.output_file) / (1024 * 1024)
                print(f"   📏 Tamaño: {size_mb:.2f} MB")
