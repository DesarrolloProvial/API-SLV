"""Verificacion de aditividad del Anexo C (contrato externo versionado).

El contrato solo crece: pasar es agregar rutas, esquemas o campos;
fallar es eliminar o renombrar rutas, metodos, respuestas, parametros o
propiedades, o cambiarles el tipo. Uso en CI y en local:

    python contratos/verificar_aditividad.py base.json actual.json
"""
import json
import sys


def es_aditivo(base: dict, actual: dict) -> list:
    """Compara el OpenAPI actual contra la instantanea base.

    Args:
        base: OpenAPI congelado (`contratos/instantaneas/anexo_c_v1/`).
        actual: OpenAPI recien generado desde los esquemas.

    Returns:
        list: Rupturas detectadas (vacia = aditivo, puede evolucionar).
    """
    errores = []
    errores.extend(_comparar_rutas(base, actual))
    errores.extend(
        _comparar_esquemas(
            base.get("components", {}).get("schemas", {}),
            actual.get("components", {}).get("schemas", {}),
        )
    )
    return errores


def _comparar_rutas(base: dict, actual: dict) -> list:
    """Exige que ninguna ruta, metodo, respuesta o parametro se pierda."""
    errores = []
    rutas_base = base.get("paths", {})
    rutas_actual = actual.get("paths", {})
    for ruta, metodos in rutas_base.items():
        if ruta not in rutas_actual:
            errores.append(f"ruta eliminada: {ruta}")
            continue
        for metodo, operacion in metodos.items():
            vigente = rutas_actual[ruta].get(metodo)
            if vigente is None:
                errores.append(f"metodo eliminado: {metodo.upper()} {ruta}")
                continue
            for codigo in (operacion.get("responses", {}) or {}):
                if codigo not in (vigente.get("responses", {}) or {}):
                    errores.append(
                        f"respuesta eliminada: {metodo.upper()} {ruta} {codigo}"
                    )
            params_base = {
                (p.get("name"), p.get("in"))
                for p in (operacion.get("parameters", {}) or [])
            }
            params_actual = {
                (p.get("name"), p.get("in"))
                for p in (vigente.get("parameters", {}) or [])
            }
            for param in params_base - params_actual:
                errores.append(
                    f"parametro eliminado: {metodo.upper()} {ruta} {param}"
                )
    return errores


def _comparar_esquemas(base: dict, actual: dict) -> list:
    """Exige que ningun esquema ni propiedad se pierda o cambie de tipo."""
    errores = []
    for nombre, esquema in base.items():
        if nombre not in actual:
            errores.append(f"esquema eliminado: {nombre}")
            continue
        errores.extend(_comparar_propiedades(nombre, esquema, actual[nombre], actual))
    return errores


def _comparar_propiedades(
    ruta: str, esquema_base: dict, esquema_actual: dict, todos: dict
) -> list:
    """Compara propiedades en profundidad (resuelve `$ref` e `items`)."""
    errores = []
    props_base = esquema_base.get("properties", {}) or {}
    props_actual = esquema_actual.get("properties", {}) or {}
    for nombre, prop_base in props_base.items():
        if nombre not in props_actual:
            errores.append(f"campo eliminado: {ruta}.{nombre}")
            continue
        prop_actual = props_actual[nombre]
        tipos_base = _tipos(prop_base)
        tipos_actual = _tipos(prop_actual)
        if tipos_base - tipos_actual:
            errores.append(
                f"tipo cambiado: {ruta}.{nombre} {sorted(tipos_base)}"
                f" -> {sorted(tipos_actual)}"
            )
            continue
        errores.extend(
            _comparar_referencias(
                f"{ruta}.{nombre}", prop_base, prop_actual, todos
            )
        )
    return errores


def _comparar_referencias(
    ruta: str, prop_base: dict, prop_actual: dict, todos: dict
) -> list:
    """Baja a `$ref` e `items` cuando ambas puntas apuntan al mismo sitio."""
    errores = []
    ref_base = _referencia(prop_base)
    ref_actual = _referencia(prop_actual)
    if ref_base and ref_actual:
        if ref_base != ref_actual:
            return [f"referencia cambiada: {ruta} {ref_base} -> {ref_actual}"]
        destino_base = todos.get(ref_base, {})
        destino_actual = todos.get(ref_actual, {})
        return _comparar_propiedades(ruta, destino_base, destino_actual, todos)
    for clave in ("items",):
        hijo_base = (prop_base.get(clave, {}) or {})
        hijo_actual = (prop_actual.get(clave, {}) or {})
        if hijo_base and hijo_actual:
            errores.extend(
                _comparar_referencias(ruta, hijo_base, hijo_actual, todos)
            )
    return errores


def _referencia(propiedad: dict) -> str:
    """Devuelve el nombre del esquema referenciado o vacio."""
    if "$ref" in propiedad:
        return propiedad["$ref"].split("/")[-1]
    for rama in propiedad.get("anyOf", []) or []:
        if "$ref" in rama:
            return rama["$ref"].split("/")[-1]
    return ""


def _tipos(propiedad: dict) -> set:
    """Normaliza los tipos aceptados (`type` + ramas `anyOf` + `$ref`)."""
    tipos = set()
    if "$ref" in propiedad:
        return {"ref:" + propiedad["$ref"].split("/")[-1]}
    if "type" in propiedad:
        tipos.add(propiedad["type"])
    for rama in propiedad.get("anyOf", []) or []:
        if "$ref" in rama:
            tipos.add("ref:" + rama["$ref"].split("/")[-1])
        elif "type" in rama:
            tipos.add(rama["type"])
    if "items" in propiedad:
        tipos.add("array")
    return tipos or {"desconocido"}


def principal() -> None:
    """Compara dos archivos OpenAPI y falla ante cualquier ruptura."""
    if len(sys.argv) != 3:
        print("Uso: verificar_aditividad.py base.json actual.json")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as archivo:
        base = json.load(archivo)
    with open(sys.argv[2], encoding="utf-8") as archivo:
        actual = json.load(archivo)
    rupturas = es_aditivo(base, actual)
    if rupturas:
        print("Contrato NO aditivo (Anexo C):")
        for ruptura in rupturas:
            print(f"  - {ruptura}")
        sys.exit(1)
    print("Contrato aditivo: conforme al Anexo C.")


if __name__ == "__main__":
    principal()
