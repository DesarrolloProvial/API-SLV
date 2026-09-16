"""Enrutador de refrendos: GET paginado con cursor opaco (tarea 3.3)."""
from django.http import HttpRequest
from ninja import Router

from aplicaciones.auditoria.propagador_correlacion import obtener_codigo
from aplicaciones.refrendos.esquemas.esquema_refrendos import EsquemaRespuestaRefrendos
from aplicaciones.refrendos.servicios.servicio_refrendos import (
    armar_respuesta_refrendos,
    paginar_refrendos,
)
from aplicaciones.seguridad.cursor_opaco import CursorInvalido
from aplicaciones.seguridad.errores_uniformes import (
    construir_error_no_encontrado,
)
from aplicaciones.vehiculos.esquemas.esquema_busqueda import EsquemaError
from aplicaciones.vehiculos.selectores.selector_expediente import (
    obtener_por_placa_exacta,
)
from aplicaciones.vehiculos.servicios.armador_expediente import construir_vinculos
from aplicaciones.vehiculos.servicios.normalizador_placa import normalizar_placa

# Nota: el primer parametro se llama `request` por exigencia de Ninja.
enrutador = Router()


@enrutador.get(
    "/{placa}/expediente/refrendos",
    response={200: EsquemaRespuestaRefrendos, 404: EsquemaError},
    tags=["refrendos"],
    summary="Refrendos paginados con cursor opaco",
)
def ver_refrendos(request: HttpRequest, placa: str, cursor: str | None = None):
    """Devuelve una pagina acotada de refrendos o 404 uniforme.

    Cursor invalido, manipulado o de otra placa -> mismo 404 sin dato.
    Extranjera no autorizada -> mismo 404 (verifica expediente primero).
    Sin `page/limit` ni totales: solo `cursor` opcional.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa exacta consultada.
        cursor: Token opaco de la pagina anterior (None en la primera).

    Returns:
        Tupla `(estado, cuerpo)` 200 paginada o 404 uniforme.
    """
    codigo = obtener_codigo(request)
    norma = normalizar_placa(placa)
    if not norma:
        return 404, construir_error_no_encontrado(codigo)
    expediente = obtener_por_placa_exacta(norma)
    if expediente is None:
        return 404, construir_error_no_encontrado(codigo)
    try:
        elementos, siguiente = paginar_refrendos(norma, cursor)
    except CursorInvalido:
        return 404, construir_error_no_encontrado(codigo)
    return 200, armar_respuesta_refrendos(
        expediente.get("placa") or norma,
        elementos,
        siguiente,
        codigo,
        construir_vinculos(norma),
    )
