"""Selector de busqueda: candidatas por sufijo entre activos (tarea 3.1).

Lee solo `intercambio.vista_busqueda`. Orden determinista
`placa_norma ASC`; trae `tope + 1` para detectar `truncado`
sin conteos. Sin `icontains`, sin `page/limit`.

Decision de extranjeras (spec consulta, CRITICO 1 / ADVERTENCIA 1):
las extranjeras SOLO resuelven por igualdad exacta de placa completa
y solo si el convenio las autoriza (`PERMITIR_PLACAS_EXTRANJERAS=1`).
Por eso `buscar_por_sufijo` excluye SIEMPRE `tipo="extranjera"`
(aun con el flag ON); la via exacta es `obtener_extranjera_exacta`.
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


def buscar_por_sufijo(
    sufijo: str, tipo_letra: str, tope: int | None = None
) -> list[dict]:
    """Busca candidatas activas por sufijo6 mas primera letra.

    Nunca devuelve extranjeras: se excluyen siempre por
    `tipo="extranjera"` (con o sin convenio). La extranjera
    autorizada solo resuelve por exacta en `obtener_extranjera_exacta`.

    Args:
        sufijo: Ultimos 6 ya validados (`[0-9]{3}[A-Z]{3}`).
        tipo_letra: Primera letra consultada (un tipo nunca ve otro).
        tope: Maximo convenido (None = central `TOPE_CANDIDATAS`).

    Returns:
        list[dict]: Hasta `tope + 1` filas ordenadas como contrato.
    """
    from aplicaciones.vehiculos.servicios.resolutor_candidatas import tope_vigente

    tope = tope_vigente(tope)
    consulta = VistaBusqueda.objects.using(alias_lectura()).filter(
        placa_sufijo6=sufijo,
        placa_norma__startswith=tipo_letra,
        activa=True,
    )
    consulta = consulta.exclude(tipo="extranjera")
    return list(
        consulta.order_by("placa_norma").values(*COLUMNAS_CANDIDATA)[
            : tope + 1
        ]
    )


def obtener_extranjera_exacta(placa_norma: str) -> dict | None:
    """Obtiene la extranjera activa por igualdad exacta o None.

    Solo resuelve si el convenio autoriza extranjeras
    (`PERMITIR_PLACAS_EXTRANJERAS=1`); con el flag apagado (defecto)
    es como si no existiera (404 uniforme en el llamador). No acepta
    sufijos ni parciales: exige `placa_norma` completa ya normalizada.

    Args:
        placa_norma: Placa ya normalizada (igualdad exacta).

    Returns:
        dict | None: Fila candidata o None (inexistente, no activa,
            no extranjera o convenio sin autorizacion).
    """
    if not placa_norma:
        return None
    if not getattr(settings, "PERMITIR_PLACAS_EXTRANJERAS", False):
        return None
    return (
        VistaBusqueda.objects.using(alias_lectura())
        .filter(placa_norma=placa_norma, activa=True, tipo="extranjera")
        .values(*COLUMNAS_CANDIDATA)
        .first()
    )


def alias_lectura() -> str:
    """Devuelve el alias de lectura (el espejo en produccion).

    Returns:
        str: Alias Django configurado en `ALIAS_ESPEJO`.
    """
    return getattr(settings, "ALIAS_ESPEJO", "default")
