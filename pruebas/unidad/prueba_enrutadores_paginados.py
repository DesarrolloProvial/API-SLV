"""Pruebas de refrendos e historial con selectores simulados (sin BD).

Verifican paginacion con cursor opaco: primera pagina, siguiente con
cursor real, cursor manipulado y de otra placa -> 404 uniforme, mas
correlacion y no-store en cada respuesta.
"""
from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from pruebas.ayuda_autenticacion import (
    TODOS_LOS_AMBITOS,
    cabecera_autorizacion,
)

from aplicaciones.seguridad.cursor_opaco import emitir_cursor

EXPEDIENTE = {"placa_norma": "C123ABC", "placa": "C123ABC"}

FILAS_REFRENDOS = [
    {
        "placa_norma": "C123ABC",
        "placa": "C123ABC",
        "codigo_refrendo": f"R{i:02d}",
        "fecha_refrendo": date(2025, 1, 1),
        "fecha_vencimiento": date(2026, 1, 1),
        "estado": "vigente",
        "vigencia_anios": 1,
    }
    for i in range(3)
]

FILAS_HISTORIAL = [
    {
        "placa_norma": "C123ABC",
        "placa": "C123ABC",
        "codigo_correlativo": f"CORR{i:02d}",
        "estado_aprobacion": "aprobado",
        "activa": True,
        "vigente_desde": date(2024, 1, 1),
        "fecha_baja": None,
        "motivo_baja_codigo": None,
        "empresa_implementadora": "Empresa X",
    }
    for i in range(3)
]


