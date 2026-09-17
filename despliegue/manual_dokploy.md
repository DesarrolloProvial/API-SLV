# Manual de despliegue en Dokploy (proyecto `intercambio`)

> **EJECUCIÓN MANUAL GUIADA — NO AUTOMÁTICA.**
> Nada de este archivo se ejecuta solo ni desde CI. Cada paso lo corre una
> persona con el rol indicado, verificando el paso anterior antes de seguir.
> Sin valores reales ni secretos: solo nombres de variables
> (`despliegue/archivo_ambiente_ejemplo`) y marcadores `<...>` por completar
> en el gestor de Dokploy. El usuario conoce su Dokploy: cada referencia a la
> interfaz se describe por propósito, no por etiqueta exacta.

Contexto: el stack vive en el MISMO servidor del ERP pero en un proyecto
Dokploy APARTE (`intercambio`), con el mismo patrón del ERP (servicio
Compose apuntando al repo `DesarrolloProvial/API-SLV`). La entrada es SOLO
por el túnel; ningún servicio publica puertos al anfitrión. Los recursos
(CPU/RAM/disco) se comparten con el ERP: vigilar el tablero del servidor
tras el primer despliegue y dimensionar antes del piloto.

## Paso 0 — Requisitos

Qué: tener listo el proyecto nuevo, el acceso al repo y las variables.
Dónde: panel de Dokploy + gestor de secretos + panel Cloudflare.

1. Proyecto nuevo `intercambio` creado en Dokploy (vacío, sin servicios).
2. El repo `DesarrolloProvial/API-SLV` ya conectado en Dokploy (acceso OK).
3. Variables listas en el gestor (solo nombres; valores fuera del repo).
4. Token del túnel gestionado creado en Cloudflare (`Zero Trust`, túnel
   `intercambio-dgt`); guardado como `TOKEN_TUNEL` en el gestor.
5. Hostname reservado: `<DOMINIO_INTERCAMBIO>` (p. ej.
   `intercambio.provial.gob.gt`, a confirmar en convenio).

Verificación: el proyecto existe, el repo responde y el gestor muestra
todas las variables del paso 2 (sin valores en claro en el repo).
Si falla: no seguir; sin token ni variables no hay despliegue sano.

## Paso 1 — Servicio Compose de producción

Qué: crear UN servicio de tipo Compose dentro del proyecto `intercambio`.
Dónde: proyecto `intercambio` → crear servicio → opción de Compose desde
repositorio git.

1. Apuntar al repo `DesarrolloProvial/API-SLV`, rama `main`.
2. Ruta del archivo compose: `despliegue/composicion_produccion.yaml`.
3. NO tocar `despliegue/composicion.yaml` (es de desarrollo local).
4. No declarar puertos publicados: el compose ya viene sin `ports:`.

Verificación: el servicio muestra los 4 componentes (`api`,
`postgres-espejo`, `nginx`, `tunel`) antes del primer despliegue.
Si falla: revisar repo/rama/ruta; nada se despliega a ciegas.

## Paso 2 — Variables de entorno

Qué: cargar las variables en el campo de entorno del servicio Compose.
Dónde: configuración del servicio → sección de variables de entorno.

| Servicio | Variables (solo nombres) |
|---|---|
| `api` | `LLAVE_SECRETA`, `ANFITRIONES_PERMITIDOS`, `NOMBRE_BD`, `USUARIO_BD`, `CLAVE_BD`, `PUERTO_BD`, `ALIAS_ESPEJO`, `PERMITIR_PLACAS_EXTRANJERAS`, `TOPE_CANDIDATAS`, `TOPE_REFERENDOS`, `TOPE_HISTORIAL`, `URL_JWKS`, `EMISOR_JWT`, `AUDIENCIA_JWT`, `TOLERANCIA_RELOJ_SEG`, `TIEMPO_CACHE_JWKS_SEG`, `TOKENS_REVOCADOS`, `LIMITE_BUSCAR_TOPE`, `LIMITE_RECURSO_TOPE`, `VENTANA_LIMITE_SEG`, `REDES_METRICAS_PERMITIDAS` |
| `postgres-espejo` | `NOMBRE_BD`, `USUARIO_BD`, `CLAVE_BD` (como `POSTGRES_*`) |
| `tunel` | `TOKEN_TUNEL` (el túnel va por token; `TUNEL_ID` es solo referencia del modo local con credenciales y aquí NO se usa) |

Notas:

- `ANFITRION_BD` queda fijo a `postgres-espejo` (nombre del servicio).
- Fase 1: `URL_JWKS`/`EMISOR_JWT`/`AUDIENCIA_JWT` llevan los valores
  RESERVADOS del convenio (el IdP real llega en el paso 6); producción
  exige `URL_JWKS` no vacía y sin IdP toda petición responde 401 uniforme.
- Fase 2 (aún NO cargar): `DIRECCION_CA_INTERNA`,
  `HUELLA_CA_INTERMEDIA`, `PROVISIONADOR_ACME`, `VIGENCIA_HOJA_DIAS`,
  `URL_CRL_INTERMEDIA` (PKI) + valores reales del IdP.
