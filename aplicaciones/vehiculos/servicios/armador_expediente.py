"""Armado de expediente y generales desde la fila exacta (tareas 3.1/3.2).

Mapeo puro fila -> respuesta. `vin` y `tarjeta_circulacion` estan
restringidos por ambito y se excluyen hasta la tarea 3.4 (denegar por
defecto: sin ambito no sale ningun dato restringido). `vinculos` solo
trae lo implementado; el resto de ambitos se agrega en 3.3/3.4.
"""


def construir_vinculos(placa: str) -> dict:
    """Construye los vinculos del expediente hacia lo implementado.

    Fuente unica para no duplicar rutas entre contextos (3.3). El
    candado por ambitos (filtrar lo no autorizado) llega en 3.4.

    Args:
        placa: Placa ya normalizada para las rutas.

    Returns:
        dict: Rutas de expediente, generales y los 4 subrecursos.
    """
    base = f"/api/v1/vehiculos/{placa}/expediente"
    return {
        "expediente": base,
        "generales": f"{base}/generales",
        "propietario": f"{base}/propietario",
        "empresa": f"{base}/empresa",
        "refrendos": f"{base}/refrendos",
        "historial": f"{base}/historial",
    }


def armar_expediente(fila: dict, codigo_correlacion: str) -> dict:
    """Arma la respuesta de expediente con subconjunto de generales.

    Args:
        fila: Fila del selector exacto (vista_expediente).
        codigo_correlacion: Codigo de correlacion de la peticion.

    Returns:
        dict: Expediente con `vehiculo`, `vinculacion`,
            `refrendo_vigente` y `vinculos`.
    """
    placa = fila.get("placa_norma") or fila.get("placa") or ""
    refrendo = None
    if fila.get("refrendo_codigo") or fila.get("refrendo_fecha"):
        refrendo = {
            "codigo": fila.get("refrendo_codigo"),
            "fecha": fila.get("refrendo_fecha"),
            "vencimiento": fila.get("refrendo_vencimiento"),
            "estado": fila.get("refrendo_estado"),
        }
    return {
        "codigo_correlacion": codigo_correlacion,
        "placa": fila.get("placa") or placa,
        "vehiculo": {
            "chasis": fila.get("chasis"),
            "marca": fila.get("marca"),
            "linea": fila.get("linea"),
            "modelo": fila.get("modelo"),
            "serie": fila.get("serie"),
            "tipo_placa": fila.get("tipo_placa"),
            "clasificacion": fila.get("clasificacion"),
            "tipo_vehiculo": fila.get("tipo_vehiculo"),
            "uso": fila.get("uso"),
            "color": fila.get("color"),
            "departamento": fila.get("departamento"),
            "municipio": fila.get("municipio"),
            "motor": fila.get("motor"),
            "asientos": fila.get("asientos"),
            "ejes": fila.get("ejes"),
            "cilindraje": fila.get("cilindraje"),
            "centimetros_cubicos": fila.get("centimetros_cubicos"),
            "toneladas": fila.get("toneladas"),
            "codigo_correlativo": fila.get("codigo_correlativo"),
            "estado_aprobacion": fila.get("estado_aprobacion"),
            "activa": fila.get("activa"),
            "fecha_codigo": fila.get("fecha_codigo"),
            "tipo_slv_codigo": fila.get("tipo_slv_codigo"),
            "tipo_slv_nombre": fila.get("tipo_slv_nombre"),
        },
        "vinculacion": {
            "propietario_nombre": fila.get("propietario_nombre"),
            "empresa_nombre": fila.get("empresa_nombre"),
            "empresa_autorizacion": fila.get("empresa_autorizacion"),
            "empresa_esta_autorizada": fila.get("empresa_esta_autorizada"),
        },
        "refrendo_vigente": refrendo,
        "vinculos": construir_vinculos(placa),
    }


def armar_generales(fila: dict, codigo_correlacion: str) -> dict:
    """Arma la respuesta de generales (caracterizacion sin restringidos).

    Args:
        fila: Fila del selector exacto (vista_expediente).
        codigo_correlacion: Codigo de correlacion de la peticion.

    Returns:
        dict: Generales con `generales` (sin vin/tarjeta ni vinculos
            sensibles) y `vinculos` hacia expediente y generales.
    """
    placa = fila.get("placa_norma") or fila.get("placa") or ""
    expediente = armar_expediente(fila, codigo_correlacion)
    vehiculo = expediente["vehiculo"]
    return {
        "codigo_correlacion": codigo_correlacion,
        "placa": fila.get("placa") or placa,
        "generales": {
            clave: vehiculo[clave]
            for clave in (
                "chasis", "marca", "linea", "modelo", "serie", "tipo_placa",
                "clasificacion", "tipo_vehiculo", "uso", "color",
                "departamento", "municipio", "motor", "asientos", "ejes",
                "cilindraje", "centimetros_cubicos", "toneladas",
                "codigo_correlativo", "estado_aprobacion", "activa",
            )
        },
        "vinculos": expediente["vinculos"],
    }
