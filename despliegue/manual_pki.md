# Manual PKI interna (step-ca para servicios internos)

> **EJECUCIÓN MANUAL GUIADA — NO AUTOMÁTICA.**
> Nada de este archivo se ejecuta solo ni desde CI. Cada paso lo corre una
> persona con el rol indicado, verificando el paso anterior antes de seguir.
> Sin valores reales ni secretos: solo nombres de variables
> (`despliegue/archivo_ambiente_ejemplo`) y marcadores `<...>` por completar
> en el gestor externo.

## 0. Objetivo y frontera

PKI INTERNA con `step-ca` para certificados de servicio internos:

- `nginx` ↔ `api` (TLS interno entre pasarela y aplicación).
- `api` ↔ PostgreSQL espejo con `sslmode=verify-full` (ya exigido en
  `configuracion/ajustes_produccion.py:39`; sin certificado válido la API no
  conecta).
- `api` ↔ Keycloak (TLS hacia el IdP y hacia `URL_JWKS`).

Frontera explícita: los certificados de CLIENTE para la CONTRAPARTE (DGT)
salen de la CA GESTIONADA de Cloudflare en el borde, no de nuestra CA
(`BYOCA` es plan Enterprise y no se usa). Nuestra PKI NO cubre el borde:
no emite ni valida el `mTLS` externo. Ver `despliegue/manual_borde.md` §2.

## 1. Topología recomendada

- Raíz (`root CA`) OFFLINE: solo firma la intermedia, vive fuera de línea
  bajo custodia (ver §5). Nunca atiende tráfico.
- Intermedia (`intermediate CA`) ONLINE: la única que emite hojas. Corre en
  `step-ca` como servicio dedicado en la infra nueva (Dokploy) con volumen
  persistente para `$(STEP_CA_DB)` y la llave de la intermedia.
- Provisionador ACME en `step-ca` para emisión y renovación automática de
  hojas de corta vida (`VIGENCIA_HOJA_DIAS`, días, a fijar en convenio).
- Nota de desarrollo (opcional, sin sobre-ingeniería): en
  `despliegue/composicion.yaml` puede agregarse un servicio `pki` solo para
  desarrollo con la misma imagen `step-ca`, sin volumen compartido con
  producción y sin material real. En producción `step-ca` vive en Dokploy,
  no en la composición de desarrollo.

## 2. Inventario de certificados necesarios

| Servicio | Tipo | CN/SAN esperado (placeholder) | Uso | Renovación |
|---|---|---|---|---|
| `postgres-espejo` | servidor | CN=`<ESPEJO_INTERNO>` SAN=`<ESPEJO_INTERNO>` | TLS `api`→PG (`verify-full`) | ACME, corta |
| `api` (cliente PG) | cliente | CN=`<USUARIO_LECTOR>` | `hostssl ... cert` en `pg_hba` | ACME, corta |
| `nginx` | servidor | CN=`<NGINX_INTERNO>` SAN=`<NGINX_INTERNO>` | TLS interno hacia `api` | ACME, corta |
| `api` | servidor | CN=`<API_INTERNA>` SAN=`<API_INTERNA>` | TLS `nginx`→`api` | ACME, corta |
| `keycloak` | servidor | CN=`<IDP_INTERNO>` SAN=`<IDP_INTERNO>` | TLS `api`→IdP y `URL_JWKS` | ACME, corta |
| emergencia | cliente | CN=`<OPERADOR_PKI>` | Emisión manual si ACME cae | Manual |

Las huellas de cada hoja emitida se anotan en
`despliegue/inventario_huellas.md` (sin secretos).

## 3. Pasos manuales guiados

### 3.1 Inicializar raíz + intermedia (custodio raíz)

```sh
step ca init --name "<PKI_INTERNA>" --dns "<CA_INTERNA>" \
  --address "<CA_INTERNA>:<PUERTO_CA>" \
  --provisioner "<OPERADOR_PKI>"
```

1. Genera raíz offline + intermedia online (contraseñas en gestor externo).
2. Guarda el material según §5 ANTES de seguir.
3. Verificación: `step certificate inspect <RUTA_INTERMEDIA_CRT>`
   muestra emisor = raíz y vigencia esperada.

### 3.2 Custodiar el material (custodio raíz)

1. Raíz offline: medio extraíble cifrado + copia de respaldo (ver §5).
2. Intermedia: solo en el volumen persistente de `step-ca` y en respaldo.
3. Verificación: el repo y la imagen NO contienen llaves
   (`grep -ri "BEGIN.*PRIVATE KEY" despliegue/ configuracion/` vacío).

### 3.3 Desplegar `step-ca` (operador plataforma, Dokploy)

1. Servicio dedicado `pki` con volumen persistente y variables
   `DIRECCION_CA_INTERNA`, `HUELLA_CA_INTERMEDIA`, `URL_CRL_INTERMEDIA`.
2. Expone solo red interna; nunca por el túnel ni por el borde.
3. Verificación: `curl <DIRECCION_CA_INTERNA>/health` responde 200 en
   red interna y nada desde internet.

### 3.4 Crear provisionador ACME (operador PKI)

```sh
step ca provisioner add "<PROVISIONADOR_ACME>" --type ACME
```

