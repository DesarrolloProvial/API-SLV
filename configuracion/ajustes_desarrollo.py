"""Ajustes de desarrollo local (sqlite, sin endurecer)."""
from .ajustes_base import *  # noqa: F401,F403

DEPURAR = True
DEBUG = True
ANFITRIONES_PERMITIDOS = ["*"]
ALLOWED_HOSTS = list(ANFITRIONES_PERMITIDOS)
