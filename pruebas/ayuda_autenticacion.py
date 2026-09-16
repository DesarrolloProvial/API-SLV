"""Ayuda de autenticacion para pruebas (HS256 local, sin red).

Genera JWT firmados con `LLAVE_SECRETA` de los ajustes vigentes, el mismo
modo que usa el validador sin `URL_JWKS`. Solo pruebas: produccion exige
`RS256` por JWKS.
"""
import time
import uuid

import jwt
from django.conf import settings


def emitir_token_prueba(
    ambitos: list | None = None,
    *,
    expirado: bool = False,
    firma: str | None = None,
    algoritmo: str = "HS256",
    reclamos_extra: dict | None = None,
) -> str:
    """Emite un token de prueba con los ambitos dados.

    Args:
        ambitos: Ambitos OAuth2 a incluir en `scope` (separados por hora).
        expirado: Si True, el `exp` queda en el pasado.
        firma: Llave de firma (por defecto la `LLAVE_SECRETA` vigente).
        algoritmo: Algoritmo de firma (`HS256` en pruebas).
        reclamos_extra: Reclamos a mezclar (p. ej. `jti` fijo).

    Returns:
        str: JWT compacto listo para `Authorization: Bearer`.
    """
    ahora = int(time.time())
    carga = {
        "sub": "dgt-intercambio",
        "client_id": "dgt-intercambio",
        "scope": " ".join(ambitos or []),
        "iat": ahora - 60,
        "exp": ahora - 300 if expirado else ahora + 300,
        "jti": str(uuid.uuid4()),
    }
    emisor = getattr(settings, "EMISOR_JWT", "")
    audiencia = getattr(settings, "AUDIENCIA_JWT", "")
    if emisor:
        carga["iss"] = emisor
    if audiencia:
        carga["aud"] = audiencia
    carga.update(reclamos_extra or {})
    return jwt.encode(carga, firma or settings.LLAVE_SECRETA, algorithm=algoritmo)


def cabecera_autorizacion(ambitos: list | None = None, **opciones) -> dict:
    """Arma el `extra` de Django para `Authorization: Bearer`.

    Args:
        ambitos: Ambitos del token de prueba.
        opciones: Opciones de `emitir_token_prueba`.

    Returns:
        dict: `{"HTTP_AUTHORIZATION": "Bearer ..."}` para el cliente.
    """
    return {"HTTP_AUTHORIZATION": f"Bearer {emitir_token_prueba(ambitos, **opciones)}"}


TODOS_LOS_AMBITOS = [
    "vehiculos.lectura",
    "vehiculos.propietario.lectura",
    "vehiculos.empresa.lectura",
    "vehiculos.refrendos.lectura",
    "vehiculos.historial.lectura",
]
