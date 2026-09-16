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

        Reutiliza `X-Codigo-Correlacion` del borde si viene (generado en
        borde, propagado como cabecera); si no, genera uno nuevo. Toda
        respuesta lleva `Cache-Control: no-store`, su codigo en cuerpo y
        cabecera, y `Retry-After` cuando el enrutador marco cuota.

        Args:
            peticion: Peticion HTTP entrante.

        Returns:
            La respuesta sellada con correlacion y sin cache.
        """
        peticion.codigo_correlacion = (
            _codigo_del_borde(peticion) or generar_codigo_correlacion()
        )
        respuesta = self.get_response(peticion)
        respuesta["Cache-Control"] = "no-store"
        respuesta["X-Codigo-Correlacion"] = peticion.codigo_correlacion
        reintento = getattr(peticion, "limite_reintento_en", None)
        if reintento is not None:
            respuesta["Retry-After"] = str(max(1, int(reintento)))
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


def _codigo_del_borde(peticion) -> str | None:
    """Lee el codigo que envio el borde, si es valido.

    Args:
        peticion: Peticion HTTP con cabeceras del borde.

    Returns:
        str | None: Codigo del borde o None si no viene o es invalido.
    """
    cabecera = ""
    if hasattr(peticion, "headers"):
        cabecera = peticion.headers.get("X-Codigo-Correlacion", "")
    if not cabecera:
        cabecera = peticion.META.get("HTTP_X_CODIGO_CORRELACION", "")
    texto = cabecera.strip()
    if len(texto) < 8 or len(texto) > 64:
        return None
    if any(c.isspace() for c in texto):
        return None
    return texto