class PruebaSubrecursosPaginados(SimpleTestCase):
    """Contrato 404/200 con cursor de refrendos e historial."""

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

    def test_refrendos_sin_expediente_da_404(self):
        """Extranjera no autorizada o ausente: mismo 404 sin dato."""
        with patch(
            "aplicaciones.refrendos.enrutador_refrendos.obtener_por_placa_exacta",
            return_value=None,
        ):
            self._verificar_404(
                self.client.get("/api/v1/vehiculos/C123ABC/expediente/refrendos", **cabecera_autorizacion(TODOS_LOS_AMBITOS))
            )

    def test_refrendos_con_cursor_manipulado_da_404(self):
        """Cursor roto o firmado por otro filtro se rechaza sin dato."""
        with patch(
            "aplicaciones.refrendos.enrutador_refrendos.obtener_por_placa_exacta",
            return_value=dict(EXPEDIENTE),
        ):
            self._verificar_404(
                self.client.get(
                    "/api/v1/vehiculos/C123ABC/expediente/refrendos?cursor=roto",
                    **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                )
            )
            ajeno = emitir_cursor("P999ZZZ", 10)
            self._verificar_404(
                self.client.get(
                    f"/api/v1/vehiculos/C123ABC/expediente/refrendos?cursor={ajeno}",
                    **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                )
            )

    @patch(
        "aplicaciones.refrendos.enrutador_refrendos.obtener_por_placa_exacta",
        return_value=dict(EXPEDIENTE),
    )
    @patch(
        "aplicaciones.refrendos.enrutador_refrendos.paginar_refrendos",
        return_value=([{"codigo_refrendo": "R01"}], None),
    )
    def test_refrendos_ultima_pagina_sin_siguiente(self, _pag, _exp):
        """Pagina final trae elementos y `cursor_siguiente` nulo."""
        cuerpo = self._verificar_200(
            self.client.get("/api/v1/vehiculos/C123ABC/expediente/refrendos", **cabecera_autorizacion(TODOS_LOS_AMBITOS))
        )
        self.assertEqual(len(cuerpo["refrendos"]), 1)
        self.assertIsNone(cuerpo["cursor_siguiente"])
        self.assertIn("historial", cuerpo["vinculos"])

    def test_refrendos_pagina_con_siguiente_real(self):
        """Con 3 filas y tope 2 hay cursor siguiente que avanza."""
        from aplicaciones.refrendos.servicios.servicio_refrendos import (
            paginar_refrendos,
        )

        with patch(
            "aplicaciones.refrendos.servicios.servicio_refrendos.listar_refrendos",
            return_value=list(FILAS_REFRENDOS[:3]),
        ):
            elementos, siguiente = paginar_refrendos("C123ABC", None, tope=2)
            self.assertEqual(len(elementos), 2)
            self.assertTrue(siguiente)
            self.assertNotIn("C123ABC", siguiente)

    @patch(
        "aplicaciones.refrendos.enrutador_refrendos.obtener_por_placa_exacta",
        return_value=dict(EXPEDIENTE),
    )
    @patch(
        "aplicaciones.refrendos.enrutador_refrendos.paginar_refrendos",
        return_value=([{"codigo_refrendo": "R01"}], "opaco-siguiente"),
    )
    def test_refrendos_enrutador_expone_siguiente(self, _pag, _exp):
        """El enrutador expone el cursor siguiente sin totales."""
        cuerpo = self._verificar_200(
            self.client.get("/api/v1/vehiculos/C123ABC/expediente/refrendos", **cabecera_autorizacion(TODOS_LOS_AMBITOS))
        )
        self.assertEqual(cuerpo["cursor_siguiente"], "opaco-siguiente")
        self.assertNotIn("total", str(cuerpo).lower())

    def test_historial_sin_expediente_da_404(self):
        """Extranjera no autorizada o ausente: mismo 404 sin dato."""
        with patch(
            "aplicaciones.historial.enrutador_historial.obtener_por_placa_exacta",
            return_value=None,
        ):
            self._verificar_404(
                self.client.get("/api/v1/vehiculos/C123ABC/expediente/historial", **cabecera_autorizacion(TODOS_LOS_AMBITOS))
            )

    def test_historial_con_cursor_manipulado_da_404(self):
        """Cursor roto o de otra placa se rechaza sin dato."""
        with patch(
            "aplicaciones.historial.enrutador_historial.obtener_por_placa_exacta",
            return_value=dict(EXPEDIENTE),
        ):
            self._verificar_404(
                self.client.get(
                    "/api/v1/vehiculos/C123ABC/expediente/historial?cursor=roto",
                    **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                )
            )
            ajeno = emitir_cursor("P999ZZZ", 10)
            self._verificar_404(
                self.client.get(
                    f"/api/v1/vehiculos/C123ABC/expediente/historial?cursor={ajeno}",
                    **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                )
            )

    @patch(
        "aplicaciones.historial.enrutador_historial.obtener_por_placa_exacta",
        return_value=dict(EXPEDIENTE),
    )
    @patch(
        "aplicaciones.historial.enrutador_historial.paginar_historial",
        return_value=([{"codigo_correlativo": "CORR01"}], "siguiente-opaco"),
    )
    def test_historial_con_siguiente_opaco(self, _pag, _exp):
        """Pagina intermedia trae elementos y cursor sin totales."""
        cuerpo = self._verificar_200(
            self.client.get("/api/v1/vehiculos/C123ABC/expediente/historial", **cabecera_autorizacion(TODOS_LOS_AMBITOS))
        )
        self.assertEqual(len(cuerpo["historial"]), 1)
        self.assertEqual(cuerpo["cursor_siguiente"], "siguiente-opaco")
        self.assertNotIn("total", str(cuerpo).lower())
        self.assertNotIn("RESTRINGIDO", str(cuerpo))

    def test_historial_paginado_real_sin_totales(self):
        """Servicio real: 3 filas con tope 2 dan 2 + siguiente firmado."""
        from aplicaciones.historial.servicios.servicio_historial import (
            paginar_historial,
        )

        with patch(
            "aplicaciones.historial.servicios.servicio_historial.listar_historial",
            return_value=FILAS_HISTORIAL[:3],
        ):
            elementos, siguiente = paginar_historial("C123ABC", None, tope=2)
            self.assertEqual(len(elementos), 2)
            self.assertTrue(siguiente)
            self.assertNotIn("C123ABC", siguiente)
