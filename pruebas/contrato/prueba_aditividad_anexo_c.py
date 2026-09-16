"""Aditividad del Anexo C: el contrato solo crece (tarea 3.4).

Compara el OpenAPI vivo contra la instantanea congelada y exige casos
unitarios: agregar campo pasa, eliminar/renombrar/cambiar tipo falla.
"""
import copy
import json
from pathlib import Path

from django.test import SimpleTestCase

from contratos.verificar_aditividad import es_aditivo

INSTANTANEA = (
    Path(__file__).resolve().parent.parent.parent
    / "contratos" / "instantaneas" / "anexo_c_v1" / "openapi_v1.json"
)


class PruebaAditividadAnexoC(SimpleTestCase):
    """El vivo es aditivo contra la instantanea; el comparador frena roturas."""

    def _vivo(self) -> dict:
        """Pide el OpenAPI vivo sin autenticacion (es publico)."""
        respuesta = self.client.get("/api/openapi.json")
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.json()

    def _base(self) -> dict:
        """Carga la instantanea congelada del Anexo C v1."""
        self.assertTrue(INSTANTANEA.exists(), "Falta la instantanea openapi_v1.json")
        return json.loads(INSTANTANEA.read_text(encoding="utf-8"))

    def test_vivo_es_aditivo_contra_instantanea(self):
        """El OpenAPI vivo no rompe la instantanea congelada."""
        rupturas = es_aditivo(self._base(), self._vivo())
        self.assertEqual(rupturas, [])

    def test_agregar_campo_nuevo_pasa(self):
        """Un campo nuevo en un esquema es aditivo (pasa)."""
        base, actual = self._base(), self._base()
        esquema = next(iter(actual["components"]["schemas"].values()))
        esquema.setdefault("properties", {})["campo_nuevo_convenido"] = {
            "type": "string", "title": "Campo Nuevo Convenido"
        }
        self.assertEqual(es_aditivo(base, actual), [])

    def test_eliminar_campo_falla(self):
        """Quitar un campo del contrato falla (exige version nueva)."""
        base, actual = self._base(), copy.deepcopy(self._base())
        nombre, esquema = next(iter(actual["components"]["schemas"].items()))
        campo, _ = next(iter(esquema["properties"].items()))
        del esquema["properties"][campo]
        rupturas = es_aditivo(base, actual)
        self.assertTrue(rupturas, f"Debio fallar al quitar {nombre}.{campo}")

    def test_cambiar_tipo_falla(self):
        """Cambiar el tipo de un campo falla (rompe clientes)."""
        base, actual = self._base(), copy.deepcopy(self._base())
        esquema = next(iter(actual["components"]["schemas"].values()))
        campo, prop = next(iter(esquema["properties"].items()))
        prop["type"] = "integer" if prop.get("type") != "integer" else "boolean"
        prop.pop("anyOf", None)
        rupturas = es_aditivo(base, actual)
        self.assertTrue(rupturas, f"Debio fallar al cambiar {campo}")

    def test_eliminar_ruta_falla(self):
        """Quitar una ruta del contrato falla."""
        base, actual = self._base(), copy.deepcopy(self._base())
        ruta, _ = next(iter(actual["paths"].items()))
        del actual["paths"][ruta]
        rupturas = es_aditivo(base, actual)
        self.assertTrue(rupturas, f"Debio fallar al quitar {ruta}")
