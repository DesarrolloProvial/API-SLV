"""Verificacion de ambitos OAuth2 por recurso (tarea 3.4).

`vehiculos.lectura` es la base (`buscar`, `expediente`, `generales`); cada
subrecurso exige ademas su ambito propio. Sin el ambito no sale ningun
dato (403 `sin_permiso` uniforme); los `vinculos` solo traen lo
autorizado para no anunciar lo que el cliente no puede ver.
"""
from typing import Final

from aplicaciones.seguridad.validador_jwks import (
    TokenInvalido,
    autenticar_peticion,
)

AMBITO_BASE: Final[str] = "vehiculos.lectura"
AMBITO_PROPIETARIO: Final[str] = "vehiculos.propietario.lectura"
AMBITO_EMPRESA: Final[str] = "vehiculos.empresa.lectura"
AMBITO_REFRENDOS: Final[str] = "vehiculos.refrendos.lectura"
AMBITO_HISTORIAL: Final[str] = "vehiculos.historial.lectura"

AMBITOS_RECURSO: Final[dict] = {
    "buscar": frozenset({AMBITO_BASE}),
    "expediente": frozenset({AMBITO_BASE}),
    "generales": frozenset({AMBITO_BASE}),
    "propietario": frozenset({AMBITO_BASE, AMBITO_PROPIETARIO}),
    "empresa": frozenset({AMBITO_BASE, AMBITO_EMPRESA}),
    "refrendos": frozenset({AMBITO_BASE, AMBITO_REFRENDOS}),
    "historial": frozenset({AMBITO_BASE, AMBITO_HISTORIAL}),
}

AMBITO_POR_VINCULO: Final[dict] = {
    "expediente": AMBITO_BASE,
    "generales": AMBITO_BASE,
    "propietario": AMBITO_PROPIETARIO,
    "empresa": AMBITO_EMPRESA,
    "refrendos": AMBITO_REFRENDOS,
    "historial": AMBITO_HISTORIAL,
}


class PermisoDenegado(Exception):
    """El token es valido pero no trae el ambito del recurso."""


def obtener_ambitos(reclamos: dict) -> set:
    """Extrae los ambitos del reclamo `scope` (cadena separada por hora).

    Args:
        reclamos: Reclamos verificados del token.

    Returns:
        set: Ambitos presentes (vacio si no hay `scope`).
    """
    crudo = reclamos.get("scope", "")
    if isinstance(crudo, (list, tuple)):
        return {str(a) for a in crudo if a}
    return {a for a in str(crudo).split() if a}


def exigir_ambitos(reclamos: dict, recurso: str) -> set:
    """Exige los ambitos del recurso o deniega sin dato.

    Args:
        reclamos: Reclamos verificados del token.
        recurso: Clave de `AMBITOS_RECURSO` (p. ej. `refrendos`).

    Returns:
        set: Ambitos del token (para filtrar `vinculos`).

    Raises:
        PermisoDenegado: Si falta la base o el ambito propio.
    """
    requeridos = AMBITOS_RECURSO.get(recurso, frozenset({AMBITO_BASE}))
    presentes = obtener_ambitos(reclamos)
    if not requeridos.issubset(presentes):
        raise PermisoDenegado(f"Falta ambito para {recurso}.")
    return presentes


def autenticar_y_autorizar(peticion, recurso: str) -> tuple:
    """Autentica el portador y autoriza el recurso en un paso.

    Args:
        peticion: Peticion HTTP con cabecera `Authorization`.
        recurso: Clave de `AMBITOS_RECURSO`.

    Returns:
        tuple: `(reclamos, ambitos)` verificados y autorizados.

    Raises:
        TokenInvalido: Si falta el token o no es valido (401).
        PermisoDenegado: Si el token no trae el ambito (403).
    """
    reclamos = autenticar_peticion(peticion)
    ambitos = exigir_ambitos(reclamos, recurso)
    peticion.cliente_intercambio = _cliente_desde_reclamos(reclamos)
    peticion.ambitos_intercambio = set(ambitos)
    return reclamos, ambitos


def _cliente_desde_reclamos(reclamos: dict) -> str:
    """Calcula la identidad de metricas (misma que la cuota).

    Args:
        reclamos: Reclamos verificados del token.

    Returns:
        str: `client_id`/`sub`/`azp` o `anonimo` como ultimo recurso.
    """
    from aplicaciones.seguridad.aplicador_limites import clave_cliente

    return clave_cliente(reclamos)


def filtrar_vinculos(vinculos: dict, ambitos: set) -> dict:
    """Filtra `vinculos` a lo autorizado (sin anunciar lo ajeno).

    Args:
        vinculos: Mapa completo de rutas del expediente.
        ambitos: Ambitos del token (`obtener_ambitos` o `exigir_ambitos`).

    Returns:
        dict: Solo las rutas cuyo ambito esta presente.
    """
    return {
        clave: ruta
        for clave, ruta in vinculos.items()
        if AMBITO_POR_VINCULO.get(clave, AMBITO_BASE) in ambitos
    }
