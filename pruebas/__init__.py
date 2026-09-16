"""Pruebas del esqueleto base."""
import os
import unittest


def load_tests(loader, tests, ignore=None):
    """Descubre `prueba_*.py` bajo este paquete.

    Args:
        loader: Cargador de pruebas de unittest.
        tests: Conjunto inicial (sin usar).
        ignore: Patrones a ignorar.

    Returns:
        TestSuite: Conjunto descubierto en subpaquetes.
    """
    aqui = os.path.dirname(__file__)
    raiz = os.path.dirname(aqui)
    return loader.discover(
        start_dir=aqui, pattern="prueba*.py", top_level_dir=raiz
    )


__all__ = ["load_tests"]
