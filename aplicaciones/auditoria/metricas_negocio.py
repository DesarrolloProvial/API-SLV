"""Metricas de servicio y negocio (tarea 4.1, sin dependencias nuevas).

Contadores en memoria con exposicion en texto Prometheus (`/metricas`,
solo red interna). Etiquetas acotadas (`recurso`, `estado`, `cliente`,
`ambito`); el `codigo_correlacion` y la placa NUNCA son etiquetas
(cardinalidad): viajan como campo del registro, nunca como label.
"""
import threading

#: Cubos del histograma de latencia en segundos (habilita p95 en tablero).
TOPES_LATENCIA_SEG: tuple = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

_bloqueo = threading.Lock()
_peticiones: dict = {}
_latencia_suma: dict = {}
_latencia_cuenta: dict = {}
_latencia_cubos: dict = {}
_bytes_respuesta: dict = {}
_limites: dict = {}
_errores_bd = 0
_busquedas = 0
_candidatas = 0
_entregas: dict = {}


def observar_peticion(
    recurso: str,
    estado: int,
    duracion_seg: float,
    respuesta_bytes: int = 0,
    cliente: str = "",
    ambitos=(),
) -> None:
    """Cuenta la peticion con latencia y deriva negocio y limites.

    Deriva sin tocar enrutadores: `429` suma al contador de limites;
    `200` en `buscar` suma busqueda; `200` en otro recurso de la API
    suma entrega bajo el ambito propio del recurso.

    Args:
        recurso: Clave de `recurso_desde_ruta` (`buscar`, ...).
        estado: Estado HTTP respondido.
        duracion_seg: Duracion de la peticion en segundos (>= 0).
        respuesta_bytes: Tamano del cuerpo respondido en bytes.
        cliente: Identidad de cuota (`client_id`/`sub` o `anonimo`).
        ambitos: Ambitos autorizados del token (para entregas).
    """
    global _busquedas
    codigo_estado = str(estado)
    with _bloqueo:
        _peticiones[(recurso, codigo_estado, cliente)] = (
            _peticiones.get((recurso, codigo_estado, cliente), 0) + 1
        )
        _latencia_suma[recurso] = _latencia_suma.get(recurso, 0.0) + max(
            0.0, duracion_seg
        )
        _latencia_cuenta[recurso] = _latencia_cuenta.get(recurso, 0) + 1
        for tope in TOPES_LATENCIA_SEG:
            if duracion_seg <= tope:
                _latencia_cubos[(recurso, str(tope))] = (
                    _latencia_cubos.get((recurso, str(tope)), 0) + 1
                )
        _bytes_respuesta[recurso] = (
            _bytes_respuesta.get(recurso, 0) + max(0, respuesta_bytes)
        )
        if estado == 429:
            _limites[recurso] = _limites.get(recurso, 0) + 1
        if estado == 200 and recurso == "buscar":
            _busquedas += 1
        if estado == 200 and recurso not in (
            "buscar", "salud", "metricas", "otro",
        ):
            _entregas[(recurso, _ambito_propio(recurso, ambitos))] = (
                _entregas.get(
                    (recurso, _ambito_propio(recurso, ambitos)), 0
                ) + 1
            )


def observar_candidatas(cantidad: int) -> None:
    """Suma las candidatas devueltas por `buscar` (volumen de negocio).

    Args:
        cantidad: Candidatas entregadas en la respuesta (>= 0).
    """
    global _candidatas
    with _bloqueo:
        _candidatas += max(0, int(cantidad))


def observar_error_bd() -> None:
    """Cuenta un error de BD (trazabilidad operativa, sin detalle)."""
    global _errores_bd
    with _bloqueo:
        _errores_bd += 1


def limpiar_metricas() -> None:
    """Vacia todos los contadores (solo pruebas)."""
    global _errores_bd, _busquedas, _candidatas
    with _bloqueo:
        _peticiones.clear()
        _latencia_suma.clear()
        _latencia_cuenta.clear()
        _latencia_cubos.clear()
        _bytes_respuesta.clear()
        _limites.clear()
        _entregas.clear()
        _errores_bd = 0
        _busquedas = 0
        _candidatas = 0


