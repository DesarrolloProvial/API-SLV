"""Esquemas del contexto vehiculos (fuente del OpenAPI)."""
from aplicaciones.vehiculos.esquemas.esquema_busqueda import (
    EsquemaCandidata,
    EsquemaError,
    EsquemaRespuestaBusqueda,
    EsquemaVinculoExpediente,
)
from aplicaciones.vehiculos.esquemas.esquema_expediente import (
    EsquemaExpediente,
    EsquemaGenerales,
    EsquemaRefrendoVigente,
    EsquemaVehiculo,
    EsquemaVinculacion,
    EsquemaVinculos,
)

__all__ = [
    "EsquemaCandidata",
    "EsquemaError",
    "EsquemaExpediente",
    "EsquemaGenerales",
    "EsquemaRefrendoVigente",
    "EsquemaRespuestaBusqueda",
    "EsquemaVehiculo",
    "EsquemaVinculacion",
    "EsquemaVinculoExpediente",
    "EsquemaVinculos",
]
