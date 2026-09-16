#!/usr/bin/env python
"""Punto de entrada de gestion Django."""
import os
import sys


def principal() -> None:
    """Ejecuta la utilidad de administracion de Django."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "configuracion.ajustes_desarrollo"
    )
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    principal()
