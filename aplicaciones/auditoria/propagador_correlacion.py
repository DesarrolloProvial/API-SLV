"""Propagacion del codigo de correlacion (seam minimo PR4).

Genera el `codigo_correlacion` (UUIDv7) por peticion, lo expone en
`peticion.codigo_correlacion` y marca toda respuesta con
`Cache-Control: no-store`. La propagacion completa (cabecera hacia el
borde, `application_name` en PostgreSQL y campos de registro) se cierra
en la tarea 3.4.
"""
import uuid


def generar_codigo_correlacion() -> str:
    """Genera un codigo de correlacion unico (UUIDv7).

    Returns:
        str: Codigo de correlacion en formato texto.
    """
    generador = getattr(uuid, "uuid7", None)
    return str(generador() if generador is not None else uuid.uuid4())


class MiddlewareCodigoCorrelacion:
    """Asocia codigo de correlacion y prohibe cache en cada respuesta."""

    def __init__(self, get_response):
        """Guarda el siguiente eslabon de la cadena.

        Args:
            get_response: Invocable del siguiente middleware o vista.
        """
        self.get_response = get_response

    def __call__(self, peticion):
        """Genera el codigo, procesa y sella la respuesta.

        Args:
            peticion: Peticion HTTP entrante.

        Returns:
            La respuesta con `Cache-Control: no-store`.
        """
        peticion.codigo_correlacion = generar_codigo_correlacion()
        respuesta = self.get_response(peticion)
        respuesta["Cache-Control"] = "no-store"
        respuesta["X-Codigo-Correlacion"] = peticion.codigo_correlacion
        return respuesta


def obtener_codigo(peticion) -> str:
    """Lee el codigo de la peticion o genera uno de reserva.

    Args:
        peticion: Peticion HTTP (idealmente ya sellada por el middleware).

    Returns:
        str: Codigo de correlacion vigente para esta peticion.
    """
    codigo = getattr(peticion, "codigo_correlacion", None)
    return codigo if codigo else generar_codigo_correlacion()