- Espejo aparte (paso 7): `ANFITRION_ERP`, `PUERTO_ERP`, `NOMBRE_BD_ERP`,
  `USUARIO_REPLICA_ERP`, `CLAVE_REPLICA_ERP`, `PUBLICACION_INTERCAMBIO`,
  `SLOT_INTERCAMBIO`; `URL_ESPEJO_PRUEBAS` solo habilita pruebas locales.

Verificación: todas las de fase 1 presentes; ninguna de fase 2 mezclada.
Si falla: completar antes de desplegar; un secreto ausente tumba el API.

## Paso 3 — Despliegue y verificación interna (nada expuesto)

Qué: desplegar y comprobar cada capa solo por red interna.
Dónde: registro del despliegue en Dokploy + terminal del servidor
(`docker exec`) + panel Cloudflare (estado del túnel).

1. Desplegar el servicio Compose y esperar estado sano en los 4.
2. `api` responde `/salud`: ejecutar desde dentro de la red interna
   (p. ej. `docker exec` contra `api` o un contenedor de la red
   `red-intercambio`) → 200.
3. `/metricas` solo interna: misma prueba interna → 200; desde fuera del
   servidor no hay ruta (sin puertos publicados no hay cómo alcanzarla).
4. `postgres-espejo` arriba: el healthcheck (`pg_isready`) en verde y el
   `api` no registra errores de conexión.
5. `nginx` levanta con la conf montada: sin errores en su registro y
   `nginx -t` válido dentro del contenedor.
6. Túnel CONECTADO: el panel Cloudflare muestra el túnel
   `intercambio-dgt` con el conector activo (puede tardar ~1 min).

Verificación: 200 interno en `/salud` y `/metricas`, postgres verde,
túnel CONECTADO, cero puertos publicados en el anfitrión.
Si falla: leer el registro del servicio que esté en rojo; reintentar el
despliegue; no tocar el borde hasta que todo esté verde.

## Paso 4 — Borde Cloudflare (hostname + mTLS + WAF)

Qué: cerrar el borde según `despliegue/manual_borde.md` §2–§3.
Dónde: panel Cloudflare (túnel, certificados, reglas) + pruebas con curl.

1. Hostname público del túnel → `http://nginx:80`
   (`manual_borde.md` §1).
2. Certificado de cliente: crear la CA gestionada del hostname y emitir
   UN certificado por institución (`dgt-intercambio`), sin compartidos
   (manual §2).
3. WAF: R1 (sin certificado válido → bloquear) y R2 (solo
   `GET /api/v1/vehiculos/*` → resto bloquear); R3–R5 en reserva
   (manual §3). Límite de ritmo sobre `buscar` (manual §4).
4. Pasar el checklist §5 del manual (bloqueos uniformes, `/salud` y
   `/metricas` solo internas, sin `Authorization`/placas en registros).

Verificación: sin certificado → bloqueo en borde; `POST` → denegado.
Si falla: revisar hostname/WAF antes de invitar a la contraparte.

## Paso 5 — Prueba temprana con la DGT

Qué: primera llamada real de punta a punta, con acta.
Dónde: internet (equipo de la DGT) + registros del API.

1. Instalar el certificado de cliente en el equipo de prueba de la DGT.
2. Consumir `GET /api/v1/vehiculos/buscar?placa=<PLACA_PRUEBA>`.
3. Resultado esperado en fase 1: el borde deja pasar (mTLS OK) y el API
   responde 401 uniforme (el IdP real llega en el paso 6); la tubería
   queda probada sin exponer dato.
4. Levantar acta: fecha, placa de prueba, código de correlación,
   resultado y asistentes.

Verificación: acta firmada con el 401 esperado y correlación trazable.
Si falla: si bloquea el borde → paso 4; si no hay correlación → paso 3.

## Paso 6 — FASE 2: PKI interna + Keycloak real

Qué: agregar `step-ca` y el IdP, redesplegar y re-verificar.
Dónde: Dokploy (nuevos servicios) + `step-ca` + Keycloak + terminal.

1. Desplegar `step-ca` como servicio de la misma red (sin puertos) según
   `despliegue/manual_pki.md` §3.1–§3.5; anotar huellas en
   `despliegue/inventario_huellas.md`.
2. Keycloak real: reino `intercambio-dgt`, cliente `dgt-intercambio`,
   5 ámbitos (`vehiculos.lectura` + 4 por recurso); cargar
   `URL_JWKS`/`EMISOR_JWT`/`AUDIENCIA_JWT` reales en el gestor.
3. Redesplegar el servicio Compose.
4. Re-verificación: sin token → 401 uniforme; con token válido y ámbito
   → 200; con ámbito insuficiente → 403.

Verificación: matriz 401/403/200 en verde y huellas anotadas.
Si falla: no abrir a la DGT; depurar IdP/PKI en red interna primero.

## Paso 7 — La ventana ERP va aparte (no mezclar)

Qué: recordar que la replicación es OTRA ventana, OTRO día, OTRO manual.
Dónde: `despliegue/manual_espejo.md` (+ `manual_resincronizacion.md`).

La ventana del ERP (rol de replicación, `wal_level`, publicación,
suscripción) se agenda y ejecuta por separado; este despliegue NO toca el
ERP ni sus servicios. Verificación de ese frente en su propio manual.
Si falla algo del espejo: no se toca este stack; se sigue el runbook.
