"""Limites y cuotas multicapa lado API (tarea 3.4).

Ventana fija en memoria por `(cliente, recurso)` con valores de dia 0
(`LIMITE_BUSCAR_TOPE` mas estricto; resto en `LIMITE_RECURSO_TOPE`;
ambos sobre `VENTANA_LIMITE_SEG`, calibrables por convenio). El borde
(nginx/WAF) lleva sus propios limites; esto es la capa API.

Al exceder: `LimiteExcedido` con `reintentar_en` (el enrutador lo
traduce al 429 `limite_excedido` uniforme y el middleware pone la
cabecera `Retry-After`). El mensaje nunca filtra umbrales. En despliegue
multirreplica, migrar el contador a Valkey (gancho fase 4).
"""
import threading
import time
from typing import Final

from django.conf import settings

RECURSO_BUSCAR: Final[str] = "buscar"


class LimiteExcedido(Exception):
    """La cuota del cliente para el recurso se agoto en la ventana."""

    def __init__(self, reintentar_en: int):
        """Guarda los segundos sugeridos para `Retry-After`.

        Args:
            reintentar_en: Segundos hasta reintentar (>= 1).
        """
        super().__init__("Limite de consultas excedido.")
        self.reintentar_en = max(1, int(reintentar_en))


_ventanas: dict = {}
_bloqueo = threading.Lock()


class AlmacenLimites:
    """Contrato minimo del contador de cuotas (gancho multirreplica).

    La version de dia 0 es en memoria por proceso. En multirreplica se
    inyecta una version Valkey con ventana fija por
    `limite:{cliente}:{recurso}` (`ZADD` + `ZREMRANGEBYSCORE` de lo
    vencido + `ZCARD` contra el tope + `EXPIRE = ventana`, sin estado
    local). `configurar_almacen_limites()` la instala y
    `restablecer_almacen_limites()` vuelve a memoria.
    """

    def cargar(self, clave: str) -> list:
        """Devuelve las marcas vigentes conocidas para la clave.

        Args:
            clave: Identidad de cuota (`cliente:recurso`).

        Returns:
            list: Marcas de tiempo monotonicas conocidas.
        """
        raise NotImplementedError

    def guardar(self, clave: str, marcas: list) -> None:
        """Persiste las marcas vigentes de la clave.

        Args:
            clave: Identidad de cuota (`cliente:recurso`).
            marcas: Marcas vigentes a conservar.
        """
        raise NotImplementedError


class _AlmacenMemoria(AlmacenLimites):
    """Contador en memoria por proceso (dia 0, sin red)."""

    def __init__(self):
        """Inicia el mapa vacio de ventanas."""
        self.ventanas: dict = {}

    def cargar(self, clave: str) -> list:
        """Devuelve una copia de las marcas de la clave."""
        return list(self.ventanas.get(clave, []))

    def guardar(self, clave: str, marcas: list) -> None:
        """Guarda una copia de las marcas vigentes."""
        self.ventanas[clave] = list(marcas)


_almacen: AlmacenLimites = _AlmacenMemoria()


def tope_para(recurso: str) -> tuple:
    """Devuelve `(tope, ventana_seg)` del recurso (dia 0 calibrable).

    Args:
        recurso: Clave del recurso (`buscar` u otro).

    Returns:
        tuple: `(maximo_de_peticiones, ventana_en_segundos)`.
    """
    ventana = int(getattr(settings, "VENTANA_LIMITE_SEG", 60))
    if recurso == RECURSO_BUSCAR:
        return int(getattr(settings, "LIMITE_BUSCAR_TOPE", 30)), ventana
    return int(getattr(settings, "LIMITE_RECURSO_TOPE", 60)), ventana


def clave_cliente(reclamos: dict, peticion=None) -> str:
    """Calcula la identidad de cuota (cliente OAuth2, nunca secreto).

    Args:
        reclamos: Reclamos verificados del token.
        peticion: Peticion HTTP (reservada para futuros criterios).

    Returns:
        str: `client_id`/`sub`/`azp` o `anonimo` como ultimo recurso.
    """
    _ = peticion
    for campo in ("client_id", "sub", "azp"):
        valor = reclamos.get(campo)
        if valor:
            return str(valor)
    return "anonimo"


def verificar_limite(peticion, reclamos: dict, recurso: str) -> None:
    """Verifica la cuota del cliente o deniega con reintento.

    Args:
        peticion: Peticion HTTP (no se lee; reserva de criterio).
        reclamos: Reclamos verificados del token.
        recurso: Clave del recurso para el tope.

    Raises:
        LimiteExcedido: Con `reintentar_en` si se agoto la ventana.
    """
    tope, ventana = tope_para(recurso)
    clave = f"{clave_cliente(reclamos, peticion)}:{recurso}"
    ahora = time.monotonic()
    with _bloqueo:
        marcas = [m for m in _almacen.cargar(clave) if ahora - m < ventana]
        if len(marcas) >= tope:
            sobrante = ventana - (ahora - marcas[0]) if marcas else ventana
            _almacen.guardar(clave, marcas)
            raise LimiteExcedido(int(sobrante) + 1)
        marcas.append(ahora)
        _almacen.guardar(clave, marcas)


def configurar_almacen_limites(almacen: AlmacenLimites) -> None:
    """Instala el almacen de cuotas (p. ej. Valkey en multirreplica).

    Args:
        almacen: Implementacion de `AlmacenLimites` a usar.
    """
    global _almacen
    with _bloqueo:
        _almacen = almacen


def restablecer_almacen_limites() -> None:
    """Vuelve al almacen en memoria de dia 0."""
    global _almacen
    with _bloqueo:
        _almacen = _AlmacenMemoria()


def limpiar_limites() -> None:
    """Vacia los contadores en memoria (solo pruebas)."""
    restablecer_almacen_limites()
