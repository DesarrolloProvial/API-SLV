"""Configuracion del contexto propietario."""
from django.apps import AppConfig


class ConfiguracionPropietario(AppConfig):
    """Registra el contexto propietario."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.propietario"
    label = "propietario"
