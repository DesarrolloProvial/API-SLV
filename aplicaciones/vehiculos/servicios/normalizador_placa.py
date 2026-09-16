"""Normalizacion de placas en servidor (PLAN 10).

Recorta, mayuscula y quita espacios y guiones. Nunca rechaza: una entrada
invalida se normaliza a algo que no coincide y termina en 404 uniforme.
"""
import re

_LIMPIEZA = re.compile(r"[\s\-]+")


def normalizar_placa(placa_cruda: str | None) -> str:
    """Normaliza una placa cruda a su forma canonica.

    Args:
        placa_cruda: Valor recibido en el parametro `placa`.

    Returns:
        str: Placa en mayusculas sin espacios ni guiones ("" si no hay nada).
    """
    if not placa_cruda:
        return ""
    return _LIMPIEZA.sub("", placa_cruda.strip().upper())
