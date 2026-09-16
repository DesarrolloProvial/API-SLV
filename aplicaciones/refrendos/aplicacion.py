"""Configuracion del contexto refrendos."""
from django.apps import AppConfig


class ConfiguracionRefrendos(AppConfig):
    """Registra el contexto refrendos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.refrendos"
    label = "refrendos"
