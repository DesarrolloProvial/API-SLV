# Manual del espejo (ventana del ERP + suscripción)

> **EJECUCIÓN MANUAL GUIADA — NO AUTOMÁTICA.**
> Nada de este archivo se ejecuta solo ni desde CI. Cada paso lo corre un
> operador con acceso autorizado, en la ventana agendada, verificando el paso
> anterior antes de seguir. Sin secretos ni valores reales: solo nombres de
> variables (`despliegue/archivo_ambiente_ejemplo`).
>
> **Fuente de verdad ejecutable:** los comandos de este manual viven también
> como scripts versionados e idempotentes: lado ERP en `base_de_datos/erp/`
> (`01_rol_replicacion.sql` … `04_verificacion_erp.sql`) y lado espejo en
> `base_de_datos/migraciones_espejo/suscripcion.sql`. Ante divergencia entre
> este texto y lo ejecutado en el despliegue real (`openspec/changes/
> api-intercambio-vehiculos/apply.md` en el repo ERP), prevalece lo real.

## 0. Requisitos previos

- Ventana de reinicio del primario del ERP agendada y comunicada.
- Respaldo reciente del primario verificado.
- PostgreSQL 18 en ambos lados y red del espejo hacia el ERP abierta.
- Variables cargadas en el gestor externo: `ANFITRION_ERP`, `PUERTO_ERP`,
  `NOMBRE_BD_ERP`, `USUARIO_REPLICA_ERP`, `CLAVE_REPLICA_ERP`,
  `PUBLICACION_INTERCAMBIO`, `SLOT_INTERCAMBIO`.

## 1. Crear el rol de replicación (antes de la ventana, sin reinicio)

Solo `REPLICATION` + `SELECT` de las tablas publicadas; sin nada más:

```sql
CREATE ROLE rol_replicacion_intercambio WITH LOGIN REPLICATION CONNECTION LIMIT 1;
GRANT CONNECT ON DATABASE "<NOMBRE_BD_ERP>" TO rol_replicacion_intercambio;
GRANT USAGE ON SCHEMA public TO rol_replicacion_intercambio;
GRANT SELECT ON
    slv_vehiculobase, slv_vehiculoimplementacionperiodo,
    slv_vehiculotitularidadperiodo, slv_vehiculoadministrativoversion,
    slv_historialrefrendovehiculo, slv_empresaimplementada,
    slv_empresaimplementadora, slv_dispositivocatalogo,
    slv_clasificacionvehiculo, slv_tipovehiculo, slv_usovehiculo,
    slv_marcavehiculo, slv_departamento, slv_municipio,
    slv_eventoimplementacion, slv_vehiculoevento,
    slv_cuposolicitudvehiculo, slv_documentoexpediente
    TO rol_replicacion_intercambio;
```

Verificación: `SELECT rolname, rolreplication, rolconnlimit FROM pg_roles
WHERE rolname = 'rol_replicacion_intercambio';` (replicación sí, límite 1).

## 2. Activar `wal_level = logical` (en la ventana, con reinicio)

```sql
SHOW wal_level; -- hoy: replica
ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_wal_senders = 5;
ALTER SYSTEM SET max_replication_slots = 5;
ALTER SYSTEM SET max_slot_wal_keep_size = '10GB'; -- partida interna, calibrar
```

Reiniciar el servicio postgres del ERP y verificar:

```sql
SHOW wal_level; -- debe decir: logical
```

Revertir exige otra ventana; por eso el monitoreo del slot es día 0
(`observabilidad/reglas_alertas.yaml`).

## 3. Crear la publicación (en la ventana, sin reinicio adicional)

Filas completas a propósito: la exclusión de sensibles vive en las vistas del
espejo, así una columna nueva no rompe la replicación (anti-drift, §6):

```sql
CREATE PUBLICATION pub_intercambio FOR TABLE
    slv_vehiculobase, slv_vehiculoimplementacionperiodo,
    slv_vehiculotitularidadperiodo, slv_vehiculoadministrativoversion,
    slv_historialrefrendovehiculo, slv_empresaimplementada,
    slv_empresaimplementadora, slv_dispositivocatalogo,
    slv_clasificacionvehiculo, slv_tipovehiculo, slv_usovehiculo,
    slv_marcavehiculo, slv_departamento, slv_municipio,
    slv_eventoimplementacion, slv_vehiculoevento,
    slv_cuposolicitudvehiculo, slv_documentoexpediente;
```

Verificación: `SELECT count(*) FROM pg_publication_tables
WHERE pubname = 'pub_intercambio';` (esperado: 18).

## 4. Verificación post-ventana (ERP)

- `SHOW wal_level;` → `logical`.
- Publicación con 18 tablas (§3).
- Rol con solo replicación y lectura (§1).
- El ERP opera normal (`:8001/:8080` responden); la ventana termina aquí.

## 5. Suscripción en el espejo + snapshot inicial (tras la ventana)

```sql
CREATE SUBSCRIPTION sub_intercambio
    CONNECTION 'host=<ANFITRION_ERP> port=<PUERTO_ERP> dbname=<NOMBRE_BD_ERP>
        user=rol_replicacion_intercambio password=<CLAVE_REPLICA_ERP>'
    PUBLICATION pub_intercambio
    WITH (copy_data = true, create_slot = true, slot_name = 'slot_intercambio');
```

Verificación: `TABLE pg_stat_subscription;` (una fila activa),
`SELECT count(*) FROM slv_vehiculobase;` en ambos lados (el espejo converge
con rezago acotado) y luego `base_de_datos/migraciones_espejo/orden_aplicacion.md`.

## Anexo A. REPLICA IDENTITY por tabla publicada

Regla: con PK basta el valor por defecto; sin PK ni índice único, fijar
`FULL` (en el ERP, con ventana si exige reinicio de la suscripción) y
probar un UPDATE/DELETE en preproducción. Se espera `id` (Django por defecto).

```sql
SELECT n.nspname AS esquema, c.relname AS tabla,
    CASE c.relreplident WHEN 'd' THEN 'defecto (usa PK)' WHEN 'n' THEN 'NOTHING (¡revisar!)'
        WHEN 'f' THEN 'FULL' WHEN 'i' THEN 'índice único' END AS replica_identity,
    EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = c.oid AND i.indisprimary) AS tiene_pk
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r' AND c.relname LIKE 'slv\_%' ESCAPE '\' ORDER BY 1, 2;
```

| Tablas | Cambios esperados | Acción |
|---|---|---|
| `slv_vehiculotitularidadperiodo`, `slv_vehiculoadministrativoversion`, `slv_historialrefrendovehiculo` | UPDATE/DELETE habituales | Confirmar PK; si falta → `FULL` |
| `slv_vehiculobase`, periodos de implementación, empresas, eventos, cupo, documentos | INSERT + UPDATE de estado | Confirmar PK; si falta → `FULL` |
| Catálogos (7) | Casi inmutables | Confirmar PK; `FULL` solo si falta |
