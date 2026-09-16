"""Resolucion interna por sufijo mas filtro por tipo (PLAN 10/25).

El consumidor envia la placa completa; aqui se deriva el sufijo (ultimos
6, patron `[0-9]{3}[A-Z]{3}`) y el tipo (primera letra). Solo las
variantes del mismo tipo llegan a candidatas; un tipo distinto jamas
aparece. Sin conteos: `truncado` solo indica si hubo mas alla del tope.
"""
import re
from typing import Final

from django.conf import settings

PATRON_SUFIJO: Final = re.compile(r"[0-9]{3}[A-Z]{3}$")

#: Tope de dia 0 (calibrable por convenio via `TOPE_CANDIDATAS`).
TOPE_CANDIDATAS: Final[int] = 10


def tope_vigente(tope: int | None = None) -> int:
    """Resuelve el tope central (ajuste) o el de dia 0.

    Args:
        tope: Tope explicito (pruebas) o None para el central.

    Returns:
        int: Tope a aplicar.
    """
    if tope is not None:
        return tope
    return int(getattr(settings, "TOPE_CANDIDATAS", TOPE_CANDIDATAS))


def extraer_sufijo_y_tipo(placa_norma: str) -> tuple[str, str] | None:
    """Deriva (sufijo, tipo) o devuelve None si no hay sufijo valido.

    Args:
        placa_norma: Placa ya normalizada.

    Returns:
        Tupla `(sufijo6, primera_letra)` o None ante formato no resoluble.
    """
    if not placa_norma or len(placa_norma) < 6:
        return None
    sufijo = placa_norma[-6:]
    if not PATRON_SUFIJO.match(sufijo):
        return None
    return sufijo, placa_norma[0]


def resolver_por_sufijo_y_tipo(
    sufijo: str,
    tipo_letra: str,
    filas: list[dict],
    tope: int | None = None,
) -> tuple[list[dict], bool]:
    """Convierte filas del selector en candidatas del mismo tipo.

    Args:
        sufijo: Ultimos 6 ya validados (trazabilidad, no se re-deriva).
        tipo_letra: Primera letra consultada; filtra en defensa propia.
        filas: Filas ya ordenadas (`activa DESC, placa_norma ASC`).
        tope: Maximo de candidatas (None = central `TOPE_CANDIDATAS`).

    Returns:
        Tupla `(candidatas, truncado)`; `truncado` es True si hubo mas.
    """
    _ = sufijo
    tope = tope_vigente(tope)
    propias = [f for f in filas if (f.get("placa_norma") or "").startswith(tipo_letra)]
    return [armar_candidata(f) for f in propias[:tope]], len(propias) > tope


def armar_candidata(fila: dict) -> dict:
    """Arma la ficha minima de una candidata con su vinculo.

    Args:
        fila: Fila del selector de busqueda.

    Returns:
        dict: Candidata con `vinculos.expediente` para desambiguar.
    """
    placa = fila.get("placa_norma") or fila.get("placa") or ""
    return {
        "placa": fila.get("placa") or placa,
        "marca": fila.get("marca"),
        "linea": fila.get("linea"),
        "modelo": fila.get("modelo"),
        "empresa_implementadora": fila.get("empresa_implementadora"),
        "vinculos": {"expediente": f"/api/v1/vehiculos/{placa}/expediente"},
    }
