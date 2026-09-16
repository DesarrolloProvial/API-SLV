"""Pruebas unitarias del cursor opaco (sin BD).

Verifican firma, rechazo ante manipulacion, ligadura al filtro de placa
y formato ilegible. El enrutador traduce `CursorInvalido` al 404 uniforme.
"""
from django.test import SimpleTestCase, override_settings

from aplicaciones.seguridad.cursor_opaco import (
    CursorInvalido,
    decodificar_cursor,
    emitir_cursor,
)


class PruebaCursorOpaco(SimpleTestCase):
    """Ciclo emitir y validar del cursor firmado."""

    def test_ida_y_vuelta_conserva_posicion_y_placa(self):
        """Emitir y decodificar devuelve el mismo desplazamiento."""
        cursor = emitir_cursor("C123ABC", 0)
        self.assertEqual(decodificar_cursor(cursor, "C123ABC"), 0)
        siguiente = emitir_cursor("C123ABC", 10)
        self.assertEqual(decodificar_cursor(siguiente, "C123ABC"), 10)

    def test_token_no_expone_placa_en_claro(self):
        """El token es opaco: la placa no aparece literal en el texto."""
        cursor = emitir_cursor("C123ABC", 0)
        self.assertIn(".", cursor)
        self.assertNotIn("C123ABC", cursor)

    def test_cursor_de_otra_placa_se_rechaza(self):
        """El filtro liga el cursor: reusarlo en otra placa es invalido."""
        cursor = emitir_cursor("C123ABC", 0)
        with self.assertRaises(CursorInvalido):
            decodificar_cursor(cursor, "P123ABC")

    def test_cuerpo_manipulado_se_rechaza(self):
        """Cambiar un caracter del cuerpo rompe la firma."""
        cursor = emitir_cursor("C123ABC", 0)
        cuerpo, firma = cursor.split(".", 1)
        alterado = ("A" if cuerpo[0] != "A" else "B") + cuerpo[1:]
        with self.assertRaises(CursorInvalido):
            decodificar_cursor(f"{alterado}.{firma}", "C123ABC")

    def test_firma_manipulada_se_rechaza(self):
        """Cambiar un caracter de la firma se rechaza sin distinguir causa."""
        cursor = emitir_cursor("C123ABC", 0)
        cuerpo, firma = cursor.split(".", 1)
        alterada = ("A" if firma[-1] != "A" else "B") + firma[1:]
        with self.assertRaises(CursorInvalido):
            decodificar_cursor(f"{cuerpo}.{alterada}", "C123ABC")

    def test_formatos_ilegibles_se_rechazan(self):
        """Vacio, sin punto y basura codificada son invalidos."""
        for valor in ("", "sincuerpo", "....", "!!!.???", "aGVsbw.bm8"):
            with self.subTest(valor=valor):
                with self.assertRaises(CursorInvalido):
                    decodificar_cursor(valor, "C123ABC")

    def test_emitir_exige_placa_y_posicion_validas(self):
        """Emitir valida sus entradas antes de firmar."""
        with self.assertRaises(ValueError):
            emitir_cursor("", 0)
        with self.assertRaises(ValueError):
            emitir_cursor("C123ABC", -1)

    @override_settings(LLAVE_SECRETA="otra-llave-de-prueba")
    def test_firma_con_otra_llave_se_rechaza(self):
        """Un cursor firmado con otra llave no es valido aqui."""
        cursor = emitir_cursor("C123ABC", 0)
        with override_settings(LLAVE_SECRETA="llave-distinta"):
            with self.assertRaises(CursorInvalido):
                decodificar_cursor(cursor, "C123ABC")
