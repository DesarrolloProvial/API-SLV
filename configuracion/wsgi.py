"""Punto WSGI para gunicorn (solo lectura del espejo)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuracion.ajustes_produccion")

aplicacion = get_wsgi_application()
