"""Selector de empresa: implementadora vigente por placa exacta (tarea 3.3).

Lee solo `intercambio.vista_empresa` por igualdad exacta de
`placa_norma`. Ordena la vigente primero (`activa` descendente, luego
autorizacion mas reciente); sin filas no hay dato (luego 404). La
coherencia de extranjeras la da el expediente (ver selector propietario).
"""
from aplicaciones.empresa.modelos import VistaEmpresa
from aplicaciones.vehiculos.selectores.selector_busqueda import alias_lectura

COLUMNAS_EMPRESA = (
    "placa_norma",
    "placa",
    "codigo_correlativo",
    "estado_aprobacion",
    "activa",
    "nombre_empresa",
    "numero_autorizacion",
    "esta_autorizada",
    "fecha_autorizacion",
)


def obtener_empresa(placa_norma: str) -> dict | None:
    """Obtiene la empresa vigente o None si la placa no tiene filas.

    Args:
        placa_norma: Placa ya normalizada (igualdad exacta, sin parciales).

    Returns:
        dict | None: Fila vigente (o ultima conocida) o None (luego 404).
    """
    return (
        VistaEmpresa.objects.using(alias_lectura())
        .filter(placa_norma=placa_norma)
        .order_by("-activa", "-fecha_autorizacion")
        .values(*COLUMNAS_EMPRESA)
        .first()
    )
