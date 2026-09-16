"""Ajustes compartidos por todos los entornos."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LLAVE_SECRETA = os.getenv(
    "LLAVE_SECRETA", "insegura-solo-desarrollo-cambiar-en-produccion"
)
DEPURAR = False

ANFITRIONES_PERMITIDOS = [
    h for h in os.getenv("ANFITRIONES_PERMITIDOS", "").split(",") if h
]

APLICACIONES_PROPIAS = [
    "aplicaciones.vehiculos",
    "aplicaciones.propietario",
    "aplicaciones.empresa",
    "aplicaciones.refrendos",
    "aplicaciones.historial",
    "aplicaciones.seguridad",
    "aplicaciones.auditoria",
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    *APLICACIONES_PROPIAS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "aplicaciones.auditoria.propagador_correlacion.MiddlewareCodigoCorrelacion",
]

#: Alias de lectura del espejo (el `default` apunta al espejo en produccion).
ALIAS_ESPEJO = os.getenv("ALIAS_ESPEJO", "default")

#: Placas extranjeras solo si el convenio las autoriza (spec consulta).
PERMITIR_PLACAS_EXTRANJERAS = os.getenv("PERMITIR_PLACAS_EXTRANJERAS", "") == "1"

ROOT_URLCONF = "configuracion.enrutado_principal"

BASES_DATOS_NOMBRE = os.getenv("NOMBRE_BD", "espejo")
BASES_DATOS_USUARIO = os.getenv("USUARIO_BD", "lector")
BASES_DATOS_CLAVE = os.getenv("CLAVE_BD", "")
BASES_DATOS_ANFITRION = os.getenv("ANFITRION_BD", "localhost")
BASES_DATOS_PUERTO = os.getenv("PUERTO_BD", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "es-gt"
TIME_ZONE = "America/Guatemala"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEST_RUNNER = "pruebas.ejecutor.EjecutorEspanol"
