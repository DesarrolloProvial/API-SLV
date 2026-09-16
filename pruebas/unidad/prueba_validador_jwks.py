"""Pruebas del validador JWKS (sin red, llaves locales).

Cubren el contrato: firma valida acepta, firma invalida/expirada/ausente
rechaza con `TokenInvalido` (el enrutador lo traduce al 401 uniforme).
"""
from django.test import SimpleTestCase, override_settings

from aplicaciones.seguridad.validador_jwks import (
    TokenInvalido,
    autenticar_peticion,
    limpiar_cache_jwks,
    revocar_token,
    validar_token,
)
from pruebas.ayuda_autenticacion import emitir_token_prueba


class _PeticionFalsa:
    """Peticion minima con cabecera `Authorization`."""

    def __init__(self, autorizacion: str = ""):
        """Guarda la cabecera a exponer como `headers` y `META`."""
        self.headers = {"Authorization": autorizacion} if autorizacion else {}
        self.META = (
            {"HTTP_AUTHORIZATION": autorizacion} if autorizacion else {}
        )


class PruebaValidadorJwks(SimpleTestCase):
    """Ciclo firmar y validar del modo local (HS256 sin JWKS)."""

    def setUp(self):
        """Limpia revocados y cache antes de cada prueba."""
        limpiar_cache_jwks()

    def tearDown(self):
        """Limpia revocados y cache despues de cada prueba."""
        limpiar_cache_jwks()

    def test_token_valido_con_ambitos_acepta(self):
        """Token firmado con la llave vigente devuelve sus reclamos."""
        token = emitir_token_prueba(["vehiculos.lectura"])
        reclamos = validar_token(token)
        self.assertIn("vehiculos.lectura", reclamos.get("scope", ""))

    def test_token_expirado_se_rechaza(self):
        """Un `exp` pasado se rechaza sin detallar la causa."""
        with self.assertRaises(TokenInvalido):
            validar_token(emitir_token_prueba(["vehiculos.lectura"], expirado=True))

    def test_firma_invalida_se_rechaza(self):
        """Firmar con otra llave no pasa la validacion."""
        token = emitir_token_prueba(["vehiculos.lectura"], firma="llave-ajena")
        with self.assertRaises(TokenInvalido):
            validar_token(token)

    def test_token_revocado_se_rechaza_de_inmediato(self):
        """Un `jti` revocado se deniega sin esperar su expiracion."""
        token = emitir_token_prueba(
            ["vehiculos.lectura"], reclamos_extra={"jti": "jti-revocado-1"}
        )
        revocar_token("jti-revocado-1")
        with self.assertRaises(TokenInvalido):
            validar_token(token)

    def test_peticion_sin_portador_se_rechaza(self):
        """Sin cabecera o sin esquema `Bearer` hay `TokenInvalido`."""
        for autorizacion in ("", "Token abc.def.ghi", "Bearer "):
            with self.subTest(autorizacion=autorizacion):
                with self.assertRaises(TokenInvalido):
                    autenticar_peticion(_PeticionFalsa(autorizacion))

    def test_peticion_con_portador_valido_autentica(self):
        """`autenticar_peticion` extrae y valida el portador."""
        token = emitir_token_prueba(["vehiculos.lectura"])
        reclamos = autenticar_peticion(_PeticionFalsa(f"Bearer {token}"))
        self.assertEqual(reclamos.get("client_id"), "dgt-intercambio")

    def test_algoritmo_none_se_rechaza(self):
        """`alg=none` nunca se acepta aunque el cuerpo sea legible."""
        import jwt as biblioteca

        token = biblioteca.encode({"scope": "x"}, key="", algorithm="none")
        with self.assertRaises(TokenInvalido):
            validar_token(token)

    @override_settings(
        EMISOR_JWT="https://idp.ejemplo/realms/intercambio-dgt",
        AUDIENCIA_JWT="dgt-intercambio",
    )
    def test_emisor_y_audiencia_se_exigen_cuando_configurados(self):
        """Con IdP configurado, `iss`/`aud` distintos se rechazan."""
        bueno = emitir_token_prueba(["vehiculos.lectura"])
        self.assertIn("vehiculos.lectura", validar_token(bueno).get("scope", ""))
        import jwt as biblioteca
        import time

        carga = {
            "sub": "dgt-intercambio",
            "scope": "vehiculos.lectura",
            "iat": int(time.time()) - 60,
            "exp": int(time.time()) + 300,
            "iss": "https://idp.otro/realms/otro",
            "aud": "otro-cliente",
            "jti": "jti-ajeno",
        }
        from django.conf import settings

        ajeno = biblioteca.encode(carga, settings.LLAVE_SECRETA, algorithm="HS256")
        with self.assertRaises(TokenInvalido):
            validar_token(ajeno)
