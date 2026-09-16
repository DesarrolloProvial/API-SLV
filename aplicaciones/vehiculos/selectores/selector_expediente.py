"""Selector de expediente: ficha exacta entre activos (tarea 3.2).

Lee solo `intercambio.vista_expediente` por igualdad exacta de
`placa_norma`. Extranjeras solo si el convenio las autoriza
(`PERMITIR_PLACAS_EXTRANJERAS`); si no, es como si no existieran.
"""
from django.conf import settings

from aplicaciones.vehiculos.modelos import VistaExpediente
from aplicaciones.vehiculos.selectores.selector_busqueda import alias_lectura

COLUMNAS_EXPEDIENTE = tuple(f.name for f in VistaExpediente._meta.fields)


def obtener_por_placa_exacta(placa_norma: str) -> dict | None:
    """Obtiene la ficha vigente por placa exacta o None si no aplica.

    Args:
        placa_norma: Placa ya normalizada (igualdad exacta, sin parciales).

    Returns:
        dict | None: Fila del expediente o None (inexistente, no vigente
            o extranjera no autorizada: el llamador responde 404 uniforme).
    """
    fila = (
        VistaExpediente.objects.using(alias_lectura())
        .filter(placa_norma=placa_norma, activa=True)
        .values(*COLUMNAS_EXPEDIENTE)
        .first()
    )
    if fila is None:
        return None
    if fila.get("tipo_placa") == "extranjera" and not getattr(
        settings, "PERMITIR_PLACAS_EXTRANJERAS", False
    ):
        return None
    return fila
