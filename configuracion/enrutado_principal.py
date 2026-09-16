"""Enrutado principal: solo delega a enrutadores por contexto."""
import ipaddress

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import path
from ninja import NinjaAPI

from aplicaciones.auditoria.propagador_correlacion import obtener_codigo
from aplicaciones.seguridad.errores_uniformes import (
    construir_error_no_encontrado,
)
from aplicaciones.empresa.enrutador_empresa import (
    enrutador as enrutador_empresa,
)
from aplicaciones.historial.enrutador_historial import (
    enrutador as enrutador_historial,
)
from aplicaciones.propietario.enrutador_propietario import (
    enrutador as enrutador_propietario,
)
from aplicaciones.refrendos.enrutador_refrendos import (
    enrutador as enrutador_refrendos,
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


def vista_metricas(peticion):
    """Expone las metricas Prometheus solo a la red interna.

    Sin token (el raspado no se autentica); el control es la red:
    nginx solo la proxya en red interna y esta vista niega con 404
    cualquier origen fuera de las redes privadas o de
    `REDES_METRICAS_PERMITIDAS`.

    Args:
        peticion: Peticion HTTP entrante.

    Returns:
        HttpResponse: Texto Prometheus o 404 uniforme sin fuga.
    """
    if not _es_red_interna(peticion):
        return JsonResponse(
            construir_error_no_encontrado(obtener_codigo(peticion)), status=404
        )
    from aplicaciones.auditoria.metricas_negocio import exponer_metricas

    return HttpResponse(
        exponer_metricas(),
        content_type="text/plain; version=0.0.4; charset=utf-8",
    )


def _es_red_interna(peticion) -> bool:
    """Indica si el origen pertenece a la red interna permitida.

    Args:
        peticion: Peticion HTTP con `REMOTE_ADDR`.

    Returns:
        bool: True si es IP privada o de las redes configuradas.
    """
    try:
        origen = ipaddress.ip_address(
            peticion.META.get("REMOTE_ADDR", "").split(",")[0].strip()
        )
    except ValueError:
        return False
    if origen.is_private or origen.is_loopback:
        return True
    for red in getattr(settings, "REDES_METRICAS_PERMITIDAS", []) or []:
        try:
            if origen in ipaddress.ip_network(red, strict=False):
                return True
        except ValueError:
            continue
    return False


api = NinjaAPI(
    title="Intercambio de vehiculos",
    version="1.0.0",
    # Seco: el borde solo expone `GET /api/v1/vehiculos/*`; la UI
    # interactiva no sale a internet (se consulta `openapi.json`).
    docs_url=None,
)
api.add_router("/v1/vehiculos", enrutador_busqueda)
api.add_router("/v1/vehiculos", enrutador_expediente)
api.add_router("/v1/vehiculos", enrutador_propietario)
api.add_router("/v1/vehiculos", enrutador_empresa)
api.add_router("/v1/vehiculos", enrutador_refrendos)
api.add_router("/v1/vehiculos", enrutador_historial)


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
    path("metricas", vista_metricas, name="metricas"),
    path("api/", api.urls),
]
