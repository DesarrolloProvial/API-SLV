"""Selector de busqueda: candidatas por sufijo entre activos (tarea 3.1).

Lee solo `intercambio.vista_busqueda`. Orden determinista
`activa DESC, placa_norma ASC`; trae `tope + 1` para detectar `truncado`
sin conteos. Sin `icontains`, sin `page/limit`.
"""
from django.conf import settings

from aplicaciones.vehiculos.modelos import VistaBusqueda

COLUMNAS_CANDIDATA = (
    "placa_norma",
    "placa",
    "marca",
    "linea",
    "modelo",
    "empresa_implementadora",
)


def buscar_por_sufijo(sufijo: str, tipo_letra: str, tope: int) -> list[dict]:
    """Busca candidatas activas por sufijo6 mas primera letra.

    Args:
        sufijo: Ultimos 6 ya validados (`[0-9]{3}[A-Z]{3}`).
        tipo_letra: Primera letra consultada (un tipo nunca ve otro).
        tope: Maximo convenido; se trae uno extra para el `truncado`.

    Returns:
        list[dict]: Hasta `tope + 1` filas ordenadas como contrato.
    """
    consulta = VistaBusqueda.objects.using(alias_lectura()).filter(
        placa_sufijo6=sufijo,
        placa_norma__startswith=tipo_letra,
        activa=True,
    )
    if not getattr(settings, "PERMITIR_PLACAS_EXTRANJERAS", False):
        consulta = consulta.exclude(tipo="extranjera")
    return list(
        consulta.order_by("-activa", "placa_norma").values(*COLUMNAS_CANDIDATA)[
            : tope + 1
        ]
    )


def alias_lectura() -> str:
    """Devuelve el alias de lectura (el espejo en produccion).

    Returns:
        str: Alias Django configurado en `ALIAS_ESPEJO`.
    """
    return getattr(settings, "ALIAS_ESPEJO", "default")
