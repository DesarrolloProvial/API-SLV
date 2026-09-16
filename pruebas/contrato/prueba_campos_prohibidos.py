"""Ausencia de campos prohibidos del PLAN §11 en contrato y respuestas.

Escanea los nombres de propiedad del OpenAPI vivo y una respuesta real
con fila hostil (con prohibidos): el armador nunca los emite.
"""
from django.test import SimpleTestCase

from aplicaciones.vehiculos.servicios.armador_expediente import armar_expediente
from pruebas.contrato.campos_prohibidos import (
    contiene_prohibido,
    escanear_propiedades,
)

FILA_HOSTIL = {
    "placa_norma": "C123ABC",
    "placa": "C123ABC",
    "password": "secreto",
    "hash": "abc",
    "token": "t",
    "session_key": "s",
    "cui": "123",
    "telefonos": "555",
    "correo_electronico": "a@b.c",
    "domicilio": "calle",
    "sha256": "h",
    "ruta_almacenamiento": "/minio/x",
    "observaciones_internas": "interno",
    "datos_extra": {"usernames": ["u"]},
}


class PruebaCamposProhibidos(SimpleTestCase):
    """El contrato y las respuestas estan libres de prohibidos."""

    def test_openapi_sin_prohibidos(self):
        """Ninguna propiedad del OpenAPI vivo es ni contiene un prohibido."""
        respuesta = self.client.get("/api/openapi.json")
        self.assertEqual(respuesta.status_code, 200)
        hallazgos = []
        for nombre, esquema in respuesta.json()["components"]["schemas"].items():
            for campo in (esquema.get("properties", {}) or {}):
                hallado = contiene_prohibido(campo)
                if hallado:
                    hallazgos.append(f"{nombre}.{campo} -> {hallado}")
        self.assertEqual(hallazgos, [])

    def test_respuesta_real_sin_prohibidos(self):
        """Aun con fila hostil, el expediente no emite prohibidos."""
        cuerpo = armar_expediente(dict(FILA_HOSTIL), "codigo-prueba")
        hallazgos = escanear_propiedades(cuerpo)
        self.assertEqual(hallazgos, [])

    def test_detector_reconoce_prohibidos(self):
        """El detector marca `cui`/`correo` y no marca `municipio`."""
        self.assertEqual(contiene_prohibido("cui"), "cui")
        self.assertEqual(contiene_prohibido("correo_electronico"), "correo")
        self.assertIsNone(contiene_prohibido("municipio"))
        self.assertIsNone(contiene_prohibido("marca"))
