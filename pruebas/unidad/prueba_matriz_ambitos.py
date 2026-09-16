"""Matriz endpoint por ambito: 401 sin token, 403 sin ambito, 200 con el.

Verifica el contrato de la spec: sin ambito no sale ningun dato (mensaje
uniforme) y los `vinculos` solo traen lo autorizado. Selectores
simulados; sin BD.
"""
from datetime import date
from unittest.mock import patch

from django.test import SimpleTestCase

from pruebas.ayuda_autenticacion import cabecera_autorizacion

BASE = ["vehiculos.lectura"]
TODO = [
    "vehiculos.lectura",
    "vehiculos.propietario.lectura",
    "vehiculos.empresa.lectura",
    "vehiculos.refrendos.lectura",
    "vehiculos.historial.lectura",
]

FILA_EXPEDIENTE = {
    "placa_norma": "C123ABC",
    "placa": "C123ABC",
    "activa": True,
    "tipo_placa": "guatemalteca",
}


def _simuladores(recurso: str):
    """Devuelve los `patch` de selectores para un 200 del recurso."""
    if recurso == "buscar":
        return [
            patch(
                "aplicaciones.vehiculos.enrutador_busqueda.buscar_por_sufijo",
                return_value=[{"placa_norma": "C123ABC", "placa": "C123ABC"}],
            )
        ]
    if recurso in ("expediente", "generales"):
        return [
            patch(
                "aplicaciones.vehiculos.enrutador_expediente.obtener_por_placa_exacta",
                return_value=dict(
                    FILA_EXPEDIENTE,
                    chasis="CH1",
                    marca="Toyota",
                    linea="Hilux",
                    modelo="2020",
                    fecha_codigo=date(2024, 1, 15),
                ),
            )
        ]
    if recurso == "propietario":
        return [
            patch(
                "aplicaciones.propietario.enrutador_propietario.obtener_por_placa_exacta",
                return_value=dict(FILA_EXPEDIENTE),
            ),
            patch(
                "aplicaciones.propietario.enrutador_propietario.obtener_propietario",
                return_value={"placa": "C123ABC", "nombre_empresa": "T"},
            ),
        ]
    if recurso == "empresa":
        return [
            patch(
                "aplicaciones.empresa.enrutador_empresa.obtener_por_placa_exacta",
                return_value=dict(FILA_EXPEDIENTE),
            ),
            patch(
                "aplicaciones.empresa.enrutador_empresa.obtener_empresa",
                return_value={"placa": "C123ABC", "nombre_empresa": "E"},
            ),
        ]
    if recurso == "refrendos":
        return [
            patch(
                "aplicaciones.refrendos.enrutador_refrendos.obtener_por_placa_exacta",
                return_value=dict(FILA_EXPEDIENTE),
            ),
            patch(
                "aplicaciones.refrendos.enrutador_refrendos.paginar_refrendos",
                return_value=([], None),
            ),
        ]
    return [
        patch(
            "aplicaciones.historial.enrutador_historial.obtener_por_placa_exacta",
            return_value=dict(FILA_EXPEDIENTE),
        ),
        patch(
            "aplicaciones.historial.enrutador_historial.paginar_historial",
            return_value=([], None),
        ),
    ]


RUTAS = {
    "buscar": "/api/v1/vehiculos/buscar?placa=C123ABC",
    "expediente": "/api/v1/vehiculos/C123ABC/expediente",
    "generales": "/api/v1/vehiculos/C123ABC/expediente/generales",
    "propietario": "/api/v1/vehiculos/C123ABC/expediente/propietario",
    "empresa": "/api/v1/vehiculos/C123ABC/expediente/empresa",
    "refrendos": "/api/v1/vehiculos/C123ABC/expediente/refrendos",
    "historial": "/api/v1/vehiculos/C123ABC/expediente/historial",
}

AMBITO_PROPIO = {
    "buscar": BASE,
    "expediente": BASE,
    "generales": BASE,
    "propietario": ["vehiculos.lectura", "vehiculos.propietario.lectura"],
    "empresa": ["vehiculos.lectura", "vehiculos.empresa.lectura"],
    "refrendos": ["vehiculos.lectura", "vehiculos.refrendos.lectura"],
    "historial": ["vehiculos.lectura", "vehiculos.historial.lectura"],
}


