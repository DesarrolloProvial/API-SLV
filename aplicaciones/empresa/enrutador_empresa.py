"""Enrutador de empresa: GET por placa exacta (tarea 3.3)."""
from django.http import HttpRequest
from ninja import Router

from aplicaciones.auditoria.propagador_correlacion import obtener_codigo
from aplicaciones.empresa.esquemas.esquema_empresa import EsquemaEmpresa
from aplicaciones.empresa.selectores.selector_empresa import obtener_empresa
from aplicaciones.empresa.servicios.armador_empresa import armar_empresa
from aplicaciones.seguridad.errores_uniformes import (
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
    "/{placa}/expediente/empresa",
    response={
        200: EsquemaEmpresa,
        401: EsquemaError,
        403: EsquemaError,
        404: EsquemaError,
    },
    tags=["empresa"],
    summary="Empresa vigente por placa exacta",
)
def ver_empresa(request: HttpRequest, placa: str):
    """Devuelve la empresa vigente o error uniforme.

    Exige base + `vehiculos.empresa.lectura`: sin ambito no sale ningun
    dato (403 uniforme).

    La extranjera no autorizada se comporta como inexistente: la
    verificacion del expediente ya la filtra antes del subrecurso.

    Args:
        request: Peticion HTTP con codigo de correlacion.
        placa: Placa exacta consultada.

    Returns:
        Tupla `(estado, cuerpo)` 200 con empresa o error uniforme.
    """
    codigo = obtener_codigo(request)
    try:
        _, ambitos = autenticar_y_autorizar(request, "empresa")
    except TokenInvalido:
        return 401, construir_error_no_autenticado(codigo)
    except PermisoDenegado:
        return 403, construir_error_sin_permiso(codigo)
    norma = normalizar_placa(placa)
    if not norma:
        return 404, construir_error_no_encontrado(codigo)
    if obtener_por_placa_exacta(norma) is None:
        return 404, construir_error_no_encontrado(codigo)
    fila = obtener_empresa(norma)
    if fila is None:
        return 404, construir_error_no_encontrado(codigo)
    return 200, armar_empresa(fila, codigo, construir_vinculos(norma, ambitos))
