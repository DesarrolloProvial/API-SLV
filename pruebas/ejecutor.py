"""Ejecutor de pruebas con patron de nombres en espanol."""
from django.test.runner import DiscoverRunner


class EjecutorEspanol(DiscoverRunner):
    """Descubre archivos `prueba_*.py` en lugar de `test_*.py`."""

    pattern = "prueba*.py"
