"""Validacion de JWT contra JWKS (tarea 3.4).

Produccion: `RS256` con llaves de `URL_JWKS` (Keycloak, reino
`intercambio-dgt`), `EMISOR_JWT` y `AUDIENCIA_JWT` configurados; vigencia
corta la define el IdP. Desarrollo/pruebas: sin `URL_JWKS` se acepta
`HS256` firmado con `LLAVE_SECRETA` (solo local, jamas en produccion).

Token ausente, expirado o con firma invalida -> `TokenInvalido` (el
enrutador lo traduce al 401 `no_autenticado` uniforme). La revocacion
real es Keycloak (revocar cliente/token) + denegar en el borde; aqui hay
una lista de `jti` denegados (`TOKENS_REVOCADOS` + `revocar_token()`)
como segunda capa de emergencia.
"""
import base64
import json
import logging
import threading
import time
import urllib.request
from typing import Final

import jwt
from django.conf import settings

ALGORITMOS_JWKS: Final[tuple] = ("RS256",)
ALGORITMO_PRUEBAS: Final[str] = "HS256"

_registro = logging.getLogger("intercambio.consulta")

_cache_bloqueo = threading.Lock()
_cache_llaves: dict = {}
_cache_instante: float = 0.0

_revocados_bloqueo = threading.Lock()
_revocados_memoria: set = set()


class TokenInvalido(Exception):
    """El token falta, expiro, su firma es invalida o fue revocado."""


def extraer_portador(peticion) -> str | None:
    """Extrae el token `Bearer` de la cabecera `Authorization`.

    Args:
        peticion: Peticion HTTP entrante.

    Returns:
        str | None: Token sin el prefijo o None si no hay portador.
    """
    cabecera = peticion.headers.get("Authorization", "") if hasattr(
        peticion, "headers"
    ) else peticion.META.get("HTTP_AUTHORIZATION", "")
    if not cabecera:
        cabecera = peticion.META.get("HTTP_AUTHORIZATION", "")
    esquema, _, valor = cabecera.partition(" ")
    if esquema.lower() != "bearer" or not valor.strip():
        return None
    return valor.strip()


def autenticar_peticion(peticion) -> dict:
    """Autentica la peticion y devuelve sus reclamos.

    Args:
        peticion: Peticion HTTP con cabecera `Authorization`.

    Returns:
        dict: Reclamos verificados (`sub`, `scope`, `jti`, ...).

    Raises:
        TokenInvalido: Si falta el token o no pasa la validacion.
    """
    token = extraer_portador(peticion)
    if token is None:
        raise TokenInvalido("Falta el token portador.")
    return validar_token(token)


def validar_token(token: str, llaves: dict | None = None) -> dict:
    """Valida firma, vigencia, emisor, audiencia y revocacion.

    Args:
        token: JWT compacto recibido del cliente.
        llaves: Mapa `kid -> llave` para pruebas (omite la red JWKS).

    Returns:
        dict: Reclamos verificados del token.

    Raises:
        TokenInvalido: Ante cualquier fallo, sin detallar la causa.
    """
    if not token or token.count(".") != 2:
        raise TokenInvalido("Formato de token no reconocido.")
    try:
        cabecera = jwt.get_unverified_header(token)
    except Exception as error:
        raise TokenInvalido("Cabecera de token ilegible.") from error
    if cabecera.get("alg") == "none":
        raise TokenInvalido("Algoritmo no permitido.")
    try:
        if llaves is not None:
            reclamos = _validar_con_llaves(token, cabecera, llaves)
        elif _usa_jwks():
            reclamos = _validar_con_jwks(token, cabecera)
        else:
            reclamos = _validar_desarrollo(token)
    except TokenInvalido:
        raise
    except Exception as error:
        raise TokenInvalido("Token no valido.") from error
    _exigir_no_revocado(reclamos)
    return reclamos


def revocar_token(jti: str) -> None:
    """Deniega un `jti` en memoria (emergencia, sin esperar expiracion).

    Args:
        jti: Identificador del token a denegar (vacio se ignora).
    """
    if not jti:
        return
    with _revocados_bloqueo:
        _revocados_memoria.add(jti)


def limpiar_cache_jwks() -> None:
    """Vacia la cache JWKS y la lista en memoria (solo pruebas)."""
    global _cache_llaves, _cache_instante
    with _cache_bloqueo:
        _cache_llaves = {}
        _cache_instante = 0.0
    with _revocados_bloqueo:
        _revocados_memoria.clear()


