"""Cursor opaco firmado para refrendos e historial (tarea 3.3).

Token `base64url` con posicion mas filtro (`placa_norma`), firmado con
HMAC-SHA256 derivado de `LLAVE_SECRETA`. Solo lo usan refrendos e
historial; el resto de recursos no acepta paginacion. Sin totales ni
`page/limit`: el llamador pide `tope + 1` y emite `cursor_siguiente`
solo si hubo mas. Cursor invalido o manipulado -> `CursorInvalido`
(el enrutador lo traduce al 404 uniforme, sin senal de causa).

Sin expiracion por diseno: el cursor solo guarda posicion publica mas
filtro, sin datos sensibles; un TTL anadiria reloj sin beneficio. Se
puede agregar `exp` si el convenio lo exige sin romper el formato
(version `v` permite evolucion).
"""
import base64
import hashlib
import hmac
import json
from typing import Final

from django.conf import settings

VERSION_CURSOR: Final[int] = 1


class CursorInvalido(Exception):
    """El cursor no es autentico, no corresponde al filtro o es ilegible."""


def emitir_cursor(placa_norma: str, desplazamiento: int) -> str:
    """Emite un cursor opaco para la placa y posicion dadas.

    Args:
        placa_norma: Placa ya normalizada (filtro ligado al cursor).
        desplazamiento: Posicion inicial de la siguiente pagina (>= 0).

    Returns:
        str: Token `cuerpo.firma` en `base64url` sin relleno.

    Raises:
        ValueError: Si la placa esta vacia o el desplazamiento es negativo.
    """
    if not placa_norma:
        raise ValueError("La placa del cursor no puede estar vacia.")
    if not isinstance(desplazamiento, int) or desplazamiento < 0:
        raise ValueError("El desplazamiento debe ser un entero >= 0.")
    carga = {"placa": placa_norma, "pos": desplazamiento, "v": VERSION_CURSOR}
    cuerpo = _a_base64url(json.dumps(carga, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    firma = hmac.new(_llave_firma(), cuerpo.encode("ascii"), hashlib.sha256).digest()
    return f"{cuerpo}.{_a_base64url(firma)}"


def decodificar_cursor(cursor: str, placa_norma: str) -> int:
    """Valida el cursor y devuelve el desplazamiento si liga a la placa.

    Args:
        cursor: Token opaco recibido en el parametro `cursor`.
        placa_norma: Placa ya normalizada que debe coincidir con el filtro.

    Returns:
        int: Desplazamiento (>= 0) para el selector.

    Raises:
        CursorInvalido: Ante formato roto, firma invalida, version
            desconocida, placa distinta o posicion ilegitima.
    """
    try:
        if not cursor or "." not in cursor:
            raise CursorInvalido("Formato de cursor no reconocido.")
        cuerpo, firma_recibida = cursor.split(".", 1)
        esperada = hmac.new(_llave_firma(), cuerpo.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_a_base64url(esperada), firma_recibida):
            raise CursorInvalido("Firma del cursor no valida.")
        carga = json.loads(_de_base64url(cuerpo).decode("utf-8"))
        if carga.get("v") != VERSION_CURSOR:
            raise CursorInvalido("Version de cursor no soportada.")
        if carga.get("placa") != placa_norma:
            raise CursorInvalido("El cursor no corresponde a esta placa.")
        posicion = carga.get("pos")
        if not isinstance(posicion, int) or posicion < 0:
            raise CursorInvalido("Posicion del cursor ilegitima.")
        return posicion
    except CursorInvalido:
        raise
    except Exception as error:
        raise CursorInvalido("Cursor ilegible.") from error


def _llave_firma() -> bytes:
    """Deriva la llave HMAC desde `LLAVE_SECRETA` con separacion de dominio.

    Returns:
        bytes: Llave de 32 bytes para firmar cursores (nunca se expone).
    """
    secreta = getattr(settings, "LLAVE_SECRETA", "")
    return hashlib.sha256(f"cursor-opaco-v1:{secreta}".encode("utf-8")).digest()


def _a_base64url(datos: bytes) -> str:
    """Codifica a `base64url` sin relleno.

    Args:
        datos: Bytes a codificar.

    Returns:
        str: Texto `base64url` sin `=`.
    """
    return base64.urlsafe_b64encode(datos).decode("ascii").rstrip("=")


def _de_base64url(texto: str) -> bytes:
    """Decodifica `base64url` sin relleno.

    Args:
        texto: Texto `base64url` con o sin relleno.

    Returns:
        bytes: Bytes decodificados.
    """
    relleno = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode((texto + relleno).encode("ascii"))
