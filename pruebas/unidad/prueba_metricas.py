"""Pruebas de metricas internas (sin BD ni red).

Verifican: `/metricas` responde en red interna y niega la externa sin
fuga, cada peticion cuenta con latencia, `buscar` suma busqueda y
candidatas, la entrega suma por ambito, y el codigo nunca es etiqueta.
"""
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from aplicaciones.auditoria.metricas_negocio import (
    exponer_metricas,
    limpiar_metricas,
    observar_error_bd,
)
from pruebas.ayuda_autenticacion import (
    TODOS_LOS_AMBITOS,
    cabecera_autorizacion,
)
from pruebas.unidad.prueba_enrutadores_vehiculos import FILA_EXPEDIENTE


class PruebaMetricas(SimpleTestCase):
    """Endpoint interno y contadores de servicio y negocio."""

    def setUp(self):
        """Vacia las metricas antes de cada prueba."""
        limpiar_metricas()

    def tearDown(self):
        """Vacia las metricas despues de cada prueba."""
        limpiar_metricas()

    def test_metricas_responde_en_red_interna(self):
        """En local expone el texto Prometheus con los contadores."""
        respuesta = self.client.get("/metricas")
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta["Content-Type"].startswith("text/plain"))
        self.assertIn(
            "intercambio_peticiones_total",
            respuesta.content.decode("utf-8"),
        )

    def test_metricas_niega_red_externa_sin_fuga(self):
        """Fuera de la red interna hay 404 uniforme, sin metricas."""
        respuesta = self.client.get("/metricas", REMOTE_ADDR="8.8.8.8")
        self.assertEqual(respuesta.status_code, 404)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "no_encontrado")
        self.assertTrue(cuerpo["codigo_correlacion"])

    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[{"placa_norma": "C123ABC", "placa": "C123ABC"}],
    )
    def test_buscar_cuenta_peticion_busqueda_y_candidatas(self, _buscar):
        """Un 200 en `buscar` suma peticion, busqueda y candidatas."""
        respuesta = self.client.get(
            "/api/v1/vehiculos/buscar?placa=C123ABC",
            **cabecera_autorizacion(TODOS_LOS_AMBITOS),
        )
        self.assertEqual(respuesta.status_code, 200)
        contenido = exponer_metricas()
        self.assertIn(
            'intercambio_peticiones_total{recurso="buscar",estado="200",'
            'cliente="dgt-intercambio"} 1.0',
            contenido,
        )
        self.assertIn("intercambio_busquedas_total 1.0", contenido)
        self.assertIn("intercambio_candidatas_total 1.0", contenido)

    @patch(
        "aplicaciones.vehiculos.enrutador_expediente.obtener_por_placa_exacta",
        return_value=dict(FILA_EXPEDIENTE),
    )
    def test_expediente_cuenta_entrega_por_ambito(self, _ficha):
        """Un 200 en expediente suma la entrega bajo su ambito."""
        respuesta = self.client.get(
            "/api/v1/vehiculos/C123ABC/expediente",
            **cabecera_autorizacion(TODOS_LOS_AMBITOS),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            'intercambio_entregas_total{recurso="expediente",'
            'ambito="vehiculos.lectura"} 1.0',
            exponer_metricas(),
        )

    @override_settings(LIMITE_BUSCAR_TOPE=1, VENTANA_LIMITE_SEG=60)
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[{"placa_norma": "C123ABC", "placa": "C123ABC"}],
    )
    def test_cuota_excedida_cuenta_limite(self, _buscar):
        """El 429 suma al contador de limites del recurso."""
        from aplicaciones.seguridad.aplicador_limites import limpiar_limites

        limpiar_limites()
        try:
            ruta = "/api/v1/vehiculos/buscar?placa=C123ABC"
            extra = cabecera_autorizacion(TODOS_LOS_AMBITOS)
            self.assertEqual(self.client.get(ruta, **extra).status_code, 200)
            self.assertEqual(self.client.get(ruta, **extra).status_code, 429)
            self.assertIn(
                'intercambio_limites_total{recurso="buscar"} 1.0',
                exponer_metricas(),
            )
        finally:
            limpiar_limites()

    def test_codigo_nunca_es_etiqueta(self):
        """El codigo viaja en el registro, no en las etiquetas."""
        self.client.get(
            "/api/v1/vehiculos/inexistente",
            HTTP_X_CODIGO_CORRELACION="borde-metrica-12345678",
        )
        contenido = exponer_metricas()
        self.assertNotIn("codigo_correlacion", contenido)
        self.assertNotIn("borde-metrica-12345678", contenido)

    def test_error_bd_se_cuenta(self):
        """El gancho de BD suma al contador operativo."""
        observar_error_bd()
        self.assertIn(
            "intercambio_errores_bd_total 1.0", exponer_metricas()
        )
