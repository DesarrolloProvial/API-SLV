"""Prueba del esqueleto: salud y ajustes cargan."""
from django.test import SimpleTestCase


class PruebaEsqueleto(SimpleTestCase):
    """Verifica que la base responde y los ajustes cargan."""

    def test_salud_responde_correcto(self):
        """La ruta interna de salud responde estado correcto."""
        respuesta = self.client.get("/salud")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {"estado": "correcto"})

    def test_ajustes_por_defecto_cargan(self):
        """Los ajustes de desarrollo cargan sin secretos reales."""
        from django.conf import settings

        self.assertEqual(settings.ROOT_URLCONF, "configuracion.enrutado_principal")
        self.assertIn("aplicaciones.vehiculos", settings.INSTALLED_APPS)
