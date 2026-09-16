"""Selectores de lectura del contexto vehiculos (ORM, sin escritura)."""
from aplicaciones.vehiculos.selectores.selector_busqueda import buscar_por_sufijo
from aplicaciones.vehiculos.selectores.selector_expediente import (
    obtener_por_placa_exacta,
)

__all__ = ["buscar_por_sufijo", "obtener_por_placa_exacta"]
