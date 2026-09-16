"""Esquemas del historial (tarea 3.3)."""
from datetime import date

from ninja import Schema

from aplicaciones.vehiculos.esquemas.esquema_expediente import EsquemaVinculos


class EsquemaPeriodoHistorial(Schema):
    """Periodo con baja solo como codigo convenido (sin detalle)."""

    codigo_correlativo: str | None = None
    estado_aprobacion: str | None = None
    activa: bool | None = None
    vigente_desde: date | None = None
    fecha_baja: date | None = None
    motivo_baja_codigo: str | None = None
    empresa_implementadora: str | None = None


class EsquemaRespuestaHistorial(Schema):
    """Respuesta 200 paginada: elementos mas cursor, sin totales."""

    codigo_correlacion: str
    placa: str
    historial: list[EsquemaPeriodoHistorial]
    cursor_siguiente: str | None = None
    vinculos: EsquemaVinculos
