"""Servicios del contexto historial (paginado con cursor, sin E/S ni BD directa)."""
from aplicaciones.historial.servicios.servicio_historial import (
    TOPE_HISTORIAL,
    armar_periodo,
    armar_respuesta_historial,
    paginar_historial,
)

__all__ = [
    "TOPE_HISTORIAL",
    "armar_periodo",
    "armar_respuesta_historial",
    "paginar_historial",
]
