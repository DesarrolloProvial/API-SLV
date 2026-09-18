"""Ajustes de produccion (endurecido tras el tunel)."""
from django.core.exceptions import ImproperlyConfigured

from .ajustes_base import *  # noqa: F401,F403

DEPURAR = False
DEBUG = False

if LLAVE_SECRETA in (  # noqa: F405
    "",
    "insegura-solo-desarrollo-cambiar-en-produccion",
):
    raise ImproperlyConfigured(
        "LLAVE_SECRETA insegura en produccion: defina el secreto por entorno."
    )
if not BASES_DATOS_CLAVE:  # noqa: F405
    raise ImproperlyConfigured(
        "CLAVE_BD vacia en produccion: defina la clave del lector."
    )
if not URL_JWKS:  # noqa: F405
    # 0.2/3.4: sin JWKS la API caeria al HS256 solo-local; falla cerrado.
    raise ImproperlyConfigured(
        "URL_JWKS vacia en produccion: sin JWKS la API caeria a HS256 local."
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": BASES_DATOS_NOMBRE,  # noqa: F405
        "USER": BASES_DATOS_USUARIO,  # noqa: F405
        "PASSWORD": BASES_DATOS_CLAVE,  # noqa: F405
        "HOST": BASES_DATOS_ANFITRION,  # noqa: F405
        "PORT": BASES_DATOS_PUERTO,  # noqa: F405
        "OPTIONS": {"sslmode": "verify-full"},
        "CONN_MAX_AGE": 60,
    }
}
