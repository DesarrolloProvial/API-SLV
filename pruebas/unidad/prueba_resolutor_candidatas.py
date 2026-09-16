"""Pruebas del resolutor de candidatas (logica pura, sin BD)."""
from django.test import SimpleTestCase

from aplicaciones.vehiculos.servicios.resolutor_candidatas import (
    extraer_sufijo_y_tipo,
    resolver_por_sufijo_y_tipo,
)


def _fila(placa_norma, **extras):
    """Construye una fila minima del selector."""
    base = {
        "placa_norma": placa_norma,
        "placa": placa_norma,
        "marca": "Toyota",
        "linea": "Hilux",
        "modelo": "2020",
        "empresa_implementadora": "Empresa X",
    }
    base.update(extras)
    return base


class PruebaExtraerSufijoYTipo(SimpleTestCase):
    """Derivacion de sufijo6 y tipo desde la placa normalizada."""

    def test_extrae_sufijo_y_letra(self):
        """C123ABC da sufijo 123ABC y tipo C."""
        self.assertEqual(extraer_sufijo_y_tipo("C123ABC"), ("123ABC", "C"))

    def test_parcial_y_vacio_no_resuelven(self):
        """Sin sufijo valido no hay resolucion (sera 404 uniforme)."""
        self.assertIsNone(extraer_sufijo_y_tipo("C12"))
        self.assertIsNone(extraer_sufijo_y_tipo(""))
        self.assertIsNone(extraer_sufijo_y_tipo("12AB"))


class PruebaResolverCandidatas(SimpleTestCase):
    """Variantes del mismo tipo como candidatas; tipo distinto nunca."""

    def test_tipo_distinto_jamas_aparece(self):
        """P123ABC no sale ante consulta de tipo C."""
        filas = [_fila("C123ABC"), _fila("P123ABC")]
        candidatas, truncado = resolver_por_sufijo_y_tipo("123ABC", "C", filas)
        self.assertEqual([c["placa"] for c in candidatas], ["C123ABC"])
        self.assertFalse(truncado)

    def test_variantes_del_mismo_tipo_y_truncado(self):
        """Tres variantes salen juntas; el tope marca truncado sin conteos."""
        filas = [_fila("C123ABC"), _fila("C0123ABC"), _fila("CO123ABC")]
        candidatas, truncado = resolver_por_sufijo_y_tipo(
            "123ABC", "C", filas, tope=2
        )
        self.assertEqual(len(candidatas), 2)
        self.assertTrue(truncado)
        self.assertIn("expediente", candidatas[0]["vinculos"])
