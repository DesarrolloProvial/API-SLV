"""Propagacion del codigo de correlacion (tarea 3.4).

Genera el `codigo_correlacion` (UUIDv7) por peticion o reutiliza el del
borde (`X-Codigo-Correlacion`), lo expone en `peticion.codigo_correlacion`
y marca toda respuesta con `Cache-Control: no-store`, su codigo y
`Retry-After` cuando hubo cuota. Antes de la vista fija
`application_name` en PostgreSQL (`intercambio:<codigo>`) y al cerrar
registra una linea estructurada (sin personales ni secretos).

Gancho fase 4: tablero, metricas de negocio, alertas antiabuso y export
a frio viven en `registrador_consulta.py` + `observabilidad/`; aqui solo
queda el gancho (`propagar_correlacion_bd` + `registrar_consulta`).
"""
import uuid

from aplicaciones.auditoria.registrador_consulta import (
    recurso_desde_ruta,
    registrar_consulta,
)


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
        propagar_correlacion_bd(peticion.codigo_correlacion)
        respuesta = self.get_response(peticion)
        respuesta["Cache-Control"] = "no-store"
        respuesta["X-Codigo-Correlacion"] = peticion.codigo_correlacion
        reintento = getattr(peticion, "limite_reintento_en", None)
        if reintento is not None:
            respuesta["Retry-After"] = str(max(1, int(reintento)))
        registrar_consulta(
            peticion.codigo_correlacion,
            recurso_desde_ruta(peticion.path),
            respuesta.status_code,
        )
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


def propagar_correlacion_bd(codigo: str) -> None:
    """Fija `application_name` en PostgreSQL para rastrear la peticion.

    Sin sobrecosto: un `SET` local por peticion; en sqlite/desarrollo o
    sin BD se ignora en silencio (fase 4 lo verifica contra el espejo
    real con `SELECT current_setting('application_name')`).

    Args:
        codigo: Codigo de correlacion vigente de la peticion.
    """
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                "SET application_name = %s", [f"intercambio:{codigo}"]
            )
    except Exception:
        return
