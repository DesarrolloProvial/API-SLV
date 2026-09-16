"""Configuracion del contexto seguridad."""
from django.apps import AppConfig


class ConfiguracionSeguridad(AppConfig):
    """Registra el contexto transversal seguridad."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.seguridad"
    label = "seguridad"
