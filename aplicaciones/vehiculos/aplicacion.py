"""Configuracion del contexto vehiculos."""
from django.apps import AppConfig


class ConfiguracionVehiculos(AppConfig):
    """Registra el contexto vehiculos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.vehiculos"
    label = "vehiculos"
