# Manual de recuperación (reconstruir la replicación desde cero)

> **EJECUCIÓN MANUAL GUIADA — NO AUTOMÁTICA.**
> Nada de este archivo se ejecuta solo ni desde CI. Cada paso lo corre una
> persona con el rol indicado, verificando el paso anterior antes de seguir.
> Sin valores reales ni secretos: solo nombres de variables
> (`despliegue/archivo_ambiente_ejemplo`) y marcadores `<...>` por completar
> en el gestor externo.

## 0. Principio rector

El espejo es una COPIA DERIVABLE: no se respalda, se reconstruye. Lo firme es:

- El ERP: fuente de verdad + sus respaldos (runbook de respaldos del repo
  ERP: `docs/operations/backups.md`).
- Este repo: TODO el SQL versionado (`base_de_datos/erp/`,
  `base_de_datos/migraciones_espejo/` + `orden_aplicacion.md`).
- Dokploy: el compose (`despliegue/composicion_produccion.yaml`) + los
  nombres de variables (`despliegue/archivo_ambiente_ejemplo`).
- Cloudflare: túnel, certificados de cliente, hostname y WAF.

Prevalece lo real: ante divergencia entre un manual y lo ejecutado en el
despliegue fase 1 (ver `openspec/changes/api-intercambio-vehiculos/apply.md`
en el repo ERP), manda lo ejecutado: túnel por token (`TOKEN_TUNEL`;
`TUNEL_ID` es solo referencia del modo local), R3 como excepción de
integridad del navegador (no refuerzo por IP), sin regla de ritmo en el
borde (la única del plan free la ocupa
`cf.waf.credential_check.password_leaked`) y Super Bot Fight no aplica.

## 1. Qué custodiar y qué NO respaldar

SÍ custodiar (gestor externo, nunca en el repo):

- Valores de ambiente (todas las de `archivo_ambiente_ejemplo`, en especial
  `TOKEN_TUNEL`, `CLAVE_REPLICA_ERP`, `CLAVE_ADMIN_BD`, `URL_JWKS`).
- Certificado + llave privada del cliente de cada institución (o reemitir
  desde el panel Cloudflare si se pierden).
- Respaldos del ERP (lógico `pg_dump` + físico `pg_basebackup` + WAL,
  según `docs/operations/backups.md` del repo ERP).
- En fase 2: material PKI según `despliegue/manual_pki.md` §5.
- Actas de pruebas con la contraparte (fecha, placa de prueba, correlación).

NO respaldar (y por qué):

- El espejo (`datos-espejo-produccion`): derivable por re-suscripción; un
  respaldo solo ahorra la copia inicial y se desactualiza al instante.
- Tablas del API: no hay; el API es sin estado (toda lectura va al espejo).
- El token del túnel como archivo: se regenera en el panel y se guarda como
  `TOKEN_TUNEL`; `TUNEL_ID` + credenciales solo existen en el ejemplo local.

## 2. Checklist de conectividad espejo→ERP (prerequisito de la suscripción)

Sin esto en verde, `suscripcion.sql` no levanta. Probar desde el contenedor
del espejo con el propio rol de replicación:

```sh
docker exec -it <contenedor-postgres-espejo> psql "host=<ANFITRION_ERP> port=<PUERTO_ERP> dbname=<NOMBRE_BD_ERP> user=rol_replicacion_intercambio password=<CLAVE_REPLICA_ERP>" -c "SELECT 1;"
```

Esperado: `1`. Dos vías según cómo esté publicado el Postgres del ERP:

- Vía A — red compartida (preferida, mismo servidor): los proyectos Dokploy
  `intercambio` y del ERP comparten una red Docker; `ANFITRION_ERP` es el
  nombre del servicio/contenedor del Postgres del ERP y `PUERTO_ERP` el
  interno (`5432`). Nada se expone al exterior.
- Vía B — puerto publicado u otro anfitrión: el Postgres del ERP publica
  puerto en Dokploy o vive en otro servidor; `ANFITRION_ERP` es la IP/host y
  `PUERTO_ERP` el puerto externo.

Criterio: mismo servidor → vía A; ERP en otro anfitrión o sin red común
posible → vía B (restringir origen en firewall a la IP del espejo).

## 3. Escenario A — se perdió el espejo/stack del intercambio (el ERP intacto)

El ERP NO se toca en este escenario.

1. En Dokploy, redesplegar el servicio Compose del proyecto `intercambio`
   (`despliegue/composicion_produccion.yaml`, volumen nuevo) y esperar los 4
   servicios sanos (`despliegue/manual_dokploy.md` paso 3).
2. Pasar el checklist §2 (en verde antes de seguir).
3. Ejecutar `base_de_datos/migraciones_espejo/suscripcion.sql` como
   superusuario del espejo (crea tablas + slot + copia inicial).
4. Aplicar `base_de_datos/migraciones_espejo/orden_aplicacion.md`:
   roles → índices → vistas → concesiones (pasos 1 y 3–5; el paso 2 es esta
   suscripción).
5. Pruebas gated con el rol lector:
   `URL_ESPEJO_PRUEBAS=<dsn-lector> python manage.py test pruebas.privilegios`
   (y `prueba_selectores_espejo` para columnas del contrato).
