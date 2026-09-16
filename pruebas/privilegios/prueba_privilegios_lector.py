"""Pruebas negativas de privilegios del rol lector del espejo.

Se omiten limpiamente sin espejo (sin ``URL_ESPEJO_PRUEBAS``) para que
``python manage.py test pruebas`` siga verde sin PostgreSQL; con espejo local
y snapshot aplicado, verifican el contrato de solo lectura.
Nota: las vistas usan JOIN/LATERAL y rechazan escritura por estructura además
del permiso; por eso INSERT/UPDATE/DELETE se verifican con
``has_table_privilege`` y el intento real se hace con SELECT base y DDL.
"""
import os
import unittest

from django.test import SimpleTestCase

try:
    import psycopg
    from psycopg import errors as errores_pg
except ImportError:  # pragma: no cover - psycopg es dependencia del proyecto
    psycopg = None
    errores_pg = None


VISTAS_CONTRATO = [
    "vista_busqueda_v1",
    "vista_expediente_v1",
    "vista_generales_v1",
    "vista_propietario_v1",
    "vista_empresa_v1",
    "vista_refrendos_v1",
    "vista_historial_v1",
]


@unittest.skipIf(psycopg is None, "psycopg no instalado")
class PruebaPrivilegiosLector(SimpleTestCase):
    """El lector solo lee vistas del contrato; todo lo demás se rechaza."""

    @classmethod
    def setUpClass(cls):
        """Conecta como lector u omite si no hay espejo disponible."""
        super().setUpClass()
        url = os.getenv("URL_ESPEJO_PRUEBAS")
        if not url:
            raise unittest.SkipTest("Sin espejo: definir URL_ESPEJO_PRUEBAS con el DSN del rol lector")
        try:
            cls.conexion = psycopg.connect(url, connect_timeout=5)
            cls.conexion.autocommit = True
        except Exception as error:
            raise unittest.SkipTest(f"Espejo inalcanzable: {error}") from error

    @classmethod
    def tearDownClass(cls):
        """Cierra la conexión del lector."""
        if getattr(cls, "conexion", None) is not None:
            cls.conexion.close()
        super().tearDownClass()

    def _privilegio(self, rol, objeto, permiso):
        """Devuelve si el rol tiene el permiso sobre el objeto."""
        with self.conexion.cursor() as cursor:
            cursor.execute("SELECT has_table_privilege(%s, %s, %s)", (rol, objeto, permiso))
            return cursor.fetchone()[0]

    def _existe_relacion(self, nombre):
        """Indica si la vista o tabla ya existe en el espejo."""
        with self.conexion.cursor() as cursor:
            cursor.execute("SELECT to_regclass(%s) IS NOT NULL", (nombre,))
            return cursor.fetchone()[0]

    def test_lector_lee_vistas_contrato(self):
        """El lector tiene SELECT en las siete vistas versionadas."""
        if not self._existe_relacion("intercambio.vista_busqueda_v1"):
            self.skipTest("Vistas sin aplicar (ver orden_aplicacion.md)")
        for vista in VISTAS_CONTRATO:
            with self.subTest(vista=vista):
                self.assertTrue(self._privilegio("rol_lector_intercambio", f"intercambio.{vista}", "SELECT"))

    def test_lector_sin_escritura_en_vistas(self):
        """El lector no tiene INSERT, UPDATE, DELETE ni TRUNCATE en vistas."""
        if not self._existe_relacion("intercambio.vista_busqueda_v1"):
            self.skipTest("Vistas sin aplicar (ver orden_aplicacion.md)")
        for vista in VISTAS_CONTRATO:
            for permiso in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
                with self.subTest(vista=vista, permiso=permiso):
                    self.assertFalse(
                        self._privilegio("rol_lector_intercambio", f"intercambio.{vista}", permiso)
                    )

    def test_lector_sin_ddl_en_esquemas(self):
        """El lector no crea objetos en intercambio ni en public."""
        with self.conexion.cursor() as cursor:
            for esquema in ("intercambio", "public"):
                with self.subTest(esquema=esquema):
                    cursor.execute(
                        "SELECT has_schema_privilege('rol_lector_intercambio', %s, 'CREATE')",
                        (esquema,),
                    )
                    self.assertFalse(cursor.fetchone()[0])

    def test_lector_sin_tablas_base(self):
        """El lector no lee las tablas replicadas (verificación de privilegio)."""
        if not self._existe_relacion("slv_vehiculobase"):
            self.skipTest("Sin snapshot: tabla base ausente en el espejo")
        self.assertFalse(self._privilegio("rol_lector_intercambio", "slv_vehiculobase", "SELECT"))

    def test_intento_real_select_base_es_rechazado(self):
        """Un SELECT real a la tabla base falla por permiso insuficiente."""
        if not self._existe_relacion("slv_vehiculobase"):
            self.skipTest("Sin snapshot: tabla base ausente en el espejo")
        with self.assertRaises(errores_pg.InsufficientPrivilege):
            with self.conexion.cursor() as cursor:
                cursor.execute("SELECT 1 FROM slv_vehiculobase LIMIT 1")

    def test_intento_real_ddl_es_rechazado(self):
        """Un CREATE TABLE real con el lector falla por permiso insuficiente."""
        with self.assertRaises(errores_pg.InsufficientPrivilege):
            with self.conexion.cursor() as cursor:
                cursor.execute("CREATE TABLE intercambio.tabla_intento_lector (id integer)")
