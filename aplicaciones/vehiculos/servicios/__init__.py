"""Servicios puros del contexto vehiculos (sin E/S ni BD)."""
from aplicaciones.vehiculos.servicios.armador_expediente import (
    armar_expediente,
    armar_generales,
    construir_vinculos,
)
from aplicaciones.vehiculos.servicios.normalizador_placa import normalizar_placa
from aplicaciones.vehiculos.servicios.resolutor_candidatas import (
    TOPE_CANDIDATAS,
    extraer_sufijo_y_tipo,
    resolver_por_sufijo_y_tipo,
)

__all__ = [
    "TOPE_CANDIDATAS",
    "armar_expediente",
    "armar_generales",
    "construir_vinculos",
    "extraer_sufijo_y_tipo",
    "normalizar_placa",
    "resolver_por_sufijo_y_tipo",
]
