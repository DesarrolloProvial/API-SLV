"""Enrutado principal: solo delega a enrutadores por contexto."""
from django.http import JsonResponse
from django.urls import path
from ninja import NinjaAPI

from aplicaciones.auditoria.propagador_correlacion import obtener_codigo
from aplicaciones.seguridad.errores_uniformes import (
    construir_error_no_encontrado,
)
from aplicaciones.empresa.enrutador_empresa import (
    enrutador as enrutador_empresa,
)
from aplicaciones.propietario.enrutador_propietario import (
    enrutador as enrutador_propietario,
)
from aplicaciones.vehiculos.enrutador_busqueda import (
    enrutador as enrutador_busqueda,
)
from aplicaciones.vehiculos.enrutador_expediente import (
    enrutador as enrutador_expediente,
)


def vista_salud(peticion):
    """Responde el estado interno del servicio.

    Args:
        peticion: Peticion HTTP entrante.

    Returns:
        JsonResponse: Estado correcto del servicio.
    """
    return JsonResponse({"estado": "correcto"})


api = NinjaAPI(title="Intercambio de vehiculos", version="1.0.0")
api.add_router("/v1/vehiculos", enrutador_busqueda)
api.add_router("/v1/vehiculos", enrutador_expediente)
api.add_router("/v1/vehiculos", enrutador_propietario)
api.add_router("/v1/vehiculos", enrutador_empresa)


def vista_no_encontrada(peticion, exception=None):
    """Ruta inexistente con el mismo 404 uniforme del contrato.

    Args:
        peticion: Peticion HTTP con codigo de correlacion.
        exception: Excepcion de Django (nombre exigido; no se usa).

    Returns:
        JsonResponse: 404 `no_encontrado` con correlacion.
    """
    _ = exception
    return JsonResponse(
        construir_error_no_encontrado(obtener_codigo(peticion)), status=404
    )


handler404 = vista_no_encontrada

urlpatterns = [
    path("salud", vista_salud, name="salud"),
    path("api/", api.urls),
]
