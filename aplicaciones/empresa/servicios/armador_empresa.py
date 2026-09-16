"""Armado de empresa desde la fila vigente (tarea 3.3).

Mapeo puro fila -> respuesta. Reutiliza los vinculos del nucleo.
"""


def armar_empresa(fila: dict, codigo_correlacion: str, vinculos: dict) -> dict:
    """Arma la respuesta de empresa con vinculos del expediente.

    Args:
        fila: Fila del selector vigente (vista_empresa).
        codigo_correlacion: Codigo de correlacion de la peticion.
        vinculos: Vinculos ya construidos para la placa.

    Returns:
        dict: Empresa con `empresa` y `vinculos`.
    """
    return {
        "codigo_correlacion": codigo_correlacion,
        "placa": fila.get("placa") or fila.get("placa_norma") or "",
        "empresa": {
            "nombre_empresa": fila.get("nombre_empresa"),
            "numero_autorizacion": fila.get("numero_autorizacion"),
            "esta_autorizada": fila.get("esta_autorizada"),
            "fecha_autorizacion": fila.get("fecha_autorizacion"),
            "codigo_correlativo": fila.get("codigo_correlativo"),
            "estado_aprobacion": fila.get("estado_aprobacion"),
            "activa": fila.get("activa"),
        },
        "vinculos": vinculos,
    }
