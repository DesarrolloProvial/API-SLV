"""Pruebas de selectores y vistas contra el espejo (con omision limpia).

Sin `URL_ESPEJO_PRUEBAS` se omiten sin tocar PostgreSQL, igual que las
pruebas de privilegios. Con espejo y snapshot aplicado, ejecutan los
selectores reales y verifican las columnas del contrato.
"""
import os
import unittest
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.db import connections

from aplicaciones.vehiculos.selectores.selector_busqueda import buscar_por_sufijo
from aplicaciones.vehiculos.selectores.selector_expediente import (
    obtener_por_placa_exacta,
)

COLUMNAS_BUSQUEDA = {
    "placa_norma", "placa_sufijo6", "tipo", "activa", "placa", "chasis",
    "codigo_correlativo", "estado_aprobacion", "empresa_implementadora",
    "marca", "linea", "modelo",
}

COLUMNAS_EXPEDIENTE = {
    "placa_norma", "placa", "chasis", "vin", "tarjeta_circulacion",
    "marca", "linea", "modelo", "serie", "tipo_placa", "clasificacion",
    "tipo_vehiculo", "uso", "color", "departamento", "municipio", "motor",
    "asientos", "ejes", "cilindraje", "centimetros_cubicos", "toneladas",
    "codigo_correlativo", "estado_aprobacion", "activa", "fecha_codigo",
    "tipo_slv_codigo", "tipo_slv_nombre", "refrendo_codigo",
    "refrendo_fecha", "refrendo_vencimiento", "refrendo_estado",
    "propietario_nombre", "empresa_nombre", "empresa_autorizacion",
    "empresa_esta_autorizada",
}


def _parametros_desde_url(url: str) -> dict:
    """Convierte un DSN `postgres://` a parametros Django.

    Args:
        url: DSN del rol lector del espejo.

    Returns:
        dict: Parametros para `connections.databases`.
    """
    partes = urlparse(url)
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(partes.path.lstrip("/")),
        "USER": unquote(partes.username or ""),
        "PASSWORD": unquote(partes.password or ""),
        "HOST": partes.hostname or "localhost",
        "PORT": str(partes.port or "5432"),
        "CONN_MAX_AGE": 0,
    }


class PruebaSelectoresEspejo(unittest.TestCase):
    """Selectores reales sobre las vistas aplicadas en el espejo."""

    _alias_previo = "default"

    @classmethod
    def setUpClass(cls):
        """Registra la conexion lectora u omite sin espejo."""
        super().setUpClass()
        url = os.getenv("URL_ESPEJO_PRUEBAS")
        if not url:
            raise unittest.SkipTest(
                "Sin espejo: definir URL_ESPEJO_PRUEBAS con el DSN del rol lector"
            )
        connections.databases["espejo"] = _parametros_desde_url(url)
        try:
            with connections["espejo"].cursor() as cursor:
                cursor.execute(
                    "SELECT to_regclass('intercambio.vista_busqueda') IS NOT NULL"
                    " AND to_regclass('intercambio.vista_expediente') IS NOT NULL"
                )
                if not cursor.fetchone()[0]:
                    raise unittest.SkipTest(
                        "Vistas sin aplicar (ver orden_aplicacion.md)"
                    )
        except unittest.SkipTest:
            raise
        except Exception as error:
            raise unittest.SkipTest(f"Espejo inalcanzable: {error}") from error
        cls._alias_previo = getattr(settings, "ALIAS_ESPEJO", "default")
        settings.ALIAS_ESPEJO = "espejo"

    @classmethod
    def tearDownClass(cls):
        """Cierra, retira la conexion lectora y restaura el ajuste."""
        try:
            connections["espejo"].close()
        except Exception:
            pass
        finally:
            connections.databases.pop("espejo", None)
        settings.ALIAS_ESPEJO = cls._alias_previo
        super().tearDownClass()

    def _columnas(self, vista: str) -> set:
        """Columnas reales de la vista en el espejo."""
        with connections["espejo"].cursor() as cursor:
            cursor.execute(
                "SELECT column_name FROM information_schema.columns"
                " WHERE table_schema = 'intercambio' AND table_name = %s",
                [vista],
            )
            return {fila[0] for fila in cursor.fetchall()}

    def test_vista_busqueda_expone_contrato(self):
        """La vista de busqueda trae las columnas que el ORM espera."""
        self.assertTrue(COLUMNAS_BUSQUEDA <= self._columnas("vista_busqueda_v1"))

    def test_vista_expediente_expone_contrato(self):
        """La vista de expediente trae las columnas que el ORM espera."""
        self.assertTrue(
            COLUMNAS_EXPEDIENTE <= self._columnas("vista_expediente_v1")
        )

    def test_buscar_inexistente_devuelve_vacio(self):
        """Un sufijo sin datos ejecuta y devuelve lista vacia."""
        self.assertEqual(buscar_por_sufijo("000000", "Z", 10), [])

    def test_expediente_inexistente_devuelve_none(self):
        """Una placa ausente ejecuta y devuelve None (luego 404)."""
        self.assertIsNone(obtener_por_placa_exacta("ZZZ000000"))
