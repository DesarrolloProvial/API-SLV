"""Enrutador de busqueda: GET buscar (delgado, tarea 3.1)."""
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
from aplicaciones.vehiculos.esquemas.esquema_busqueda import (
    EsquemaError,
    EsquemaRespuestaBusqueda,
)
from aplicaciones.vehiculos.selectores.selector_busqueda import buscar_por_sufijo
from aplicaciones.vehiculos.servicios.normalizador_placa import normalizar_placa
from aplicaciones.vehiculos.servicios.resolutor_candidatas import (
    extraer_sufijo_y_tipo,
    resolver_por_sufijo_y_tipo,
)

# Nota: el primer parametro se llama `request` por exigencia de Ninja
# (solo omite del esquema el parametro con ese nombre literal).


enrutador = Router()


@enrutador.get(
    "/buscar",
    response={
        200: EsquemaRespuestaBusqueda,
        401: EsquemaError,
        403: EsquemaError,
        404: EsquemaError,
        429: EsquemaError,
    },
    tags=["vehiculos"],
    summary="Buscar candidatas por placa completa",
)
def buscar_vehiculos(request: HttpRequest, placa: str | None = None):
    """Busca por placa completa; 404 uniforme si no resuelve.

    Exige `vehiculos.lectura`: sin token -> 401, sin ambito -> 403,
    ambos uniformes y sin dato.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa completa del consumidor (unica via).

    Returns:
        Tupla `(estado, cuerpo)` 200 con candidatas o error uniforme.
    """
    codigo = obtener_codigo(request)
    try:
        reclamos, _ambitos = autenticar_y_autorizar(request, "buscar")
    except TokenInvalido:
        return 401, construir_error_no_autenticado(codigo)
    except PermisoDenegado:
        return 403, construir_error_sin_permiso(codigo)
    try:
        verificar_limite(request, reclamos, "buscar")
    except LimiteExcedido as excedido:
        request.limite_reintento_en = excedido.reintentar_en
        return 429, construir_error_limite_excedido(codigo)
    norma = normalizar_placa(placa)
    extraccion = extraer_sufijo_y_tipo(norma)
    if extraccion is None:
        return 404, construir_error_no_encontrado(codigo)
    sufijo, tipo_letra = extraccion
    filas = buscar_por_sufijo(sufijo, tipo_letra)
    if not filas:
        return 404, construir_error_no_encontrado(codigo)
    candidatas, truncado = resolver_por_sufijo_y_tipo(
        sufijo, tipo_letra, filas
    )
    if not candidatas:
        return 404, construir_error_no_encontrado(codigo)
    return 200, {
        "codigo_correlacion": codigo,
        "placa": norma,
        "candidatas": candidatas,
        "truncado": truncado,
    }
