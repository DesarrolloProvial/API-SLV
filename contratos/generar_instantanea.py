"""Genera el OpenAPI actual a un archivo (CI y revision humana).

Uso:
    python contratos/generar_instantanea.py --salida /tmp/openapi_actual.json
"""
import argparse
import json
import os
import sys

import django


def principal() -> None:
    """Arranca Django, pide `/api/openapi.json` y lo guarda formateado."""
    parser = argparse.ArgumentParser(description="Genera el OpenAPI actual.")
    parser.add_argument("--salida", required=True, help="Archivo de destino.")
    args = parser.parse_args()
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "configuracion.ajustes_desarrollo"
    )
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()
    from django.test import Client

    respuesta = Client().get("/api/openapi.json", HTTP_HOST="testserver")
    if respuesta.status_code != 200:
        print(f"openapi.json devolvio {respuesta.status_code}", file=sys.stderr)
        sys.exit(1)
    with open(args.salida, "w", encoding="utf-8") as archivo:
        json.dump(respuesta.json(), archivo, indent=2, sort_keys=True)
        archivo.write("\n")
    print(f"OpenAPI actual en {args.salida}")


if __name__ == "__main__":
    principal()
