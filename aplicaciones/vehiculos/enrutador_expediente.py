"""Enrutador de expediente y generales: GET por placa exacta (tarea 3.2)."""
from django.http import HttpRequest
from ninja import Router

from aplicaciones.auditoria.propagador_correlacion import obtener_codigo
from aplicaciones.seguridad.errores_uniformes import (
    construir_error_no_encontrado,
)
from aplicaciones.vehiculos.esquemas.esquema_busqueda import EsquemaError
from aplicaciones.vehiculos.esquemas.esquema_expediente import (
    EsquemaExpediente,
    EsquemaGenerales,
)
from aplicaciones.vehiculos.selectores.selector_expediente import (
    obtener_por_placa_exacta,
)
from aplicaciones.vehiculos.servicios.armador_expediente import (
    armar_expediente,
    armar_generales,
)
from aplicaciones.vehiculos.servicios.normalizador_placa import normalizar_placa

# Nota: el primer parametro se llama `request` por exigencia de Ninja
# (solo omite del esquema el parametro con ese nombre literal).
enrutador = Router()


def _fila_o_error(norma: str, codigo: str):
    """Busca la ficha exacta o construye el 404 uniforme.

    Args:
        norma: Placa ya normalizada (igualdad exacta).
        codigo: Codigo de correlacion de la peticion.

    Returns:
        Tupla `(fila, error_404)` con uno de los dos en None.
    """
    if not norma:
        return None, construir_error_no_encontrado(codigo)
    fila = obtener_por_placa_exacta(norma)
    if fila is None:
        return None, construir_error_no_encontrado(codigo)
    return fila, None


@enrutador.get(
    "/{placa}/expediente",
    response={200: EsquemaExpediente, 404: EsquemaError},
    tags=["vehiculos"],
    summary="Expediente por placa exacta",
)
def ver_expediente(request: HttpRequest, placa: str):
    """Devuelve el expediente vigente o 404 uniforme.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa exacta consultada.

    Returns:
        Tupla `(estado, cuerpo)` 200 con expediente o 404 uniforme.
    """
    codigo = obtener_codigo(request)
    fila, error = _fila_o_error(normalizar_placa(placa), codigo)
    if error is not None:
        return 404, error
    return 200, armar_expediente(fila, codigo)


@enrutador.get(
    "/{placa}/expediente/generales",
    response={200: EsquemaGenerales, 404: EsquemaError},
    tags=["vehiculos"],
    summary="Generales por placa exacta",
)
def ver_generales(request: HttpRequest, placa: str):
    """Devuelve los generales vigentes o 404 uniforme.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa exacta consultada.

    Returns:
        Tupla `(estado, cuerpo)` 200 con generales o 404 uniforme.
    """
    codigo = obtener_codigo(request)
    fila, error = _fila_o_error(normalizar_placa(placa), codigo)
    if error is not None:
        return 404, error
    return 200, armar_generales(fila, codigo)
