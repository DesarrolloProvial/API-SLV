"""Registro estructurado de consultas (tarea 3.4, base de fase 4).

Una linea JSON por peticion con `codigo_correlacion`, recurso y estado;
nunca personales, secretos, SQL ni rutas internas. Fase 4 lo promueve a
Loki/Prometheus con tablero, metricas de negocio y exportacion a frio
(`aplicaciones/auditoria/registrador_consulta.py` es el gancho exacto:
agregar `metricas_negocio.py` y el `job intercambio-api` alli).
"""
import logging

_registro = logging.getLogger("intercambio.consulta")


def registrar_consulta(
    codigo: str, recurso: str, estado: int, cliente: str | None = None
) -> None:
    """Registra una linea estructurada de la consulta atendida.

    Args:
        codigo: Codigo de correlacion de la peticion.
        recurso: Recurso atendido (`buscar`, `expediente`, ...).
        estado: Estado HTTP respondido.
        cliente: Identidad OAuth2 (`client_id`/`sub`) o None.
    """
    linea = f"recurso={recurso} estado={estado} codigo={codigo}"
    if cliente:
        linea += f" cliente={cliente}"
    _registro.info(linea)


def recurso_desde_ruta(ruta: str) -> str:
    """Deriva el recurso desde la ruta sin datos personales.

    Args:
        ruta: Ruta HTTP (`request.path`, sin query).

    Returns:
        str: Recurso (`buscar`, `expediente`, ...) o `otro`.
    """
    partes = [p for p in ruta.strip("/").split("/") if p]
    if partes == ["salud"]:
        return "salud"
    if len(partes) < 3 or partes[0] != "api" or partes[1] != "v1":
        return "otro"
    resto = partes[2:]
    if resto[:1] == ["vehiculos"] and len(resto) == 2 and resto[1] == "buscar":
        return "buscar"
    if len(resto) >= 3 and resto[2] == "expediente":
        if len(resto) == 3:
            return "expediente"
        return resto[3] if resto[3] in (
            "generales", "propietario", "empresa", "refrendos", "historial",
        ) else "otro"
    return "otro"
