"""Configuracion del contexto auditoria."""
from django.apps import AppConfig


class ConfiguracionAuditoria(AppConfig):
    """Registra el contexto transversal auditoria."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "aplicaciones.auditoria"
    label = "auditoria"
