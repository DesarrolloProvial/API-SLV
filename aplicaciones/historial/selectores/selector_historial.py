"""Selector de historial: pagina por placa exacta (tarea 3.3).

Lee solo `intercambio.vista_historial` por igualdad exacta de
`placa_norma`. Orden determinista `vigente_desde DESC,
codigo_correlativo DESC`; trae por rebanada sin conteos ni totales.
"""
from aplicaciones.historial.modelos import VistaHistorial
from aplicaciones.vehiculos.selectores.selector_busqueda import alias_lectura

COLUMNAS_HISTORIAL = (
    "placa_norma",
    "placa",
    "codigo_correlativo",
    "estado_aprobacion",
    "activa",
    "vigente_desde",
    "fecha_baja",
    "motivo_baja_codigo",
    "empresa_implementadora",
)


def listar_historial(
    placa_norma: str, desplazamiento: int, cantidad: int
) -> list[dict]:
    """Lista una rebanada ordenada de periodos del historial.

    Args:
        placa_norma: Placa ya normalizada (igualdad exacta).
        desplazamiento: Posicion inicial (>= 0, viene del cursor).
        cantidad: Maximo a traer (el servicio pide `tope + 1`).

    Returns:
        list[dict]: Hasta `cantidad` filas en orden del contrato.
    """
    return list(
        VistaHistorial.objects.using(alias_lectura())
        .filter(placa_norma=placa_norma)
        .order_by("-vigente_desde", "-codigo_correlativo")
        .values(*COLUMNAS_HISTORIAL)[desplazamiento : desplazamiento + cantidad]
    )
