"""Pruebas de subrecursos singulares con selectores simulados (sin BD).

Mismo estilo de PR4: 404 uniforme, `codigo_correlacion` en cuerpo y
cabecera, `Cache-Control: no-store` y forma de cada respuesta.
"""
from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

FILA_PROPIETARIO = {
    "placa_norma": "C123ABC",
    "placa": "C123ABC",
    "vigente_desde": date(2023, 5, 1),
    "vigente_hasta": None,
    "nombre_empresa": "Transportes Ejemplo",
}

FILA_EMPRESA = {
    "placa_norma": "C123ABC",
    "placa": "C123ABC",
    "codigo_correlativo": "CORR1",
    "estado_aprobacion": "aprobado",
    "activa": True,
    "nombre_empresa": "Empresa X",
    "numero_autorizacion": "AUT1",
    "esta_autorizada": True,
    "fecha_autorizacion": date(2024, 2, 1),
}

EXPEDIENTE_MINIMO = {"placa_norma": "C123ABC"}


class PruebaSubrecursosSingulares(SimpleTestCase):
    """Contrato 404/200 de propietario y empresa."""

    def _verificar_404(self, respuesta):
        """El 404 no distingue causa y siempre trae correlacion."""
        self.assertEqual(respuesta.status_code, 404)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "no_encontrado")
        self.assertTrue(cuerpo["mensaje"])
        self.assertTrue(cuerpo["codigo_correlacion"])
        self.assertEqual(
            respuesta["X-Codigo-Correlacion"], cuerpo["codigo_correlacion"]
        )
        self.assertEqual(respuesta["Cache-Control"], "no-store")

    def _verificar_200(self, respuesta):
        """Toda respuesta exitosa trae correlacion y no-store."""
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertTrue(cuerpo["codigo_correlacion"])
        self.assertEqual(
            respuesta["X-Codigo-Correlacion"], cuerpo["codigo_correlacion"]
        )
        self.assertEqual(respuesta["Cache-Control"], "no-store")
        return cuerpo

    def test_propietario_sin_expediente_da_404(self):
        """Extranjera no autorizada o ausente: mismo 404 sin dato."""
        with patch(
            "aplicaciones.propietario.enrutador_propietario.obtener_por_placa_exacta",
            return_value=None,
        ):
            self._verificar_404(
                self.client.get("/api/v1/vehiculos/C123ABC/expediente/propietario")
            )

    def test_propietario_sin_vigente_da_404(self):
        """Expediente vigente pero sin titularidad vigente: 404 uniforme."""
        with (
            patch(
                "aplicaciones.propietario.enrutador_propietario.obtener_por_placa_exacta",
                return_value=dict(EXPEDIENTE_MINIMO),
            ),
            patch(
                "aplicaciones.propietario.enrutador_propietario.obtener_propietario",
                return_value=None,
            ),
        ):
            self._verificar_404(
                self.client.get("/api/v1/vehiculos/C123ABC/expediente/propietario")
            )

    @patch(
        "aplicaciones.propietario.enrutador_propietario.obtener_por_placa_exacta",
        return_value=dict(EXPEDIENTE_MINIMO),
    )
    @patch(
        "aplicaciones.propietario.enrutador_propietario.obtener_propietario",
        return_value=dict(FILA_PROPIETARIO),
    )
    def test_propietario_devuelve_vigente_y_vinculos(self, _prop, _exp):
        """Propietario trae datos minimos y los 6 vinculos."""
        cuerpo = self._verificar_200(
            self.client.get("/api/v1/vehiculos/C123ABC/expediente/propietario")
        )
        self.assertEqual(cuerpo["placa"], "C123ABC")
        self.assertEqual(
            cuerpo["propietario"]["nombre_empresa"], "Transportes Ejemplo"
        )
        for clave in (
            "expediente", "generales", "propietario",
            "empresa", "refrendos", "historial",
        ):
            self.assertIn(clave, cuerpo["vinculos"])

    def test_empresa_sin_expediente_da_404(self):
        """Extranjera no autorizada o ausente: mismo 404 sin dato."""
        with patch(
            "aplicaciones.empresa.enrutador_empresa.obtener_por_placa_exacta",
            return_value=None,
        ):
            self._verificar_404(
                self.client.get("/api/v1/vehiculos/C123ABC/expediente/empresa")
            )

    @patch(
        "aplicaciones.empresa.enrutador_empresa.obtener_por_placa_exacta",
        return_value=dict(EXPEDIENTE_MINIMO),
    )
    @patch(
        "aplicaciones.empresa.enrutador_empresa.obtener_empresa",
        return_value=dict(FILA_EMPRESA),
    )
    def test_empresa_devuelve_vigente_y_vinculos(self, _emp, _exp):
        """Empresa trae autorizacion operativa y los 6 vinculos."""
        cuerpo = self._verificar_200(
            self.client.get("/api/v1/vehiculos/C123ABC/expediente/empresa")
        )
        self.assertEqual(cuerpo["empresa"]["numero_autorizacion"], "AUT1")
        self.assertTrue(cuerpo["empresa"]["esta_autorizada"])
        for clave in (
            "expediente", "generales", "propietario",
            "empresa", "refrendos", "historial",
        ):
            self.assertIn(clave, cuerpo["vinculos"])
