"""Pruebas de enrutadores con selectores simulados (sin BD).

Verifican el contrato: 404 uniforme, `codigo_correlacion` en cuerpo y
cabecera, `Cache-Control: no-store` y forma de cada respuesta.
"""
from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from pruebas.ayuda_autenticacion import (
    TODOS_LOS_AMBITOS,
    cabecera_autorizacion,
)

FILA_EXPEDIENTE = {
    "placa_norma": "C123ABC",
    "placa": "C123ABC",
    "chasis": "CH123",
    "marca": "Toyota",
    "linea": "Hilux",
    "modelo": "2020",
    "serie": "S1",
    "tipo_placa": "guatemalteca",
    "clasificacion": "Pick-up",
    "tipo_vehiculo": "Carga",
    "uso": "Comercial",
    "color": "Blanco",
    "departamento": "Guatemala",
    "municipio": "Guatemala",
    "motor": "M1",
    "asientos": 5,
    "ejes": 2,
    "cilindraje": 2.5,
    "centimetros_cubicos": 2500.0,
    "toneladas": 1.0,
    "codigo_correlativo": "CORR1",
    "estado_aprobacion": "aprobado",
    "activa": True,
    "fecha_codigo": date(2024, 1, 15),
    "tipo_slv_codigo": "T1",
    "tipo_slv_nombre": "Tipo 1",
    "refrendo_codigo": "R1",
    "refrendo_fecha": date(2025, 3, 1),
    "refrendo_vencimiento": date(2026, 3, 1),
    "refrendo_estado": "vigente",
    "propietario_nombre": "Empresa Y",
    "empresa_nombre": "Empresa X",
    "empresa_autorizacion": "AUT1",
    "empresa_esta_autorizada": True,
    "vin": "RESTRINGIDO",
    "tarjeta_circulacion": "RESTRINGIDA",
}


class PruebaContratoComun(SimpleTestCase):
    """404 uniforme, correlacion y no-store en los tres endpoints."""

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

    def test_buscar_invalido_da_404_uniforme(self):
        """Placa parcial o vacia: mismo 404 que un inexistente."""
        for valor in ("C12", "12AB", ""):
            with self.subTest(valor=valor):
                self._verificar_404(
                    self.client.get(
                        f"/api/v1/vehiculos/buscar?placa={valor}",
                        **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                    )
                )

    def test_expediente_y_generales_ausentes_dan_404(self):
        """Placa exacta sin ficha: mismo 404 sin distinguir causa."""
        with patch(
            "aplicaciones.vehiculos.enrutador_expediente.obtener_por_placa_exacta",
            return_value=None,
        ):
            self._verificar_404(
                self.client.get(
                    "/api/v1/vehiculos/C999ZZZ/expediente",
                    **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                )
            )
            self._verificar_404(
                self.client.get(
                    "/api/v1/vehiculos/C999ZZZ/expediente/generales",
                    **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                )
            )

    def test_ruta_inexistente_da_404_uniforme(self):
        """Fuera de contrato tambien hay 404 uniforme con no-store."""
        self._verificar_404(self.client.get("/api/v1/vehiculos/inexistente"))


class PruebaRutasExitosas(SimpleTestCase):
    """Respuestas 200 con correlacion, no-store y claves en espanol."""

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

    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[{"placa_norma": "C123ABC", "placa": "C123ABC"}],
    )
    def test_buscar_devuelve_candidata_y_truncado(self, _buscar):
        """Buscar responde candidatas con vinculo y `truncado`."""
        cuerpo = self._verificar_200(
            self.client.get(
                "/api/v1/vehiculos/buscar?placa=C123ABC",
                **cabecera_autorizacion(TODOS_LOS_AMBITOS),
            )
        )
        self.assertEqual(cuerpo["placa"], "C123ABC")
        self.assertEqual(len(cuerpo["candidatas"]), 1)
        self.assertFalse(cuerpo["truncado"])
        self.assertIn(
            "expediente", cuerpo["candidatas"][0]["vinculos"]
        )

    @patch(
        "aplicaciones.vehiculos.enrutador_expediente.obtener_por_placa_exacta",
        return_value=dict(FILA_EXPEDIENTE),
    )
    def test_expediente_sin_restringidos(self, _obtener):
        """Expediente trae vehiculo/vinculacion/refrendo sin vin ni tarjeta."""
        cuerpo = self._verificar_200(
            self.client.get(
                "/api/v1/vehiculos/C123ABC/expediente",
                **cabecera_autorizacion(TODOS_LOS_AMBITOS),
            )
        )
        self.assertIn("vehiculo", cuerpo)
        self.assertIn("vinculacion", cuerpo)
        self.assertEqual(cuerpo["refrendo_vigente"]["codigo"], "R1")
        self.assertIn("generales", cuerpo["vinculos"])
        texto = str(cuerpo)
        self.assertNotIn("RESTRINGIDO", texto)
        self.assertNotIn("RESTRINGIDA", texto)

    @patch(
        "aplicaciones.vehiculos.enrutador_expediente.obtener_por_placa_exacta",
        return_value=dict(FILA_EXPEDIENTE, refrendo_codigo=None, refrendo_fecha=None),
    )
    def test_generales_sin_refrendo(self, _obtener):
        """Generales trae el subconjunto y refrendo ausente no rompe."""
        cuerpo = self._verificar_200(
            self.client.get(
                "/api/v1/vehiculos/C123ABC/expediente/generales",
                **cabecera_autorizacion(TODOS_LOS_AMBITOS),
            )
        )
        self.assertIn("generales", cuerpo)
        self.assertEqual(cuerpo["generales"]["marca"], "Toyota")
        self.assertNotIn("vinculacion", cuerpo)
