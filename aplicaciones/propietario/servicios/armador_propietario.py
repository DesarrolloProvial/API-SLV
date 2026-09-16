"""Armado de propietario desde la fila vigente (tarea 3.3).

Mapeo puro fila -> respuesta. Reutiliza `construir_vinculos` del nucleo
para no duplicar las rutas del expediente.
"""


def armar_propietario(fila: dict, codigo_correlacion: str, vinculos: dict) -> dict:
    """Arma la respuesta de propietario con vinculos del expediente.

    Args:
        fila: Fila del selector vigente (vista_propietario).
        codigo_correlacion: Codigo de correlacion de la peticion.
        vinculos: Vinculos ya construidos para la placa.

    Returns:
        dict: Propietario con `propietario` y `vinculos`.
    """
    return {
        "codigo_correlacion": codigo_correlacion,
        "placa": fila.get("placa") or fila.get("placa_norma") or "",
        "propietario": {
            "nombre_empresa": fila.get("nombre_empresa"),
            "vigente_desde": fila.get("vigente_desde"),
            "vigente_hasta": fila.get("vigente_hasta"),
        },
        "vinculos": vinculos,
    }
