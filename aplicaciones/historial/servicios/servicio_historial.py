"""Servicio paginado del historial con cursor opaco (tarea 3.3).

Mismo patron que refrendos: tope bajo de dia 0, `tope + 1` sin conteos,
cursor ligado a la placa. El motivo de baja solo sale como codigo
convenido (detalle y contexto excluidos por construccion en la vista).
"""
from typing import Final

from aplicaciones.historial.selectores.selector_historial import listar_historial
from aplicaciones.seguridad.cursor_opaco import (
    CursorInvalido,
    decodificar_cursor,
    emitir_cursor,
)

#: Tope de dia 0; calibrar en convenio (ver 3.4).
TOPE_HISTORIAL: Final[int] = 10


def paginar_historial(
    placa_norma: str, cursor: str | None, tope: int = TOPE_HISTORIAL
) -> tuple[list[dict], str | None]:
    """Pagina periodos del historial con cursor opaco ligado a la placa.

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
    filas = listar_historial(placa_norma, desplazamiento, tope + 1)
    pagina = [armar_periodo(fila) for fila in filas[:tope]]
    siguiente = None
    if len(filas) > tope:
        siguiente = emitir_cursor(placa_norma, desplazamiento + tope)
    return pagina, siguiente


def armar_periodo(fila: dict) -> dict:
    """Arma un periodo sin detalles internos de baja.

    Args:
        fila: Fila del selector (vista_historial).

    Returns:
        dict: Periodo con correlativo, vigencia y empresa implementadora.
    """
    return {
        "codigo_correlativo": fila.get("codigo_correlativo"),
        "estado_aprobacion": fila.get("estado_aprobacion"),
        "activa": fila.get("activa"),
        "vigente_desde": fila.get("vigente_desde"),
        "fecha_baja": fila.get("fecha_baja"),
        "motivo_baja_codigo": fila.get("motivo_baja_codigo"),
        "empresa_implementadora": fila.get("empresa_implementadora"),
    }


def armar_respuesta_historial(
    placa: str,
    elementos: list[dict],
    cursor_siguiente: str | None,
    codigo_correlacion: str,
    vinculos: dict,
) -> dict:
    """Arma la respuesta paginada del historial.

    Args:
        placa: Placa para la respuesta (la original, no la norma).
        elementos: Periodos ya armados de esta pagina.
        cursor_siguiente: Token para la siguiente pagina (None si es ultima).
        codigo_correlacion: Codigo de correlacion de la peticion.
        vinculos: Vinculos ya construidos para la placa.

    Returns:
        dict: Respuesta con `historial`, `cursor_siguiente` y `vinculos`.
    """
    return {
        "codigo_correlacion": codigo_correlacion,
        "placa": placa,
        "historial": elementos,
        "cursor_siguiente": cursor_siguiente,
        "vinculos": vinculos,
    }


__all__ = [
    "TOPE_HISTORIAL",
    "armar_periodo",
    "armar_respuesta_historial",
    "paginar_historial",
]
