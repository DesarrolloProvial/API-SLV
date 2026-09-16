"""Esquemas de refrendos (tarea 3.3)."""
from datetime import date

from ninja import Schema

from aplicaciones.vehiculos.esquemas.esquema_expediente import EsquemaVinculos


class EsquemaRefrendo(Schema):
    """Refrendo sin observacion ni motivo (excluidos por construccion)."""

    codigo_refrendo: str | None = None
    fecha_refrendo: date | None = None
    fecha_vencimiento: date | None = None
    estado: str | None = None
    vigencia_anios: int | None = None


class EsquemaRespuestaRefrendos(Schema):
    """Respuesta 200 paginada: elementos mas cursor, sin totales."""

    codigo_correlacion: str
    placa: str
    refrendos: list[EsquemaRefrendo]
    cursor_siguiente: str | None = None
    vinculos: EsquemaVinculos
