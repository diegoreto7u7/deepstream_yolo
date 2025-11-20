"""
Detector de cruces de línea
Usa geometría vectorial (producto cruz) para detectar cruces
"""
import json
import os


class LineCrossingDetector:
    """Detecta cuando un objeto cruza una línea y determina la dirección"""

    def __init__(self, line_start=None, line_end=None, direccion_entrada="izquierda"):
        """
        Inicializa el detector

        Args:
            line_start (tuple): Punto inicial de la línea (x, y)
            line_end (tuple): Punto final de la línea (x, y)
            direccion_entrada (str): Lado de entrada ('izquierda' o 'derecha')
        """
        self.line_start = line_start
        self.line_end = line_end
        self.direccion_entrada = direccion_entrada

    def set_line(self, start, end):
        """
        Configura los puntos de la línea

        Args:
            start: Punto inicial (x, y)
            end: Punto final (x, y)
        """
        self.line_start = tuple(start) if start else None
        self.line_end = tuple(end) if end else None

    def set_direction(self, direccion):
        """
        Configura la dirección de entrada

        Args:
            direccion: 'izquierda' o 'derecha'
        """
        self.direccion_entrada = direccion

    def get_line_points(self):
        """
        Obtiene los puntos de la línea

        Returns:
            list: [line_start, line_end]
        """
        return [self.line_start, self.line_end] if self.line_start and self.line_end else []

    def punto_cruza_linea(self, x, y, prev_x, prev_y):
        """
        Detecta si un punto cruza la línea usando producto cruz

        Args:
            x (int): Posición X actual
            y (int): Posición Y actual
            prev_x (int): Posición X anterior
            prev_y (int): Posición Y anterior

        Returns:
            str: "ENTRADA", "SALIDA" o None
        """
        if not self.line_start or not self.line_end:
            return None

        def lado_linea(px, py):
            """Producto cruz para determinar lado"""
            return (self.line_end[0] - self.line_start[0]) * (py - self.line_start[1]) - \
                   (self.line_end[1] - self.line_start[1]) * (px - self.line_start[0])

        lado_actual = lado_linea(x, y)
        lado_anterior = lado_linea(prev_x, prev_y)

        # Detectar cruce (cambio de signo)
        if lado_actual * lado_anterior < 0:
            # Determinar dirección del cruce
            cruzando_izq_a_der = lado_anterior < 0 and lado_actual > 0
            cruzando_der_a_izq = lado_anterior > 0 and lado_actual < 0

            # Aplicar dirección configurada
            if self.direccion_entrada == "izquierda":
                if cruzando_izq_a_der:
                    return "ENTRADA"
                elif cruzando_der_a_izq:
                    return "SALIDA"
            else:  # derecha
                if cruzando_der_a_izq:
                    return "ENTRADA"
                elif cruzando_izq_a_der:
                    return "SALIDA"

        return None

    def tiene_linea_configurada(self):
        """
        Verifica si hay una línea configurada

        Returns:
            bool: True si line_start y line_end están definidos
        """
        return self.line_start is not None and self.line_end is not None
