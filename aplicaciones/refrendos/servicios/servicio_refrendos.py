"""Servicio paginado de refrendos con cursor opaco (tarea 3.3).

Tope bajo de dia 0 (`TOPE_REFERENDOS`); se calibra en convenio (3.4).
Pide `tope + 1` al selector para detectar `cursor_siguiente` sin conteos.
Cursor invalido -> `CursorInvalido` (el enrutador da el 404 uniforme).
"""
from typing import Final

from aplicaciones.refrendos.selectores.selector_refrendos import listar_refrendos
from aplicaciones.seguridad.cursor_opaco import (
    CursorInvalido,
    decodificar_cursor,
    emitir_cursor,
)

#: Tope de dia 0; calibrar en convenio (ver 3.4).
TOPE_REFERENDOS: Final[int] = 10


def paginar_refrendos(
    placa_norma: str, cursor: str | None, tope: int = TOPE_REFERENDOS
) -> tuple[list[dict], str | None]:
    """Pagina refrendos con cursor opaco ligado a la placa.

    Args:
        placa_norma: Placa ya normalizada (filtro del cursor y selector).
        cursor: Token opaco de la pagina anterior (None en la primera).
        tope: Maximo de elementos por pagina.

    Returns:
        Tupla `(elementos, cursor_siguiente)`; `cursor_siguiente` es None
            cuando no hay mas paginas. Sin totales.

    Raises:
        CursorInvalido: Si el cursor es ilegible, manipulado o de otra placa.
    """
    desplazamiento = 0
    if cursor:
        desplazamiento = decodificar_cursor(cursor, placa_norma)
    filas = listar_refrendos(placa_norma, desplazamiento, tope + 1)
    pagina = [armar_refrendo(fila) for fila in filas[:tope]]
    siguiente = None
    if len(filas) > tope:
        siguiente = emitir_cursor(placa_norma, desplazamiento + tope)
    return pagina, siguiente


def armar_refrendo(fila: dict) -> dict:
    """Arma un refrendo sin campos internos (observacion/motivo excluidos).

    Args:
        fila: Fila del selector (vista_refrendos).

    Returns:
        dict: Refrendo con codigo, fechas, estado y vigencia.
    """
    return {
        "codigo_refrendo": fila.get("codigo_refrendo"),
        "fecha_refrendo": fila.get("fecha_refrendo"),
        "fecha_vencimiento": fila.get("fecha_vencimiento"),
        "estado": fila.get("estado"),
        "vigencia_anios": fila.get("vigencia_anios"),
    }


def armar_respuesta_refrendos(
    placa: str,
    elementos: list[dict],
    cursor_siguiente: str | None,
    codigo_correlacion: str,
    vinculos: dict,
) -> dict:
    """Arma la respuesta paginada de refrendos.

    Args:
        placa: Placa para la respuesta (la original, no la norma).
        elementos: Refrendos ya armados de esta pagina.
        cursor_siguiente: Token para la siguiente pagina (None si es ultima).
        codigo_correlacion: Codigo de correlacion de la peticion.
        vinculos: Vinculos ya construidos para la placa.

    Returns:
        dict: Respuesta con `refrendos`, `cursor_siguiente` y `vinculos`.
    """
    return {
        "codigo_correlacion": codigo_correlacion,
        "placa": placa,
        "refrendos": elementos,
        "cursor_siguiente": cursor_siguiente,
        "vinculos": vinculos,
    }


__all__ = [
    "TOPE_REFERENDOS",
    "armar_refrendo",
    "armar_respuesta_refrendos",
    "paginar_refrendos",
]
