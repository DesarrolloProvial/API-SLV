"""Errores uniformes del contrato de intercambio (seam minimo PR4).

La pieza completa (401/403/429, verificador de ambitos y aplicador de
limites) se cierra en la tarea 3.4; aqui solo vive el 404 uniforme que
exigen las tareas 3.1 y 3.2.
"""
from typing import Final

ERROR_NO_ENCONTRADO: Final[str] = "no_encontrado"
MENSAJE_NO_ENCONTRADO: Final[str] = "Recurso no encontrado."


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
