"""Pruebas del normalizador de placas (logica pura, sin BD)."""
from django.test import SimpleTestCase

from aplicaciones.vehiculos.servicios.normalizador_placa import normalizar_placa


class PruebaNormalizadorPlaca(SimpleTestCase):
    """Trim, mayusculas y limpieza de espacios y guiones."""

    def test_mayuscula_y_limpia(self):
        """Normaliza una placa con espacios y guiones."""
        self.assertEqual(normalizar_placa("  c-123 abc "), "C123ABC")

    def test_vacia_y_nula_devuelven_vacio(self):
        """Entradas vacias no rompen: terminaran en 404 uniforme."""
        self.assertEqual(normalizar_placa(""), "")
        self.assertEqual(normalizar_placa(None), "")
