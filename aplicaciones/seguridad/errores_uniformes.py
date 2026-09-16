"""Errores uniformes del contrato de intercambio (tarea 3.4).

Todos los errores llevan `error`, `mensaje` y `codigo_correlacion`; nunca
detallan la causa interna ni los umbrales. `no-store` y la cabecera
`X-Codigo-Correlacion` los pone el middleware en TODA respuesta.
"""
from typing import Final

ERROR_NO_ENCONTRADO: Final[str] = "no_encontrado"
MENSAJE_NO_ENCONTRADO: Final[str] = "Recurso no encontrado."

ERROR_NO_AUTENTICADO: Final[str] = "no_autenticado"
MENSAJE_NO_AUTENTICADO: Final[str] = "Autenticacion requerida."

ERROR_SIN_PERMISO: Final[str] = "sin_permiso"
MENSAJE_SIN_PERMISO: Final[str] = "Sin permiso para este recurso."

ERROR_LIMITE_EXCEDIDO: Final[str] = "limite_excedido"
MENSAJE_LIMITE_EXCEDIDO: Final[str] = (
    "Limite de consultas excedido. Intente de nuevo mas tarde."
)


def construir_error_no_encontrado(codigo_correlacion: str) -> dict:
    """Construye el cuerpo 404 uniforme sin senal de causa.

    Args:
        codigo_correlacion: Codigo de correlacion de la peticion.

    Returns:
        dict: Cuerpo con `error`, `mensaje` y `codigo_correlacion`.
    """
    return {
        "error": ERROR_NO_ENCONTRADO,
        "mensaje": MENSAJE_NO_ENCONTRADO,
        "codigo_correlacion": codigo_correlacion,
    }


def construir_error_no_autenticado(codigo_correlacion: str) -> dict:
    """Construye el cuerpo 401 uniforme (token ausente o invalido).

    Args:
        codigo_correlacion: Codigo de correlacion de la peticion.

    Returns:
        dict: Cuerpo 401 sin detallar la causa interna.
    """
    return {
        "error": ERROR_NO_AUTENTICADO,
        "mensaje": MENSAJE_NO_AUTENTICADO,
        "codigo_correlacion": codigo_correlacion,
    }


def construir_error_sin_permiso(codigo_correlacion: str) -> dict:
    """Construye el cuerpo 403 uniforme (ambito insuficiente).

    Args:
        codigo_correlacion: Codigo de correlacion de la peticion.

    Returns:
        dict: Cuerpo 403 sin entregar ningun dato del recurso.
    """
    return {
        "error": ERROR_SIN_PERMISO,
        "mensaje": MENSAJE_SIN_PERMISO,
        "codigo_correlacion": codigo_correlacion,
    }


def construir_error_limite_excedido(codigo_correlacion: str) -> dict:
    """Construye el cuerpo 429 uniforme (cuota excedida).

    El `Retry-After` viaja como cabecera (lo pone el middleware); aqui
    solo va el cuerpo, sin filtrar umbrales.

    Args:
        codigo_correlacion: Codigo de correlacion de la peticion.

    Returns:
        dict: Cuerpo 429 sin detalle de la politica interna.
    """
    return {
        "error": ERROR_LIMITE_EXCEDIDO,
        "mensaje": MENSAJE_LIMITE_EXCEDIDO,
        "codigo_correlacion": codigo_correlacion,
    }
