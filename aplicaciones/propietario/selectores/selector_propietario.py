"""Selector de propietario: titularidad vigente por placa exacta (tarea 3.3).

Lee solo `intercambio.vista_propietario` por igualdad exacta de
`placa_norma`. Toma la vigente (`vigente_hasta` nula o futura,
la mas reciente); sin vigente no hay dato (el llamador da 404).
La coherencia de extranjeras la da el expediente: el enrutador verifica
primero la ficha exacta, que ya trata la extranjera no autorizada como
inexistente.
"""
from datetime import date

from django.db.models import Q

from aplicaciones.propietario.modelos import VistaPropietario
from aplicaciones.vehiculos.selectores.selector_busqueda import alias_lectura

COLUMNAS_PROPIETARIO = (
    "placa_norma",
    "placa",
    "vigente_desde",
    "vigente_hasta",
    "nombre_empresa",
)


def obtener_propietario(placa_norma: str) -> dict | None:
    """Obtiene la titularidad vigente o None si no hay vigente.

    Args:
        placa_norma: Placa ya normalizada (igualdad exacta, sin parciales).

    Returns:
        dict | None: Fila vigente o None (luego 404 uniforme).
    """
    hoy = date.today()
    return (
        VistaPropietario.objects.using(alias_lectura())
        .filter(
            placa_norma=placa_norma,
        )
        .filter(Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy))
        .order_by("-vigente_desde")
        .values(*COLUMNAS_PROPIETARIO)
        .first()
    )
