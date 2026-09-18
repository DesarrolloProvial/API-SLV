"""Ajustes de preproduccion (postgres espejo, sin depurar)."""
from django.core.exceptions import ImproperlyConfigured

from .ajustes_base import *  # noqa: F401,F403

DEPURAR = False
DEBUG = False

# 0.2/3.4: preproduccion exige `URL_JWKS` (solo nombre, sin valores); sin
# IdP la API caeria al HS256 solo-local. Fase 1 de borde fuera.
if not URL_JWKS:  # noqa: F405
    raise ImproperlyConfigured(
        "URL_JWKS vacia en preproduccion: sin JWKS la API caeria a HS256 local."
    )

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
