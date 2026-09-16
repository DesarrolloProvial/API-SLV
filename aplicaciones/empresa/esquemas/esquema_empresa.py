"""Esquemas de empresa (tarea 3.3)."""
from datetime import date

from ninja import Schema

from aplicaciones.vehiculos.esquemas.esquema_expediente import EsquemaVinculos


class EsquemaEmpresaDatos(Schema):
    """Empresa implementadora vigente (sin personales ni representantes)."""

    nombre_empresa: str | None = None
    numero_autorizacion: str | None = None
    esta_autorizada: bool | None = None
    fecha_autorizacion: date | None = None
    codigo_correlativo: str | None = None
    estado_aprobacion: str | None = None
    activa: bool | None = None


class EsquemaEmpresa(Schema):
    """Respuesta 200 de empresa por placa exacta."""

    codigo_correlacion: str
    placa: str
    empresa: EsquemaEmpresaDatos
    vinculos: EsquemaVinculos
