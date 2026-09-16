"""Servicios puros del contexto empresa (sin E/S ni BD)."""
from aplicaciones.empresa.servicios.armador_empresa import armar_empresa

__all__ = ["armar_empresa"]
