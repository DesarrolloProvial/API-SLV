"""Esquemas de busqueda y del error uniforme (tarea 3.1)."""
from ninja import Schema


class EsquemaVinculoExpediente(Schema):
    """Vinculo hacia el expediente para desambiguar en dos pasos."""

    expediente: str


class EsquemaCandidata(Schema):
    """Ficha minima de una candidata del mismo tipo."""

    placa: str
    marca: str | None = None
    linea: str | None = None
    modelo: str | None = None
    empresa_implementadora: str | None = None
    vinculos: EsquemaVinculoExpediente


class EsquemaRespuestaBusqueda(Schema):
    """Respuesta 200 de buscar: candidatas mas `truncado` (sin totales)."""

    codigo_correlacion: str
    placa: str
    candidatas: list[EsquemaCandidata]
    truncado: bool


class EsquemaError(Schema):
    """Error uniforme en espanol con correlacion (p. ej. 404)."""

    error: str
    mensaje: str
    codigo_correlacion: str
