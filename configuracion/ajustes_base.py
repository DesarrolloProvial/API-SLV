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

#: Aliases exigidos por Django (nombres del ecosistema; el canonico en
#: espanol vive arriba). Sin estos, `SECRET_KEY` vacia rompe el arranque
#: y `testserver`/dominios reales fallan por `ALLOWED_HOSTS`.
SECRET_KEY = LLAVE_SECRETA
ALLOWED_HOSTS = list(ANFITRIONES_PERMITIDOS)
DEBUG = DEPURAR

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

#: Topes de dia 0 (calibrables por convenio; el codigo los relee via
#: `getattr(settings, ...)` para no recompilar al calibrar).
TOPE_CANDIDATAS = int(os.getenv("TOPE_CANDIDATAS", "10"))
TOPE_REFERENDOS = int(os.getenv("TOPE_REFERENDOS", "10"))
TOPE_HISTORIAL = int(os.getenv("TOPE_HISTORIAL", "10"))

#: Keycloak/JWKS (nombres; sin valores ni secretos en el repo).
URL_JWKS = os.getenv("URL_JWKS", "")
EMISOR_JWT = os.getenv("EMISOR_JWT", "")
AUDIENCIA_JWT = os.getenv("AUDIENCIA_JWT", "")
TOLERANCIA_RELOJ_SEG = int(os.getenv("TOLERANCIA_RELOJ_SEG", "30"))
TIEMPO_CACHE_JWKS_SEG = int(os.getenv("TIEMPO_CACHE_JWKS_SEG", "600"))
#: Lista de `jti` revocados (emergencia; lo real es Keycloak + borde).
TOKENS_REVOCADOS = [
    j for j in os.getenv("TOKENS_REVOCADOS", "").split(",") if j
]

#: Limites multicapa lado API (dia 0, a calibrar en convenio; el borde
#: nginx/WAF lleva los suyos). `buscar` es la mas estricta.
LIMITE_BUSCAR_TOPE = int(os.getenv("LIMITE_BUSCAR_TOPE", "30"))
LIMITE_RECURSO_TOPE = int(os.getenv("LIMITE_RECURSO_TOPE", "60"))
VENTANA_LIMITE_SEG = int(os.getenv("VENTANA_LIMITE_SEG", "60"))

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

#: Registro estructurado con `codigo_correlacion` (JSON por linea, sin
#: personales ni secretos; fase 4 lo promueve a Loki/Prometheus).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": (
                '{"tiempo": "%(asctime)s", "nivel": "%(levelname)s", '
                '"origen": "%(name)s", "mensaje": "%(message)s"}'
            ),
        },
    },
    "handlers": {
        "consola": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "intercambio.consulta": {
            "handlers": ["consola"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
