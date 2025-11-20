"""
Constructor de URIs RTSP desde datos de cámaras
"""
from typing import Dict
from urllib.parse import quote


class RTSPBuilder:
    """Construye URIs RTSP desde configuración de cámaras"""

    @staticmethod
    def build_rtsp_uri(camera_data: Dict) -> str:
        """
        Construye la URI RTSP completa desde los datos de la cámara

        Args:
            camera_data: Diccionario con datos de la cámara desde la API
                - cam_ip: IP de la cámara
                - cam_port: Puerto RTSP
                - cam_user: Usuario
                - cam_password: Contraseña
                - cam_rstp: Path del stream (ej: "Streaming/Channels/1")

        Returns:
            URI RTSP completa (ej: rtsp://admin:password@172.80.40.12:554/Streaming/Channels/1)

        Example:
            >>> camera = {
            ...     "cam_ip": "172.80.40.12",
            ...     "cam_port": 554,
            ...     "cam_user": "admin",
            ...     "cam_password": "Radimer01",
            ...     "cam_rstp": "Streaming/Channels/1"
            ... }
            >>> RTSPBuilder.build_rtsp_uri(camera)
            'rtsp://admin:Radimer01@172.80.40.12:554/Streaming/Channels/1'
        """
        ip = camera_data.get('cam_ip', '')
        port = camera_data.get('cam_port', 554)
        user = camera_data.get('cam_user', '')
        password = camera_data.get('cam_password', '')
        path = camera_data.get('cam_rstp', '').lstrip('/')

        if not ip:
            raise ValueError("cam_ip es requerido para construir URI RTSP")

        # URL encode de credenciales para caracteres especiales
        user_encoded = quote(user, safe='')
        password_encoded = quote(password, safe='')

        # Construir URI
        if user and password:
            uri = f"rtsp://{user_encoded}:{password_encoded}@{ip}:{port}/{path}"
        else:
            uri = f"rtsp://{ip}:{port}/{path}"

        return uri

    @staticmethod
    def validate_rtsp_uri(uri: str) -> bool:
        """
        Valida que la URI RTSP tenga el formato correcto

        Args:
            uri: URI RTSP a validar

        Returns:
            True si es válida, False en caso contrario
        """
        if not uri:
            return False

        if not uri.startswith('rtsp://'):
            return False

        # Verificar que tenga al menos IP:puerto
        parts = uri.replace('rtsp://', '').split('/')
        if not parts[0]:
            return False

        return True
