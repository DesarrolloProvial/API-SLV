"""Servicios del contexto refrendos (paginado con cursor, sin E/S ni BD directa)."""
from aplicaciones.refrendos.servicios.servicio_refrendos import (
    TOPE_REFERENDOS,
    armar_refrendo,
    armar_respuesta_refrendos,
    paginar_refrendos,
)

__all__ = [
    "TOPE_REFERENDOS",
    "armar_refrendo",
    "armar_respuesta_refrendos",
    "paginar_refrendos",
]
