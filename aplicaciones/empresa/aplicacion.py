"""Configuracion del contexto empresa."""
from django.apps import AppConfig


class ConfiguracionEmpresa(AppConfig):
    """Registra el contexto empresa."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.empresa"
    label = "empresa"
