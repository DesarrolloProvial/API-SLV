"""Placas extranjeras: solo exacta con convenio, 404 uniforme sin el (spec)."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from aplicaciones.vehiculos.selectores.selector_busqueda import (
    buscar_por_sufijo,
    obtener_extranjera_exacta,
)
from aplicaciones.vehiculos.selectores.selector_expediente import (
    obtener_por_placa_exacta,
)
from pruebas.ayuda_autenticacion import (
    TODOS_LOS_AMBITOS,
    cabecera_autorizacion,
)
from pruebas.unidad.prueba_enrutadores_vehiculos import FILA_EXPEDIENTE

FILA_EXTRANJERA_BUSQUEDA = {
    "placa_norma": "E123ABC",
    "placa": "E123ABC",
    "marca": "Toyota",
    "linea": "Hilux",
    "modelo": "2020",
    "empresa_implementadora": "Empresa X",
}

FILA_EXPEDIENTE_EXTRANJERA = dict(
    FILA_EXPEDIENTE,
    placa_norma="E123ABC",
    placa="E123ABC",
    tipo_placa="extranjera",
)


def _cadena_busqueda():
    """Mock ORM con cadena filter/exclude/order/values."""
    cadena = MagicMock(name="consulta")
    cadena.filter.return_value = cadena
    cadena.exclude.return_value = cadena
    cadena.order_by.return_value = cadena
    cadena.values.return_value = cadena
    return cadena


class PruebaSufijoExcluyeExtranjeras(SimpleTestCase):
    """El sufijo nunca devuelve extranjeras, con o sin convenio."""

    def _ejecutar_con_flag(self, flag):
        """Ejecuta el sufijo con ORM simulado."""
        with override_settings(PERMITIR_PLACAS_EXTRANJERAS=flag):
            with patch(
                "aplicaciones.vehiculos.selectores.selector_busqueda."
                "VistaBusqueda"
            ) as modelo:
                cadena = _cadena_busqueda()
                cadena.__getitem__.return_value = [
                    {"placa_norma": "C123ABC"}
                ]
                modelo.objects.using.return_value = cadena
                filas = buscar_por_sufijo("123ABC", "C")
        return cadena, filas

    def test_sufijo_excluye_extranjera_con_flag_apagado(self):
        """Sin convenio el sufijo excluye `tipo=extranjera`."""
        cadena, filas = self._ejecutar_con_flag(False)
        cadena.exclude.assert_called_once_with(tipo="extranjera")
        cadena.order_by.assert_called_once_with("placa_norma")
        self.assertEqual(filas, [{"placa_norma": "C123ABC"}])

    def test_sufijo_excluye_extranjera_con_flag_encendido(self):
        """Con convenio el sufijo TAMPOCO devuelve extranjeras."""
        cadena, filas = self._ejecutar_con_flag(True)
        cadena.exclude.assert_called_once_with(tipo="extranjera")
        cadena.order_by.assert_called_once_with("placa_norma")
        self.assertEqual(filas, [{"placa_norma": "C123ABC"}])


class PruebaExactaExtranjeraSelector(SimpleTestCase):
    """La exacta solo resuelve con convenio y placa completa."""

    def test_exacta_con_flag_apagado_no_consulta_bd(self):
        """Sin convenio ni consulta: es como si no existiera."""
        with override_settings(PERMITIR_PLACAS_EXTRANJERAS=False):
            with patch(
                "aplicaciones.vehiculos.selectores.selector_busqueda."
                "VistaBusqueda"
            ) as modelo:
                self.assertIsNone(obtener_extranjera_exacta("E123ABC"))
                modelo.objects.assert_not_called()

    def test_exacta_con_flag_encendido_devuelve_fila(self):
        """Con convenio la exacta autorizada resuelve."""
        with override_settings(PERMITIR_PLACAS_EXTRANJERAS=True):
            with patch(
                "aplicaciones.vehiculos.selectores.selector_busqueda."
                "VistaBusqueda"
            ) as modelo:
                cadena = _cadena_busqueda()
                cadena.first.return_value = dict(FILA_EXTRANJERA_BUSQUEDA)
                modelo.objects.using.return_value = cadena
                fila = obtener_extranjera_exacta("E123ABC")
        self.assertEqual(fila, FILA_EXTRANJERA_BUSQUEDA)
        cadena.filter.assert_called_once_with(
            placa_norma="E123ABC", activa=True, tipo="extranjera"
        )

    def test_exacta_con_flag_encendido_sin_fila_da_none(self):
        """Con convenio pero sin fila exacta hay 404 en el llamador."""
        with override_settings(PERMITIR_PLACAS_EXTRANJERAS=True):
            with patch(
                "aplicaciones.vehiculos.selectores.selector_busqueda."
                "VistaBusqueda"
            ) as modelo:
                cadena = _cadena_busqueda()
                cadena.first.return_value = None
                modelo.objects.using.return_value = cadena
                self.assertIsNone(obtener_extranjera_exacta("E123ABD"))

    def test_exacta_vacia_da_none_sin_bd(self):
        """Vacia nunca consulta, con o sin convenio."""
        with override_settings(PERMITIR_PLACAS_EXTRANJERAS=True):
            with patch(
                "aplicaciones.vehiculos.selectores.selector_busqueda."
                "VistaBusqueda"
            ) as modelo:
                self.assertIsNone(obtener_extranjera_exacta(""))
                modelo.objects.assert_not_called()


class PruebaExpedienteExtranjeraSelector(SimpleTestCase):
    """El expediente ya era exacta + flag; se deja fijado."""

    def _fila_con_flag(self, flag, fila):
        """Ejecuta el selector de expediente con ORM simulado."""
        with override_settings(PERMITIR_PLACAS_EXTRANJERAS=flag):
            with patch(
                "aplicaciones.vehiculos.selectores.selector_expediente."
                "VistaExpediente"
            ) as modelo:
                cadena = MagicMock(name="consulta")
                cadena.filter.return_value = cadena
                cadena.values.return_value = cadena
                cadena.first.return_value = fila
                modelo.objects.using.return_value = cadena
                return obtener_por_placa_exacta("E123ABC")

    def test_expediente_extranjera_con_flag_apagado_da_none(self):
        """Sin convenio la extranjera existente es ausente."""
        self.assertIsNone(
            self._fila_con_flag(False, dict(FILA_EXPEDIENTE_EXTRANJERA))
        )

    def test_expediente_extranjera_con_flag_encendido_resuelve(self):
        """Con convenio la exacta autorizada resuelve."""
        self.assertEqual(
            self._fila_con_flag(True, dict(FILA_EXPEDIENTE_EXTRANJERA)),
            FILA_EXPEDIENTE_EXTRANJERA,
        )


class PruebaExtranjerasHttp(SimpleTestCase):
    """Cableado HTTP 200/404 para extranjeras en buscar y expediente."""

    def _verificar_404(self, respuesta):
        """404 sin causa y con correlacion cuerpo=cabecera."""
        self.assertEqual(respuesta.status_code, 404)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "no_encontrado")
        self.assertTrue(cuerpo["codigo_correlacion"])
        self.assertEqual(
            respuesta["X-Codigo-Correlacion"], cuerpo["codigo_correlacion"]
        )
        self.assertEqual(respuesta["Cache-Control"], "no-store")

    @override_settings(PERMITIR_PLACAS_EXTRANJERAS=False)
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[],
    )
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda."
        "obtener_extranjera_exacta",
        return_value=None,
    )
    def test_buscar_exacta_extranjera_flag_off_da_404(
        self, _exacta, _sufijo
    ):
        """Sin convenio la exacta extranjera da el mismo 404."""
        self._verificar_404(
            self.client.get(
                "/api/v1/vehiculos/buscar?placa=E123ABC",
                **cabecera_autorizacion(TODOS_LOS_AMBITOS),
            )
        )

    @override_settings(PERMITIR_PLACAS_EXTRANJERAS=False)
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[],
    )
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda."
        "obtener_extranjera_exacta",
        return_value=None,
    )
    def test_buscar_aproximada_extranjera_flag_off_da_404(
        self, _exacta, _sufijo
    ):
        """Sin convenio ni la aproximada revela existencia."""
        for valor in ("E123ABD", "E12", "123ABC"):
            with self.subTest(valor=valor):
                self._verificar_404(
                    self.client.get(
                        f"/api/v1/vehiculos/buscar?placa={valor}",
                        **cabecera_autorizacion(TODOS_LOS_AMBITOS),
                    )
                )

    @override_settings(PERMITIR_PLACAS_EXTRANJERAS=False)
    @patch(
        "aplicaciones.vehiculos.enrutador_expediente."
        "obtener_por_placa_exacta",
        return_value=None,
    )
    def test_expediente_extranjera_flag_off_da_404(self, _obtener):
        """Sin convenio el expediente extranjero da 404 uniforme."""
        self._verificar_404(
            self.client.get(
                "/api/v1/vehiculos/E123ABC/expediente",
                **cabecera_autorizacion(TODOS_LOS_AMBITOS),
            )
        )

    @override_settings(PERMITIR_PLACAS_EXTRANJERAS=True)
    @patch("aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo")
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda."
        "obtener_extranjera_exacta",
        return_value=dict(FILA_EXTRANJERA_BUSQUEDA),
    )
    def test_buscar_exacta_extranjera_flag_on_da_200(
        self, _exacta, mock_sufijo
    ):
        """Con convenio la exacta extranjera resuelve sin sufijo."""
        respuesta = self.client.get(
            "/api/v1/vehiculos/buscar?placa=E123ABC",
            **cabecera_autorizacion(TODOS_LOS_AMBITOS),
        )
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["placa"], "E123ABC")
        self.assertEqual(len(cuerpo["candidatas"]), 1)
        self.assertEqual(cuerpo["candidatas"][0]["placa"], "E123ABC")
        self.assertFalse(cuerpo["truncado"])
        mock_sufijo.assert_not_called()

    @override_settings(PERMITIR_PLACAS_EXTRANJERAS=True)
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[],
    )
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda."
        "obtener_extranjera_exacta",
        return_value=None,
    )
    def test_buscar_no_exacta_extranjera_flag_on_da_404(
        self, _exacta, _sufijo
    ):
        """Con convenio la variante no exacta sigue en 404."""
        self._verificar_404(
            self.client.get(
                "/api/v1/vehiculos/buscar?placa=E123ABD",
                **cabecera_autorizacion(TODOS_LOS_AMBITOS),
            )
        )

    @override_settings(PERMITIR_PLACAS_EXTRANJERAS=True)
    @patch(
        "aplicaciones.vehiculos.enrutador_expediente."
        "obtener_por_placa_exacta",
        return_value=dict(FILA_EXPEDIENTE_EXTRANJERA),
    )
    def test_expediente_extranjera_flag_on_da_200(self, _obtener):
        """Con convenio el expediente extranjero resuelve."""
        respuesta = self.client.get(
            "/api/v1/vehiculos/E123ABC/expediente",
            **cabecera_autorizacion(TODOS_LOS_AMBITOS),
        )
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.json()
        self.assertTrue(cuerpo["codigo_correlacion"])
        self.assertIn("vehiculo", cuerpo)

    @override_settings(PERMITIR_PLACAS_EXTRANJERAS=True)
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[{"placa_norma": "C123ABC", "placa": "C123ABC"}],
    )
    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda."
        "obtener_extranjera_exacta",
        return_value=None,
    )
    def test_buscar_nacional_con_flag_on_sigue_por_sufijo(
        self, _exacta, _sufijo
    ):
        """Con convenio la nacional sigue resolviendo por sufijo."""
        respuesta = self.client.get(
            "/api/v1/vehiculos/buscar?placa=C123ABC",
            **cabecera_autorizacion(TODOS_LOS_AMBITOS),
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.json()["candidatas"]), 1)
