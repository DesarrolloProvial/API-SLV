"""Pruebas de correlacion completa (sin BD real).

Verifican: el codigo del borde se reutiliza, `application_name` no rompe
en sqlite y el recurso se deriva sin datos personales.
"""
from django.test import SimpleTestCase

from aplicaciones.auditoria.propagador_correlacion import (
    propagar_correlacion_bd,
)
from aplicaciones.auditoria.registrador_consulta import recurso_desde_ruta


class PruebaCorrelacion(SimpleTestCase):
    """Borde, BD y recurso del codigo de correlacion."""

    def test_codigo_del_borde_se_reutiliza(self):
        """Con cabecera valida, cuerpo y cabecera traen el mismo codigo."""
        respuesta = self.client.get(
            "/api/v1/vehiculos/inexistente",
            HTTP_X_CODIGO_CORRELACION="borde-12345678",
        )
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()["codigo_correlacion"], "borde-12345678")
        self.assertEqual(respuesta["X-Codigo-Correlacion"], "borde-12345678")

    def test_codigo_invalido_del_borde_se_ignora(self):
        """Cabecera corta o con espacios: se genera uno nuevo."""
        respuesta = self.client.get(
            "/api/v1/vehiculos/inexistente", HTTP_X_CODIGO_CORRELACION="corto"
        )
        self.assertNotEqual(respuesta.json()["codigo_correlacion"], "corto")

    def test_application_name_no_rompe_sin_postgres(self):
        """En sqlite el `SET` se ignora sin levantar."""
        propagar_correlacion_bd("codigo-prueba-12345678")

    def test_recurso_desde_ruta_sin_personales(self):
        """La ruta con placa deriva al recurso, sin exponer la placa."""
        self.assertEqual(
            recurso_desde_ruta("/api/v1/vehiculos/C123ABC/expediente/refrendos"),
            "refrendos",
        )
        self.assertEqual(
            recurso_desde_ruta("/api/v1/vehiculos/buscar"), "buscar"
        )
        self.assertEqual(recurso_desde_ruta("/salud"), "salud")
        self.assertEqual(recurso_desde_ruta("/otra/cosa"), "otro")