def exponer_metricas() -> str:
    """Devuelve los contadores en texto de exposicion Prometheus.

    Returns:
        str: Metricas con HELP/TYPE; sin codigo ni placa en etiquetas.
    """
    with _bloqueo:
        peticiones = dict(_peticiones)
        suma = dict(_latencia_suma)
        cuenta = dict(_latencia_cuenta)
        cubos = dict(_latencia_cubos)
        bytes_por_recurso = dict(_bytes_respuesta)
        limites = dict(_limites)
        entregas = dict(_entregas)
        errores_bd = _errores_bd
        busquedas = _busquedas
        candidatas = _candidatas
    lineas = []
    lineas.append("# HELP intercambio_peticiones_total Peticiones por recurso.")
    lineas.append("# TYPE intercambio_peticiones_total counter")
    for (recurso, estado, cliente), valor in sorted(peticiones.items()):
        lineas.append(
            f'intercambio_peticiones_total{{recurso="{_escapar(recurso)}",'
            f'estado="{_escapar(estado)}",cliente="{_escapar(cliente)}"}}'
            f" {_numero(valor)}"
        )
    lineas.append("# HELP intercambio_latencia_segundos Latencia por recurso.")
    lineas.append("# TYPE intercambio_latencia_segundos histogram")
    for recurso in sorted(cuenta):
        acumulado = 0
        for tope in TOPES_LATENCIA_SEG:
            acumulado += cubos.get((recurso, str(tope)), 0)
            lineas.append(
                f'intercambio_latencia_segundos_bucket{{recurso="'
                f'{_escapar(recurso)}",le="{tope}"}} {_numero(acumulado)}'
            )
        lineas.append(
            f'intercambio_latencia_segundos_bucket{{recurso="'
            f'{_escapar(recurso)}",le="+Inf"}} {_numero(cuenta[recurso])}'
        )
        lineas.append(
            f'intercambio_latencia_segundos_sum{{recurso="'
            f'{_escapar(recurso)}"}} {_numero(suma.get(recurso, 0.0))}'
        )
        lineas.append(
            f'intercambio_latencia_segundos_count{{recurso="'
            f'{_escapar(recurso)}"}} {_numero(cuenta[recurso])}'
        )
    lineas.append("# HELP intercambio_respuesta_bytes_total Bytes respondidos.")
    lineas.append("# TYPE intercambio_respuesta_bytes_total counter")
    for recurso, valor in sorted(bytes_por_recurso.items()):
        lineas.append(
            f'intercambio_respuesta_bytes_total{{recurso="'
            f'{_escapar(recurso)}"}} {_numero(valor)}'
        )
    lineas.append("# HELP intercambio_limites_total Cuotas excedidas (429).")
    lineas.append("# TYPE intercambio_limites_total counter")
    for recurso, valor in sorted(limites.items()):
        lineas.append(
            f'intercambio_limites_total{{recurso="{_escapar(recurso)}"}}'
            f" {_numero(valor)}"
        )
    lineas.append("# HELP intercambio_errores_bd_total Errores de BD.")
    lineas.append("# TYPE intercambio_errores_bd_total counter")
    lineas.append(f"intercambio_errores_bd_total {_numero(errores_bd)}")
    lineas.append("# HELP intercambio_busquedas_total Busquedas 200.")
    lineas.append("# TYPE intercambio_busquedas_total counter")
    lineas.append(f"intercambio_busquedas_total {_numero(busquedas)}")
    lineas.append("# HELP intercambio_candidatas_total Candidatas devueltas.")
    lineas.append("# TYPE intercambio_candidatas_total counter")
    lineas.append(f"intercambio_candidatas_total {_numero(candidatas)}")
    lineas.append("# HELP intercambio_entregas_total Entregas por ambito.")
    lineas.append("# TYPE intercambio_entregas_total counter")
    for (recurso, ambito), valor in sorted(entregas.items()):
        lineas.append(
            f'intercambio_entregas_total{{recurso="{_escapar(recurso)}",'
            f'ambito="{_escapar(ambito)}"}} {_numero(valor)}'
        )
    return "\n".join(lineas) + "\n"


def _ambito_propio(recurso: str, ambitos) -> str:
    """Devuelve el ambito propio del recurso si el token lo trae.

    Args:
        recurso: Clave del recurso entregado.
        ambitos: Ambitos autorizados del token.

    Returns:
        str: Ambito propio del recurso o la base como reserva.
    """
    from aplicaciones.seguridad.verificador_ambitos import (
        AMBITO_BASE,
        AMBITO_POR_VINCULO,
    )

    propio = AMBITO_POR_VINCULO.get(recurso, AMBITO_BASE)
    return propio if propio in (ambitos or ()) else AMBITO_BASE


def _escapar(valor: str) -> str:
    """Escapa un valor de etiqueta para la exposicion.

    Args:
        valor: Texto crudo de la etiqueta.

    Returns:
        str: Texto con barra, comilla y salto escapados.
    """
    return (
        str(valor).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    )


def _numero(valor) -> str:
    """Formatea un contador como flotante de exposicion.

    Args:
        valor: Contador entero o flotante.

    Returns:
        str: Numero en formato texto Prometheus.
    """
    return repr(float(valor))
