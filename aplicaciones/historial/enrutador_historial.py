"""Enrutador del historial: GET paginado con cursor opaco (tarea 3.3)."""
from django.http import HttpRequest
from ninja import Router

from aplicaciones.auditoria.propagador_correlacion import obtener_codigo
from aplicaciones.historial.esquemas.esquema_historial import EsquemaRespuestaHistorial
from aplicaciones.historial.servicios.servicio_historial import (
    armar_respuesta_historial,
    paginar_historial,
)
from aplicaciones.seguridad.aplicador_limites import (
    LimiteExcedido,
    verificar_limite,
)
from aplicaciones.seguridad.cursor_opaco import CursorInvalido
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
from aplicaciones.vehiculos.selectores.selector_expediente import (
    obtener_por_placa_exacta,
)
from aplicaciones.vehiculos.servicios.armador_expediente import construir_vinculos
from aplicaciones.vehiculos.servicios.normalizador_placa import normalizar_placa

# Nota: el primer parametro se llama `request` por exigencia de Ninja.
enrutador = Router()


@enrutador.get(
    "/{placa}/expediente/historial",
    response={
        200: EsquemaRespuestaHistorial,
        401: EsquemaError,
        403: EsquemaError,
        404: EsquemaError,
        429: EsquemaError,
    },
    tags=["historial"],
    summary="Historial paginado con cursor opaco",
)
def ver_historial(request: HttpRequest, placa: str, cursor: str | None = None):
    """Devuelve una pagina acotada de periodos o error uniforme.

    Exige base + `vehiculos.historial.lectura`: sin ambito no sale
    ningun dato (403 uniforme). Mismas reglas que refrendos: cursor
    invalido/manipulado/ajeno y extranjera no autorizada dan el mismo
    404 sin dato. Solo `cursor`.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa exacta consultada.
        cursor: Token opaco de la pagina anterior (None en la primera).

    Returns:
        Tupla `(estado, cuerpo)` 200 paginada o error uniforme.
    """
    codigo = obtener_codigo(request)
    try:
        reclamos, ambitos = autenticar_y_autorizar(request, "historial")
    except TokenInvalido:
        return 401, construir_error_no_autenticado(codigo)
    except PermisoDenegado:
        return 403, construir_error_sin_permiso(codigo)
    try:
        verificar_limite(request, reclamos, "historial")
    except LimiteExcedido as excedido:
        request.limite_reintento_en = excedido.reintentar_en
        return 429, construir_error_limite_excedido(codigo)
    norma = normalizar_placa(placa)
    if not norma:
        return 404, construir_error_no_encontrado(codigo)
    expediente = obtener_por_placa_exacta(norma)
    if expediente is None:
        return 404, construir_error_no_encontrado(codigo)
    try:
        elementos, siguiente = paginar_historial(norma, cursor)
    except CursorInvalido:
        return 404, construir_error_no_encontrado(codigo)
    return 200, armar_respuesta_historial(
        expediente.get("placa") or norma,
        elementos,
        siguiente,
        codigo,
        construir_vinculos(norma, ambitos),
    )