6. Verificación rápida: `count(*)` de `slv_vehiculobase` en espejo contra el
   04 del ERP + `TABLE pg_stat_subscription;` con una fila activa.

## 4. Escenario B — el ERP fue restaurado (el espejo quedó desfasado o no)

Primero restaurar el ERP con su propio runbook (`docs/operations/backups.md`
del repo ERP). Luego, según el tipo de restauración:

- Lógica (`pg_dump`): rol y publicación viven en catálogos y PUEDEN FALTAR.
  Re-ejecutar `base_de_datos/erp/01_rol_replicacion.sql` y
  `base_de_datos/erp/03_publicacion.sql` (idempotentes: solo reponen lo que
  falte), y cerrar con `04_verificacion_erp.sql`. El `wal_level` sobrevive
  (vive en `postgresql.auto.conf`, fuera del dump): solo re-aplicar 02 con
  reinicio si el 04 muestra distinto de `logical`.
- Física/PITR (`pg_basebackup` + WAL): configuración y catálogos sobreviven;
  basta `04_verificacion_erp.sql` en verde (rol, 18 tablas, REPLICA IDENTITY).

Si el espejo quedó desfasado o la suscripción no converge (ver
`despliegue/manual_resincronizacion.md` §5), seguir con el escenario A
(re-suscripción; el ERP ya no se toca).

## 5. Escenario C — se perdió TODO el servidor (reconstrucción completa)

Orden estricto; cada paso en verde antes del siguiente.

1. Servidor + Dokploy instalado y acceso al repo `DesarrolloProvial/API-SLV`.
2. Proyecto `intercambio` + UN servicio Compose al repo/rama `main` con ruta
   `despliegue/composicion_produccion.yaml` (`manual_dokploy.md` paso 1) +
   variables fase 1 (nombres en `archivo_ambiente_ejemplo`; valores en el
   gestor; `manual_dokploy.md` paso 2). Desplegar y verificar interno
   (`manual_dokploy.md` paso 3).
3. Cloudflare: crear el túnel `intercambio-dgt`, guardar el token nuevo como
   `TOKEN_TUNEL` y redesplegar; Public Hostname `intercambio.provial.gob.gt`
   → `http://nginx:80`; certificado de cliente (CA gestionada, un
   certificado por institución `dgt-intercambio`) + host asociado a mTLS;
   WAF con lo ejecutado en fase 1 — R1: sin certificado válido → bloquear;
   R2: solo `GET /api/v1/vehiculos/*` → resto bloquear; R3: omitir la
   "Comprobación de integridad del navegador" para certificados (excepción
   descubierta en la prueba real; el error 1010 de clientes de servicio era
   esa comprobación). Sin regla de ritmo (ver §0) y `nginx` como segunda
   capa (`manual_borde.md` §4 + §6). Pasar el checklist `manual_borde.md` §5.
4. ERP: restaurar desde `docs/operations/backups.md` del repo ERP y luego
   lado ERP `01_rol_replicacion.sql` → `02_configuracion_wal.sql` (+ reinicio
   en ventana) → `03_publicacion.sql` → `04_verificacion_erp.sql` en verde.
5. Espejo: checklist §2 → `suscripcion.sql` →
   `orden_aplicacion.md` (roles → índices → vistas → concesiones).
6. Pruebas gated (`URL_ESPEJO_PRUEBAS`, ver §6) + prueba de humo del borde
   con el script del operador (referencia: resultados reales fase 1 — GET con
   certificado → 401 `no_autenticado` con `codigo_correlacion`; POST → 403;
   sin certificado → 403) y acta con la contraparte
   (`manual_dokploy.md` paso 5). Fase 2 (PKI + Keycloak) según
   `manual_dokploy.md` paso 6 y `manual_pki.md`.

## 6. Verificación final común (todos los escenarios)

- `TABLE pg_stat_subscription;` (una fila activa) y `pg_subscription_rel`
  con todas las tablas en `r` (`manual_resincronizacion.md` §5).
- Conteos espejo contra ERP (`count(*)` y `max(id)` por tabla) + columnas
  del contrato (`\d intercambio.vista_*`).
- `URL_ESPEJO_PRUEBAS=<dsn-lector> python manage.py test pruebas.privilegios`
  y `prueba_selectores_espejo` en verde.
- Humo del borde (§5 paso 6) y registro del incidente/acta con fecha,
  pasos y responsable.

## Anexo. Mapa de archivos

| Pieza | Ruta |
|---|---|
| Rol / WAL / publicación / verificación ERP | `base_de_datos/erp/01_rol_replicacion.sql` … `04_verificacion_erp.sql` |
| Suscripción del espejo | `base_de_datos/migraciones_espejo/suscripcion.sql` |
| Roles → índices → vistas → concesiones | `base_de_datos/migraciones_espejo/orden_aplicacion.md` |
| Ventana + REPLICA IDENTITY (origen narrativo) | `despliegue/manual_espejo.md` |
| Resincronización y anti-drift | `despliegue/manual_resincronizacion.md` |
| Compose + variables + borde + prueba DGT | `despliegue/manual_dokploy.md`, `despliegue/manual_borde.md` |
| PKI fase 2 | `despliegue/manual_pki.md` |
| Respaldos del ERP (repo ERP) | `docs/operations/backups.md` |
