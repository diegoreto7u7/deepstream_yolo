"""
Cliente API para obtener configuración de cámaras
"""
import requests
import json
from typing import List, Dict, Optional


class CameraAPIClient:
    """Cliente para comunicarse con la API de cámaras"""

    def __init__(self, api_url: str):
        """
        Inicializa el cliente API

        Args:
            api_url: URL base de la API (ej: http://172.80.20.22/api)
        """
        self.api_url = api_url.rstrip('/')
        self.cameras_endpoint = f"{self.api_url}/camaras"

    def get_cameras(self) -> List[Dict]:
        """
        Obtiene la lista de cámaras desde la API

        Returns:
            Lista de diccionarios con datos de cámaras

        Raises:
            Exception: Si hay error en la comunicación con la API
        """
        try:
            print(f"🌐 Consultando API: {self.cameras_endpoint}")
            response = requests.get(self.cameras_endpoint, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get('success', False):
                raise Exception(f"API retornó error: {data}")

            cameras = data.get('data', [])
            print(f"✅ Se obtuvieron {len(cameras)} cámaras desde la API")

            return cameras

        except requests.exceptions.RequestException as e:
            print(f"❌ Error conectando a la API: {e}")
            raise

        except json.JSONDecodeError as e:
            print(f"❌ Error decodificando respuesta JSON: {e}")
            raise
