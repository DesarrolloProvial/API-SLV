"""Selector de refrendos: pagina por placa exacta (tarea 3.3).

Lee solo `intercambio.vista_refrendos` por igualdad exacta de
`placa_norma`. Orden determinista `fecha_refrendo DESC,
codigo_refrendo DESC`; trae por rebanada (`desplazamiento: +cantidad`)
sin conteos ni totales. El cursor opaco lo resuelve el servicio.
"""
from aplicaciones.refrendos.modelos import VistaRefrendo
from aplicaciones.vehiculos.selectores.selector_busqueda import alias_lectura

COLUMNAS_REFRENDO = (
    "placa_norma",
    "placa",
    "codigo_refrendo",
    "fecha_refrendo",
    "fecha_vencimiento",
    "estado",
    "vigencia_anios",
)


def listar_refrendos(
    placa_norma: str, desplazamiento: int, cantidad: int
) -> list[dict]:
    """Lista una rebanada ordenada de refrendos.

    Args:
        placa_norma: Placa ya normalizada (igualdad exacta).
        desplazamiento: Posicion inicial (>= 0, viene del cursor).
        cantidad: Maximo a traer (el servicio pide `tope + 1`).

    Returns:
        list[dict]: Hasta `cantidad` filas en orden del contrato.
    """
    return list(
        VistaRefrendo.objects.using(alias_lectura())
        .filter(placa_norma=placa_norma)
        .order_by("-fecha_refrendo", "-codigo_refrendo")
        .values(*COLUMNAS_REFRENDO)[desplazamiento : desplazamiento + cantidad]
    )
