"""Pruebas negativas de privilegios del rol lector."""
import os
import unittest


def load_tests(loader, tests, ignore=None):
    """Descubre `prueba_*.py` en este paquete.

    Args:
        loader: Cargador de pruebas de unittest.
        tests: Conjunto inicial (sin usar).
        ignore: Patrones a ignorar.

    Returns:
        TestSuite: Conjunto descubierto en este paquete.
    """
    aqui = os.path.dirname(__file__)
    raiz = os.path.dirname(os.path.dirname(aqui))
    return loader.discover(
        start_dir=aqui, pattern="prueba*.py", top_level_dir=raiz
    )


__all__ = ["load_tests"]
