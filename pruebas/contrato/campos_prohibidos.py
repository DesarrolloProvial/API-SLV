"""Campos prohibidos del PLAN (tabla 8c y §11/§24, solo nombres).

Nunca se exponen ni se registran: secretos, PII dura, telemetria, rutas
y auditoria cruda. La comparacion normaliza (minusculas, sin tildes) y
los cortos (`cui`, `edad`) solo valen como nombre exacto para no marcar
`municipio` u otros falsos positivos. `vin`/`tarjeta_circulacion` son
restringidos (van por ambito y convenio), no prohibidos: no estan aqui.
"""
from typing import Final
import unicodedata

#: Subcadenas prohibidas (largas) + nombres exactos (cortas, ver abajo).
CAMPOS_PROHIBIDOS: Final[frozenset] = frozenset({
    "password", "contrasena", "hash", "token", "session_key", "user_agent",
    "minio", "sha256", "tamanio_bytes", "observaciones_internas",
    "observacion", "motivo_rechazo", "motivo_anulacion", "datos_extra",
    "cui", "telefono", "correo", "domicilio", "fecha_nacimiento", "edad",
    "ruta_acta", "ruta_almacenamiento", "nit", "poliza", "licencia",
    "registro_dgt", "ip_cliente", "changes",
})

#: Nombres que solo prohiben exactos (evitan falsos positivos).
EXACTOS: Final[frozenset] = frozenset({"cui", "edad", "nit", "token", "hash"})


def normalizar(texto: str) -> str:
    """Normaliza a minusculas sin tildes para comparar.

    Args:
        texto: Nombre de campo o texto a normalizar.

    Returns:
        str: Texto normalizado.
    """
    descompuesto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def contiene_prohibido(nombre: str) -> str | None:
    """Indica si un nombre de campo es o contiene un prohibido.

    Args:
        nombre: Nombre de campo del contrato o la respuesta.

    Returns:
        str | None: Prohibido hallado o None si esta limpio.
    """
    campo = normalizar(nombre)
    for prohibido in CAMPOS_PROHIBIDOS:
        if prohibido in EXACTOS:
            if campo == prohibido:
                return prohibido
        elif prohibido in campo:
            return prohibido
    return None


def escanear_propiedades(esquema: object, vista: str = "") -> list:
    """Recorre un objeto JSON y reporta claves con prohibidos.

    Args:
        esquema: Objeto (dict/lista) a escanear por claves.
        vista: Prefijo de ruta para el reporte.

    Returns:
        list: Hallazgos `vista.clave -> prohibido` (vacio = limpio).
    """
    hallazgos = []
    if isinstance(esquema, dict):
        for clave, valor in esquema.items():
            hallado = contiene_prohibido(str(clave))
            if hallado:
                hallazgos.append(f"{vista}{clave} -> {hallado}")
            hallazgos.extend(escanear_propiedades(valor, f"{vista}{clave}."))
    elif isinstance(esquema, list):
        for elemento in esquema:
            hallazgos.extend(escanear_propiedades(elemento, vista))
    return hallazgos
