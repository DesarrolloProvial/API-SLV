-- 04: verificacion de estado del lado ERP (solo lectura).
--
-- Proposito: comprobar de una pasada que la ventana dejo todo en verde
-- (WAL, rol, publicacion de 18 tablas, REPLICA IDENTITY) y tomar el conteo
-- de referencia para comparar con el espejo tras la suscripcion.
-- Version ejecutable de `despliegue/manual_espejo.md` §4 + Anexo A.
--
-- Prerequisitos: ninguno de escritura; basta un rol con lectura del
-- catalogo y SELECT en `slv_vehiculobase`. Sin variables psql.
--
-- Como ejecutarlo (conectado a la BD del ERP):
--   psql "host=<ANFITRION_ERP> dbname=<NOMBRE_BD_ERP> user=<ADMIN_ERP>" -f 04_verificacion_erp.sql
-- Nota de uso por pegado: el archivo no recibe parametros; puede pegarse
-- tal cual en psql interactivo.
--
-- Salida esperada: wal_level=logical; rol con replicacion=t, limite=1 y
-- super=f; tablas_publicadas=18; toda tabla slv_% con PK (o FULL donde se
-- documento); y el conteo de filas de referencia.

-- 1. WAL efectivo (esperado: logical).
SHOW wal_level;

-- 2. Rol de replicacion (esperado: t / 1 / f).
SELECT rolname, rolreplication, rolconnlimit, rolsuper FROM pg_roles
WHERE rolname = 'rol_replicacion_intercambio';

-- 3. Publicacion completa (esperado: 18).
SELECT count(*) AS tablas_publicadas FROM pg_publication_tables
WHERE pubname = 'pub_intercambio';

-- 4. REPLICA IDENTITY por tabla publicada (Anexo A del manual del espejo).
-- Regla: con PK basta el valor por defecto; sin PK ni indice unico, fijar
-- FULL en el ERP y probar un UPDATE/DELETE en preproduccion.
SELECT n.nspname AS esquema, c.relname AS tabla,
    CASE c.relreplident WHEN 'd' THEN 'defecto (usa PK)' WHEN 'n' THEN 'NOTHING (¡revisar!)'
        WHEN 'f' THEN 'FULL' WHEN 'i' THEN 'índice único' END AS replica_identity,
    EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = c.oid AND i.indisprimary) AS tiene_pk
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r' AND c.relname LIKE 'slv\_%' ESCAPE '\' ORDER BY 1, 2;

-- 5. Conteo de referencia (comparar con el mismo conteo en el espejo).
SELECT count(*) AS filas_vehiculobase_erp FROM slv_vehiculobase;
