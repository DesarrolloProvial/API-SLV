"""Configuracion del contexto historial."""
from django.apps import AppConfig


class ConfiguracionHistorial(AppConfig):
    """Registra el contexto historial."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.historial"
    label = "historial"
