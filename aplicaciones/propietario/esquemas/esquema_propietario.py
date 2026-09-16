"""Esquemas de propietario (tarea 3.3)."""
from datetime import date

from ninja import Schema

from aplicaciones.vehiculos.esquemas.esquema_expediente import EsquemaVinculos


class EsquemaPropietarioDatos(Schema):
    """Titularidad vigente minima (sin personales: van por convenio)."""

    nombre_empresa: str | None = None
    vigente_desde: date | None = None
    vigente_hasta: date | None = None


class EsquemaPropietario(Schema):
    """Respuesta 200 de propietario por placa exacta."""

    codigo_correlacion: str
    placa: str
    propietario: EsquemaPropietarioDatos
    vinculos: EsquemaVinculos
