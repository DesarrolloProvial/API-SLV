"""Pruebas del validador JWKS (sin red, llaves locales).

Cubren el contrato: firma valida acepta, firma invalida/expirada/ausente
rechaza con `TokenInvalido` (el enrutador lo traduce al 401 uniforme).
Endurecimiento 0.2/3.4: RS256 estricto por JWKS y fallo cerrado
(`alg`/`kid`/`iss`/`aud`/caida), sin Fase 1 de borde.
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

    @override_settings(TOKENS_REVOCADOS=["jti-lista-emergencia"])
    def test_jti_en_lista_de_emergencia_se_rechaza(self):
        """Un `jti` de `TOKENS_REVOCADOS` se deniega (kill-switch paso 1)."""
        token = emitir_token_prueba(
            ["vehiculos.lectura"],
            reclamos_extra={"jti": "jti-lista-emergencia"},
        )
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


EMISOR_EJEMPLO = "https://idp.ejemplo/realms/intercambio-dgt"
URL_JWKS_EJEMPLO = EMISOR_EJEMPLO + "/protocol/openid-connect/certs"
AUDIENCIA_EJEMPLO = "dgt-intercambio"


def _generar_rsa():
    """Genera un par RSA 2048 y devuelve `(pem_privada, pem_publica)`."""
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric import rsa

    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem_privada = privada.private_bytes(
        ser.Encoding.PEM, ser.PrivateFormat.PKCS8, ser.NoEncryption()
    ).decode("ascii")
    pem_publica = privada.public_key().public_bytes(
        ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo
    ).decode("ascii")
    return pem_privada, pem_publica


def _emitir_rs256(pem_privada, kid="llave-1", iss="", aud=""):
    """Emite un RS256 con `kid` y reclamos minimos de intercambio."""
    import time
    import uuid

    import jwt as biblioteca

    ahora = int(time.time())
    carga = {
        "sub": "dgt-intercambio", "client_id": "dgt-intercambio",
        "scope": "vehiculos.lectura", "iat": ahora - 60,
        "exp": ahora + 300, "jti": str(uuid.uuid4()),
        **({"iss": iss} if iss else {}), **({"aud": aud} if aud else {}),
    }
    return biblioteca.encode(
        carga, pem_privada, algorithm="RS256", headers={"kid": kid}
    )


def _con_llaves_jwks(publica):
    """Simula el JWKS remoto con solo `llave-1` (sin red)."""
    from unittest.mock import patch

    return patch(
        "aplicaciones.seguridad.validador_jwks._obtener_llaves_jwks",
        return_value={"llave-1": publica},
    )


def _recargar_preproduccion(url_jwks):
    """Recarga base+pre con `URL_JWKS` dada (eleva si viene vacia)."""
    import importlib
    import os
    from unittest.mock import patch

    import configuracion.ajustes_base as base

    real = os.environ.get("URL_JWKS", "")
    try:
        with patch.dict(os.environ, {"URL_JWKS": url_jwks}):
            importlib.reload(base)
            # Dentro del parche: el primer import ya corre con `URL_JWKS`.
            import configuracion.ajustes_preproduccion as pre
            return importlib.reload(pre)
    finally:
        with patch.dict(os.environ, {"URL_JWKS": real}):
            importlib.reload(base)


class PruebaValidadorJwksEndurecido(SimpleTestCase):
    """Endurecimiento 0.2/3.4 del modo JWKS (sin red real)."""

    def setUp(self):
        """Limpia revocados y cache antes de cada prueba."""
        limpiar_cache_jwks()

    def tearDown(self):
        """Limpia revocados y cache despues de cada prueba."""
        limpiar_cache_jwks()

    def test_rs256_con_llaves_inyectadas_valido_autentica(self):
        """RS256 con llave inyectada e `iss`/`aud` vigentes autentica."""
        privada, publica = _generar_rsa()
        reclamos = validar_token(
            _emitir_rs256(privada), {"llave-1": publica}
        )
        self.assertEqual(reclamos.get("sub"), "dgt-intercambio")
        self.assertIn("vehiculos.lectura", reclamos.get("scope", ""))

    def test_fallback_sin_jwks_advierte_solo_local(self):
        """Sin `URL_JWKS`, el HS256 local advierte (jamas en pre/prod)."""
        token = emitir_token_prueba(["vehiculos.lectura"])
        with self.assertWarns(UserWarning), self.assertLogs(
            "intercambio.consulta", level="WARNING"
        ):
            reclamos = validar_token(token)
        self.assertIn("vehiculos.lectura", reclamos.get("scope", ""))

    @override_settings(URL_JWKS=URL_JWKS_EJEMPLO)
    def test_algoritmo_no_permitido_en_jwks_se_rechaza(self):
        """Con JWKS, un HS256 se rechaza aunque su firma sea valida."""
        with self.assertRaises(TokenInvalido):
            validar_token(emitir_token_prueba(["vehiculos.lectura"]))

    @override_settings(URL_JWKS=URL_JWKS_EJEMPLO)
    def test_kid_desconocido_en_jwks_se_rechaza(self):
        """Con JWKS, un `kid` ausente del documento se rechaza."""
        privada, publica = _generar_rsa()
        token = _emitir_rs256(privada, kid="desconocida-0.2")
        with _con_llaves_jwks(publica):
            with self.assertRaises(TokenInvalido):
                validar_token(token)

    @override_settings(
        URL_JWKS=URL_JWKS_EJEMPLO,
        EMISOR_JWT=EMISOR_EJEMPLO,
        AUDIENCIA_JWT=AUDIENCIA_EJEMPLO,
    )
    def test_emisor_distinto_en_jwks_se_rechaza(self):
        """Con JWKS, un `iss` distinto del configurado se rechaza."""
        privada, publica = _generar_rsa()
        token = _emitir_rs256(
            privada, iss="https://idp.otro/realms/otro",
            aud=AUDIENCIA_EJEMPLO,
        )
        with _con_llaves_jwks(publica):
            with self.assertRaises(TokenInvalido):
                validar_token(token)

    @override_settings(
        URL_JWKS=URL_JWKS_EJEMPLO,
        EMISOR_JWT=EMISOR_EJEMPLO,
        AUDIENCIA_JWT=AUDIENCIA_EJEMPLO,
    )
    def test_audiencia_distinta_en_jwks_se_rechaza(self):
        """Con JWKS, una `aud` distinta de la configurada se rechaza."""
        privada, publica = _generar_rsa()
        token = _emitir_rs256(
            privada, iss=EMISOR_EJEMPLO, aud="otro-cliente"
        )
        with _con_llaves_jwks(publica):
            with self.assertRaises(TokenInvalido):
                validar_token(token)

    @override_settings(URL_JWKS=URL_JWKS_EJEMPLO)
    def test_jwks_caido_se_rechaza_sin_causa_interna(self):
        """Si el IdP no responde, hay 401 sin exponer detalle interno."""
        from unittest.mock import patch
        from urllib.error import URLError

        privada, _ = _generar_rsa()
        token = _emitir_rs256(privada)
        with patch(
            "urllib.request.urlopen", side_effect=URLError("caido")
        ):
            with self.assertRaises(TokenInvalido) as contexto:
                validar_token(token)
        self.assertNotIn("idp.ejemplo", str(contexto.exception))


class PruebaExigenciaUrlJwks(SimpleTestCase):
    """Preproduccion exige `URL_JWKS` (0.2/3.4, solo nombres)."""

    def test_preproduccion_sin_url_jwks_falla_cerrado(self):
        """Sin `URL_JWKS`, preproduccion no arranca (falla cerrado)."""
        from django.core.exceptions import ImproperlyConfigured

        with self.assertRaises(ImproperlyConfigured):
            _recargar_preproduccion("")

    def test_preproduccion_con_url_jwks_arranca(self):
        """Con `URL_JWKS` configurada, preproduccion arranca."""
        modulo = _recargar_preproduccion(URL_JWKS_EJEMPLO)
        self.assertEqual(modulo.URL_JWKS, URL_JWKS_EJEMPLO)