def _usa_jwks() -> bool:
    """Indica si hay JWKS configurado (modo produccion/Keycloak)."""
    return bool(getattr(settings, "URL_JWKS", ""))


def _opciones_verificacion() -> dict:
    """Arma issuer/audience/leeway desde ajustes (vacio = no exige)."""
    opciones: dict = {"leeway": int(getattr(settings, "TOLERANCIA_RELOJ_SEG", 30))}
    emisor = getattr(settings, "EMISOR_JWT", "")
    audiencia = getattr(settings, "AUDIENCIA_JWT", "")
    if emisor:
        opciones["issuer"] = emisor
    if audiencia:
        opciones["audience"] = audiencia
    return opciones


def _validar_con_llaves(token: str, cabecera: dict, llaves: dict) -> dict:
    """Valida contra un mapa de llaves inyectado (pruebas, sin red)."""
    llave = llaves.get(cabecera.get("kid", ""), llaves.get(""))
    if llave is None:
        raise TokenInvalido("Llave del token desconocida.")
    return jwt.decode(
        token, llave, algorithms=[cabecera.get("alg", ALGORITMO_PRUEBAS)],
        **_opciones_verificacion(),
    )


def _validar_con_jwks(token: str, cabecera: dict) -> dict:
    """Valida `RS256` contra las llaves del JWKS remoto."""
    if cabecera.get("alg") not in ALGORITMOS_JWKS:
        raise TokenInvalido("Algoritmo no permitido para JWKS.")
    llaves = _obtener_llaves_jwks()
    llave = llaves.get(cabecera.get("kid", ""))
    if llave is None:
        raise TokenInvalido("Llave del token desconocida.")
    return jwt.decode(token, llave, algorithms=list(ALGORITMOS_JWKS),
                      **_opciones_verificacion())


def _validar_desarrollo(token: str) -> dict:
    """Valida `HS256` con `LLAVE_SECRETA` (solo sin `URL_JWKS`)."""
    secreta = getattr(settings, "LLAVE_SECRETA", "")
    if not secreta:
        raise TokenInvalido("Sin llave de validacion.")
    return jwt.decode(token, secreta, algorithms=[ALGORITMO_PRUEBAS],
                      **_opciones_verificacion())


def _exigir_no_revocado(reclamos: dict) -> None:
    """Rechaza el token si su `jti` esta denegado."""
    jti = reclamos.get("jti")
    if not jti:
        return
    configurados = set(getattr(settings, "TOKENS_REVOCADOS", []) or [])
    with _revocados_bloqueo:
        denegados = configurados | _revocados_memoria
    if jti in denegados:
        raise TokenInvalido("Token revocado.")


def _obtener_llaves_jwks() -> dict:
    """Devuelve `kid -> llave` del JWKS con cache de corta vida."""
    global _cache_llaves, _cache_instante
    ttl = int(getattr(settings, "TIEMPO_CACHE_JWKS_SEG", 600))
    ahora = time.monotonic()
    with _cache_bloqueo:
        if _cache_llaves and (ahora - _cache_instante) < ttl:
            return dict(_cache_llaves)
    documento = _descargar_jwks()
    llaves = {}
    for entrada in documento.get("keys", []):
        kid = entrada.get("kid", "")
        try:
            llaves[kid] = _llave_desde_jwk(entrada)
        except Exception as error:
            _registro.warning("Llave JWKS ignorada sin detalle interno.")
            _ = error
    with _cache_bloqueo:
        _cache_llaves = llaves
        _cache_instante = ahora
    return dict(llaves)


def _descargar_jwks() -> dict:
    """Descarga el documento JWKS (errores -> `TokenInvalido`)."""
    url = getattr(settings, "URL_JWKS", "")
    try:
        with urllib.request.urlopen(url, timeout=5) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except Exception as error:
        raise TokenInvalido("IdP no disponible.") from error


def _llave_desde_jwk(entrada: dict):
    """Convierte una entrada JWK en llave verificable."""
    tipo = entrada.get("kty", "")
    if tipo == "RSA":
        return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(entrada))
    if tipo == "oct":
        relleno = "=" * (-len(entrada.get("k", "")) % 4)
        return base64.urlsafe_b64decode((entrada["k"] + relleno).encode("ascii"))
    raise TokenInvalido("Tipo de llave no soportado.")
