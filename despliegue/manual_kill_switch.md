# Manual kill-switch del intercambio

> EJECUCIÓN MANUAL GUIADA — NO AUTOMÁTICA. Cada paso lo ejecuta una
> persona con el rol indicado, en este orden, verificando antes de
> seguir. El ERP (`:8001`/`:8080`) sigue operando en todo momento.

## Roles

| Paso | Rol | Ámbito |
|------|-----|--------|
| 1 | Operador IdP | Keycloak, reino `intercambio-dgt` |
| 2 | Operador borde | Cloudflare (CA y WAF del hostname) |
| 3 | Operador borde | Reglas de denegacion en pasarela |
| 4 | Operador plataforma | Composicion del API |
| 5 | Operador datos | PostgreSQL del espejo |
| Verificación | Verificador | ERP intacto + intercambio cerrado |

## Paso 1 — Revocar tokens (operador IdP)

1. En Keycloak, deshabilite el cliente (`dgt-intercambio`) o revoque sus
   sesiones: `Clients > dgt-intercambio > Revoke` (o `kcadm.sh` segun su
   instalacion).
2. Segunda capa de emergencia del API: agregue el `jti` a
   `TOKENS_REVOCADOS` por ambiente (sin esperar expiracion).
3. Verificacion: reutilizar el token revocado → `401` uniforme.
   Verificacion local previa (sin IdP):
   `python manage.py test pruebas.unidad.prueba_validador_jwks`
   (incluye revocacion `jti` inmediata y lista `TOKENS_REVOCADOS`).

## Paso 2 — Revocar certificado de cliente (operador borde)

1. En Cloudflare: `SSL > Client Certificates` del hostname del
   intercambio → revocar el certificado de la institucion.
2. Verificacion: peticion con ese certificado → bloqueo en el borde con
   error uniforme, sin llegar al API.

## Paso 3 — Denegar en pasarela (operador borde)

1. Activar la regla WAF de denegacion total del hostname (o retirar la
   ruta publica del tunel hacia `http://nginx:80`).
2. Verificacion: cualquier ruta responde bloqueo uniforme del borde;
   el API ya no recibe trafico (`intercambio_peticiones_total` quieto).

## Paso 4 — Detener el API (operador plataforma)

1. `docker compose -f despliegue/composicion.yaml stop api` (solo el
   servicio `api`; `nginx` puede quedar respondiendo el bloqueo).
2. Verificacion: `/salud` interno deja de responder; el ERP no se toca.

## Paso 5 — Revocar acceso del espejo (operador datos)

```sql
REVOKE SELECT ON ALL TABLES IN SCHEMA intercambio
  FROM rol_lector_intercambio;
ALTER ROLE rol_lector_intercambio NOLOGIN;
```

1. Verificacion: la conexion lectora falla; el primario del ERP y la
   replicacion quedan intactos (el espejo es otra base).
2. Reversión (solo con autorizacion escrita): `NOLOGIN` → `LOGIN`,
   reconceder `SELECT` en vistas `*_v1` segun
   `base_de_datos/migraciones_espejo/orden_aplicacion.md`, y subir en
   orden inverso (4 → 1).

## Verificacion de que el ERP sigue operando (verificador)

Tras cada paso, y al final de la secuencia:

- `curl` al ERP interno (`:8001`) y al portal (`:8080`) → responden.
- Una operacion de lectura del ERP (p. ej. tablero interno) funciona.
- El intercambio esta cerrado: `buscar` no responde dato por ningun
  camino (borde bloquea o API detenida).

## Registro del incidente

Anotar fecha/hora, quien ejecuto cada paso, `jti`/certificados
revocados y codigos de correlacion afectados (de Loki por campo
`codigo_correlacion`). Sin secretos en el registro.