1. Un provisionador para hojas automáticas; otro manual para emergencia.
2. Verificación: `step ca provisioner list` muestra ambos; el ACME con
   `claims` de vigencia corta (`VIGENCIA_HOJA_DIAS`).

### 3.5 Emitir para PostgreSQL espejo (operador datos + operador PKI)

```sh
step ca certificate "<ESPEJO_INTERNO>" <RUTA_SERVIDOR_CRT> <RUTA_SERVIDOR_KEY>
step ca certificate "<USUARIO_LECTOR>" <RUTA_CLIENTE_CRT> <RUTA_CLIENTE_KEY>
```

1. En el espejo: `ssl = on`, `ssl_cert_file`, `ssl_key_file`,
   `ssl_ca_file` (intermedia) y `pg_hba.conf` con
   `hostssl ... cert` para el rol lector.
2. Reinicia el servicio postgres del espejo (solo el espejo, nunca el ERP).
3. Verificación:
   `openssl s_client -connect <ESPEJO_INTERNO>:<PUERTO_BD> -showcerts`
   encadena a la intermedia; `step certificate inspect` confirma
   CN/SAN y vigencia; la API conecta con `sslmode=verify-full`.

### 3.6 Emitir para `nginx` y `api` (operador plataforma + operador PKI)

```sh
step ca certificate "<NGINX_INTERNO>" <RUTA_NGINX_CRT> <RUTA_NGINX_KEY>
step ca certificate "<API_INTERNA>" <RUTA_API_CRT> <RUTA_API_KEY>
```

1. `nginx`: `ssl_certificate` + `ssl_certificate_key`; confía en la
   intermedia para el origen `api`.
2. `api`: presenta su hoja hacia `nginx` y confía en `HUELLA_CA_INTERMEDIA`
   para `URL_JWKS` y el espejo.
3. Verificación: `curl` interno `nginx`→`api` con TLS válido;
   `step certificate inspect` por hoja; `nginx -t` en despliegue.

### 3.7 Emitir para Keycloak (operador IdP + operador PKI)

```sh
step ca certificate "<IDP_INTERNO>" <RUTA_IDP_CRT> <RUTA_IDP_KEY>
```

1. Keycloak termina TLS con su hoja; la API valida contra la intermedia.
2. Verificación: `URL_JWKS` responde por TLS válido y la API valida
   tokens (matriz de ámbitos en verde); huella anotada en el inventario.

## 4. Rotación y revocación sin caída

- Doble validez en ventana: emitir la hoja nueva ANTES de que expire la
  vigente (p. ej. a la mitad de `VIGENCIA_HOJA_DIAS`), servir ambas durante
  la ventana, conmutar clientes, y solo entonces retirar la vieja.
- Renovación automática: ACME renueva hojas de corta vida sin operador;
  el operador solo vigila expiración (alerta a calibrar en convenio).
- Revocación (CRL): `step ca revoke --cert <HOJA> --key <LLAVE>` y publica
  en `URL_CRL_INTERMEDIA`; los servicios recargan confianza sin reinicio
  salvo postgres (reinicio solo del espejo).
- Compromiso de la intermedia: revocar la intermedia desde la raíz offline,
  emitir intermedia nueva, reemitir TODAS las hojas, actualizar
  `HUELLA_CA_INTERMEDIA` y el inventario, y registrar el incidente.
  La raíz solo se rota con ventana y doble custodia (§5).

## 5. Custodia y responsables

| Material | Custodia (rol, no persona) | Respaldo |
|---|---|---|
| Llave raíz + contraseña | Custodio raíz (doble control) | Medio offline cifrado + copia sellada |
| Llave intermedia + contraseña | Operador PKI | Volumen `step-ca` + copia cifrada |
| Contraseñas y `HUELLA_CA_INTERMEDIA` | Gestor externo, nunca en claro | Rotación de acceso por rol |
| Hojas de servicio | Cada operador de servicio | Reemisión ACME, no respaldo |

Reglas: nunca en el repo, ni en la imagen, ni en registros; nunca por chat
ni correo; todo acceso queda anotado con fecha y rol.

## 6. Interacción con el kill-switch

| Capa | Qué revoca | Dónde |
|---|---|---|
| Confianza de cliente de la contraparte | Certificado de la institución | Cloudflare (paso 2 de `manual_kill_switch.md`) |
| Tokens de la contraparte | Cliente `dgt-intercambio` / `jti` | Keycloak + `TOKENS_REVOCADOS` (paso 1) |
| Internos (`nginx`/`api`/PG/IdP) | Hojas de nuestra PKI (CRL) | `step-ca` (este manual §4) |

Ante incidente externo se ejecuta el kill-switch sin tocar la PKI interna;
ante compromiso interno se revocan hojas aquí ADEMÁS del kill-switch.
Ver `despliegue/manual_kill_switch.md` pasos 1–2 y verificación del ERP.

## 7. Variables y archivos

Nombres nuevos en `despliegue/archivo_ambiente_ejemplo` (§PKI, solo nombres):
`DIRECCION_CA_INTERNA`, `HUELLA_CA_INTERMEDIA`, `PROVISIONADOR_ACME`,
`VIGENCIA_HOJA_DIAS`, `URL_CRL_INTERMEDIA`. Huellas en
`despliegue/inventario_huellas.md` (plantilla sin secretos).
