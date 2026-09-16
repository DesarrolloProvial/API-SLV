"""Enrutador de expediente y generales: GET por placa exacta (tarea 3.2)."""
from django.http import HttpRequest
from ninja import Router

from aplicaciones.auditoria.propagador_correlacion import obtener_codigo
from aplicaciones.seguridad.aplicador_limites import (
    LimiteExcedido,
    verificar_limite,
)
from aplicaciones.seguridad.errores_uniformes import (
    construir_error_limite_excedido,
    construir_error_no_autenticado,
    construir_error_no_encontrado,
    construir_error_sin_permiso,
)
from aplicaciones.seguridad.validador_jwks import TokenInvalido
from aplicaciones.seguridad.verificador_ambitos import (
    PermisoDenegado,
    autenticar_y_autorizar,
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
    response={
        200: EsquemaExpediente,
        401: EsquemaError,
        403: EsquemaError,
        404: EsquemaError,
        429: EsquemaError,
    },
    tags=["vehiculos"],
    summary="Expediente por placa exacta",
)
def ver_expediente(request: HttpRequest, placa: str):
    """Devuelve el expediente vigente o error uniforme.

    Exige `vehiculos.lectura`: 401 sin token, 403 sin ambito, 404 sin
    ficha; `vinculos` solo trae lo autorizado.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa exacta consultada.

    Returns:
        Tupla `(estado, cuerpo)` 200 con expediente o error uniforme.
    """
    codigo = obtener_codigo(request)
    try:
        reclamos, ambitos = autenticar_y_autorizar(request, "expediente")
    except TokenInvalido:
        return 401, construir_error_no_autenticado(codigo)
    except PermisoDenegado:
        return 403, construir_error_sin_permiso(codigo)
    try:
        verificar_limite(request, reclamos, "expediente")
    except LimiteExcedido as excedido:
        request.limite_reintento_en = excedido.reintentar_en
        return 429, construir_error_limite_excedido(codigo)
    fila, error = _fila_o_error(normalizar_placa(placa), codigo)
    if error is not None:
        return 404, error
    return 200, armar_expediente(fila, codigo, ambitos)


@enrutador.get(
    "/{placa}/expediente/generales",
    response={
        200: EsquemaGenerales,
        401: EsquemaError,
        403: EsquemaError,
        404: EsquemaError,
        429: EsquemaError,
    },
    tags=["vehiculos"],
    summary="Generales por placa exacta",
)
def ver_generales(request: HttpRequest, placa: str):
    """Devuelve los generales vigentes o error uniforme.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa exacta consultada.

    Returns:
        Tupla `(estado, cuerpo)` 200 con generales o error uniforme.
    """
    codigo = obtener_codigo(request)
    try:
        reclamos, ambitos = autenticar_y_autorizar(request, "generales")
    except TokenInvalido:
        return 401, construir_error_no_autenticado(codigo)
    except PermisoDenegado:
        return 403, construir_error_sin_permiso(codigo)
    try:
        verificar_limite(request, reclamos, "generales")
    except LimiteExcedido as excedido:
        request.limite_reintento_en = excedido.reintentar_en
        return 429, construir_error_limite_excedido(codigo)
    fila, error = _fila_o_error(normalizar_placa(placa), codigo)
    if error is not None:
        return 404, error
    return 200, armar_generales(fila, codigo, ambitos)