class PruebaMatrizAmbitos(SimpleTestCase):
    """401/403/200 por recurso segun el token y sus ambitos."""

    def _verificar_error(self, respuesta, estado, error):
        """Error uniforme con correlacion cuerpo=cabecera y no-store."""
        self.assertEqual(respuesta.status_code, estado)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["error"], error)
        self.assertTrue(cuerpo["mensaje"])
        self.assertTrue(cuerpo["codigo_correlacion"])
        self.assertEqual(
            respuesta["X-Codigo-Correlacion"], cuerpo["codigo_correlacion"]
        )
        self.assertEqual(respuesta["Cache-Control"], "no-store")
        return cuerpo

    def test_sin_token_da_401_sin_dato(self):
        """Sin `Authorization` no sale ningun dato en ningun recurso."""
        for recurso, ruta in RUTAS.items():
            with self.subTest(recurso=recurso):
                respuesta = self.client.get(ruta)
                cuerpo = self._verificar_error(respuesta, 401, "no_autenticado")
                self.assertNotIn("candidatas", cuerpo)
                self.assertNotIn("vehiculo", cuerpo)

    def test_token_expirado_o_firma_invalida_da_401(self):
        """Expirado o ajeno se rechaza igual que el ausente."""
        for recurso, ruta in RUTAS.items():
            with self.subTest(recurso=recurso):
                for extra in (
                    cabecera_autorizacion(TODO, expirado=True),
                    cabecera_autorizacion(TODO, firma="llave-ajena"),
                ):
                    respuesta = self.client.get(ruta, **extra)
                    self._verificar_error(respuesta, 401, "no_autenticado")

    def test_sin_ambito_del_recurso_da_403_sin_dato(self):
        """Token valido pero sin el ambito: 403 uniforme sin dato."""
        for recurso, ruta in RUTAS.items():
            with self.subTest(recurso=recurso):
                # Base sola alcanza solo en buscar/expediente/generales.
                ambitos = [] if recurso in ("buscar", "expediente", "generales") else BASE
                simuladores = _simuladores(recurso)
                with simuladores[0]:
                    if len(simuladores) > 1:
                        with simuladores[1]:
                            respuesta = self.client.get(
                                ruta, **cabecera_autorizacion(ambitos)
                            )
                    else:
                        respuesta = self.client.get(
                            ruta, **cabecera_autorizacion(ambitos)
                        )
                cuerpo = self._verificar_error(respuesta, 403, "sin_permiso")
                self.assertNotIn("candidatas", cuerpo)
                self.assertNotIn("vehiculo", cuerpo)

    def test_con_ambito_del_recurso_da_200(self):
        """Con el ambito propio cada recurso responde 200 con correlacion."""
        for recurso, ruta in RUTAS.items():
            with self.subTest(recurso=recurso):
                simuladores = _simuladores(recurso)
                with simuladores[0]:
                    if len(simuladores) > 1:
                        with simuladores[1]:
                            respuesta = self.client.get(
                                ruta,
                                **cabecera_autorizacion(AMBITO_PROPIO[recurso]),
                            )
                    else:
                        respuesta = self.client.get(
                            ruta, **cabecera_autorizacion(AMBITO_PROPIO[recurso])
                        )
                self.assertEqual(respuesta.status_code, 200)
                cuerpo = respuesta.json()
                self.assertTrue(cuerpo["codigo_correlacion"])
                self.assertEqual(respuesta["Cache-Control"], "no-store")

    def test_vinculos_solo_traen_lo_autorizado(self):
        """Con solo la base, el expediente no anuncia subrecursos."""
        simuladores = _simuladores("expediente")
        with simuladores[0]:
            respuesta = self.client.get(
                RUTAS["expediente"], **cabecera_autorizacion(BASE)
            )
        self.assertEqual(respuesta.status_code, 200)
        vinculos = respuesta.json()["vinculos"]
        self.assertTrue(vinculos.get("expediente"))
        self.assertTrue(vinculos.get("generales"))
        for clave in ("propietario", "empresa", "refrendos", "historial"):
            self.assertFalse(vinculos.get(clave))

    def test_vinculos_completos_con_todos_los_ambitos(self):
        """Con todos los ambitos, el expediente trae los 6 vinculos."""
        simuladores = _simuladores("expediente")
        with simuladores[0]:
            respuesta = self.client.get(
                RUTAS["expediente"], **cabecera_autorizacion(TODO)
            )
        self.assertEqual(respuesta.status_code, 200)
        for clave in (
            "expediente", "generales", "propietario",
            "empresa", "refrendos", "historial",
        ):
            self.assertIn(clave, respuesta.json()["vinculos"])
