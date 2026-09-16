"""Ajustes de preproduccion (postgres espejo, sin depurar)."""
from .ajustes_base import *  # noqa: F401,F403

DEPURAR = False
DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": BASES_DATOS_NOMBRE,  # noqa: F405
        "USER": BASES_DATOS_USUARIO,  # noqa: F405
        "PASSWORD": BASES_DATOS_CLAVE,  # noqa: F405
        "HOST": BASES_DATOS_ANFITRION,  # noqa: F405
        "PORT": BASES_DATOS_PUERTO,  # noqa: F405
        "OPTIONS": {"sslmode": "verify-full"},
    }
}
