"""
Gestión de configuración de cámaras
"""
import json
from pathlib import Path
from typing import Dict, Tuple, Optional


class CameraConfig:
    """Gestiona la configuración de líneas de conteo para cámaras"""

    def __init__(self, config_dir: str = "deepstream_api/config"):
        """
        Inicializa el gestor de configuración

        Args:
            config_dir: Directorio donde guardar las configuraciones
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_line_config(self, camera_id: int, api_coordinates) -> Dict:
        """
        Obtiene la configuración de línea para una cámara

        Primero intenta cargar desde archivo local (si el usuario la editó)
        Si no existe, usa las coordenadas de la API

        Args:
            camera_id: ID de la cámara
            api_coordinates: Coordenadas desde la API (dict o string JSON)

        Returns:
            Diccionario con 'start', 'end', 'direccion_entrada'
        """
        config_file = self.config_dir / f"camera_{camera_id}_line.json"

        # Intentar cargar desde archivo local
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"📁 Configuración de línea cargada desde: {config_file}")
                return config
            except Exception as e:
                print(f"⚠️  Error cargando config local: {e}, usando API")

        # Parsear coordenadas de la API
        try:
            # Si api_coordinates ya es un diccionario, usarlo directamente
            if isinstance(api_coordinates, dict):
                coords = api_coordinates
            else:
                # Si es un string JSON, parsearlo
                coords = json.loads(api_coordinates)

            config = {
                'start': coords.get('start', [0, 0]),
                'end': coords.get('end', [0, 0]),
                'direccion_entrada': coords.get('direccion_entrada', 'izquierda')
            }
            print(f"🌐 Usando coordenadas desde API para cámara {camera_id}")
            return config
        except (json.JSONDecodeError, TypeError) as e:
            print(f"❌ Error parseando coordenadas de API: {e}")
            # Retornar configuración por defecto
            return {
                'start': [0, 0],
                'end': [0, 0],
                'direccion_entrada': 'izquierda'
            }

    def get_camera_metadata(self, camera_data: Dict) -> Dict:
        """
        Extrae metadata importante de la cámara

        Args:
            camera_data: Datos completos de la cámara desde API

        Returns:
            Diccionario con metadata
        """
        return {
            'id': camera_data.get('id'),
            'nombre': camera_data.get('cam_nombre', 'Sin nombre'),
            'zona_id': camera_data.get('zonas_id'),
            'ip': camera_data.get('cam_ip')
        }

    def save_camera_metadata(self, camera_id: int, metadata: Dict):
        """
        Guarda metadata de la cámara

        Args:
            camera_id: ID de la cámara
            metadata: Diccionario con metadata
        """
        metadata_file = self.config_dir / f"camera_{camera_id}_metadata.json"

        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"❌ Error guardando metadata: {e}")
