"""Pruebas del registro estructurado (codigo de primer nivel).

Verifican que `registrar_consulta` expone `codigo_correlacion` como campo
JSON propio (para Loki) manteniendo el texto historico del mensaje.
"""
import json

from django.test import SimpleTestCase

from aplicaciones.auditoria.registrador_consulta import (
    FormateadorConsulta,
    registrar_consulta,
)


class PruebaRegistradorConsulta(SimpleTestCase):
    """Codigo de correlacion como campo, no solo texto."""

    def test_codigo_como_campo_json_de_primer_nivel(self):
        """El codigo sale como campo propio con recurso/estado/cliente."""
        with self.assertLogs("intercambio.consulta", level="INFO") as capturado:
            registrar_consulta(
                "codigo-campo-12345678", "buscar", 200,
                cliente="dgt-intercambio",
            )
        self.assertEqual(len(capturado.records), 1)
        registro = capturado.records[0]
        self.assertEqual(registro.codigo_correlacion, "codigo-campo-12345678")
        linea = json.loads(FormateadorConsulta().format(registro))
        self.assertEqual(linea["codigo_correlacion"], "codigo-campo-12345678")
        self.assertEqual(linea["recurso"], "buscar")
        self.assertEqual(linea["estado"], 200)
        self.assertEqual(linea["cliente"], "dgt-intercambio")
        for clave in ("tiempo", "nivel", "origen", "mensaje"):
            self.assertIn(clave, linea)

    def test_texto_historico_se_mantiene(self):
        """El mensaje sigue con el formato `recurso/estado/codigo`."""
        with self.assertLogs("intercambio.consulta", level="INFO") as capturado:
            registrar_consulta("codigo-texto-12345678", "salud", 200)
        self.assertIn("codigo-texto-12345678", capturado.output[0])
        linea = json.loads(
            FormateadorConsulta().format(capturado.records[0])
        )
        self.assertEqual(linea["cliente"], "")
