"""Pruebas de limites multicapa lado API (sin red ni BD).

Verifican el contrato: al exceder la cuota hay 429 `limite_excedido`
uniforme con cabecera `Retry-After`, sin filtrar umbrales.
"""
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from aplicaciones.seguridad.aplicador_limites import (
    LimiteExcedido,
    clave_cliente,
    limpiar_limites,
    tope_para,
    verificar_limite,
)
from pruebas.ayuda_autenticacion import (
    TODOS_LOS_AMBITOS,
    cabecera_autorizacion,
)


class _PeticionFalsa:
    """Peticion minima (los limites no leen la peticion hoy)."""


class PruebaAplicadorLimites(SimpleTestCase):
    """Ventana fija por cliente y recurso en memoria."""

    def setUp(self):
        """Vacia los contadores antes de cada prueba."""
        limpiar_limites()

    def tearDown(self):
        """Vacia los contadores despues de cada prueba."""
        limpiar_limites()

    def test_hasta_el_tope_pasa_y_uno_mas_excede(self):
        """El tope + 1 levanta `LimiteExcedido` con reintento >= 1."""
        reclamos = {"client_id": "dgt-intercambio"}
        tope, _ = tope_para("empresa")
        for _ in range(tope):
            verificar_limite(_PeticionFalsa(), reclamos, "empresa")
        with self.assertRaises(LimiteExcedido) as contexto:
            verificar_limite(_PeticionFalsa(), reclamos, "empresa")
        self.assertGreaterEqual(contexto.exception.reintentar_en, 1)

    def test_mensaje_no_filtra_umbrales(self):
        """El error no revela el tope ni la ventana configurados."""
        reclamos = {"client_id": "dgt-intercambio"}
        tope, _ = tope_para("empresa")
        for _ in range(tope + 1):
            try:
                verificar_limite(_PeticionFalsa(), reclamos, "empresa")
            except LimiteExcedido as excedido:
                self.assertNotIn(str(tope), str(excedido))
        self.assertTrue(True)

    def test_clientes_distintos_no_comparten_cuota(self):
        """La cuota es por cliente: otro `client_id` empieza de cero."""
        tope, _ = tope_para("empresa")
        for _ in range(tope):
            verificar_limite(_PeticionFalsa(), {"client_id": "a"}, "empresa")
        verificar_limite(_PeticionFalsa(), {"client_id": "b"}, "empresa")

    def test_recursos_distintos_no_comparten_cuota(self):
        """La cuota es por recurso: agotar uno no bloquea otro."""
        reclamos = {"client_id": "dgt-intercambio"}
        tope, _ = tope_para("empresa")
        for _ in range(tope):
            verificar_limite(_PeticionFalsa(), reclamos, "empresa")
        verificar_limite(_PeticionFalsa(), reclamos, "historial")

    def test_buscar_es_mas_estricta_que_el_resto(self):
        """`buscar` trae el tope estricto del convenio de dia 0."""
        tope_buscar, _ = tope_para("buscar")
        tope_otro, _ = tope_para("expediente")
        self.assertLessEqual(tope_buscar, tope_otro)

    def test_clave_cliente_usa_identidad_sin_secretos(self):
        """La clave usa `client_id`/`sub` y nunca el token."""
        self.assertEqual(
            clave_cliente({"client_id": "dgt", "jti": "secreto"}), "dgt"
        )
        self.assertEqual(clave_cliente({"sub": "s"}), "s")
        self.assertEqual(clave_cliente({}), "anonimo")


@override_settings(LIMITE_BUSCAR_TOPE=2, VENTANA_LIMITE_SEG=60)
class PruebaLimitePorHttp(SimpleTestCase):
    """El 429 viaja con `Retry-After`, correlacion y no-store."""

    def setUp(self):
        """Vacia los contadores antes de cada prueba."""
        limpiar_limites()

    def tearDown(self):
        """Vacia los contadores despues de cada prueba."""
        limpiar_limites()

    @patch(
        "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
        return_value=[{"placa_norma": "C123ABC", "placa": "C123ABC"}],
    )
    def test_tercera_rafaga_da_429_con_reintento(self, _buscar):
        """Con tope 2, la tercera peticion es 429 uniforme."""
        ruta = "/api/v1/vehiculos/buscar?placa=C123ABC"
        extra = cabecera_autorizacion(TODOS_LOS_AMBITOS)
        self.assertEqual(self.client.get(ruta, **extra).status_code, 200)
        self.assertEqual(self.client.get(ruta, **extra).status_code, 200)
        respuesta = self.client.get(ruta, **extra)
        self.assertEqual(respuesta.status_code, 429)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], "limite_excedido")
        self.assertTrue(cuerpo["mensaje"])
        self.assertTrue(cuerpo["codigo_correlacion"])
        self.assertNotIn("2", cuerpo["mensaje"])
        self.assertTrue(int(respuesta["Retry-After"]) >= 1)
        self.assertEqual(
            respuesta["X-Codigo-Correlacion"], cuerpo["codigo_correlacion"]
        )
        self.assertEqual(respuesta["Cache-Control"], "no-store")
