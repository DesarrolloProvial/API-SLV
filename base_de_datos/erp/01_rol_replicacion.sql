-- 01: rol de replicacion del intercambio (lado ERP).
--
-- Proposito: crear el rol lector que usa la suscripcion del espejo, con el
-- minimo necesario y nada mas: LOGIN + REPLICATION, limite de 1 conexion, y
-- SELECT solo sobre las 18 tablas publicadas (ver 03_publicacion.sql).
-- Es la version ejecutable de `despliegue/manual_espejo.md` §1.
--
-- Prerequisitos: superusuario del ERP; valores de las variables a mano
-- (solo nombres, los valores viven en el gestor externo).
--
-- Como ejecutarlo (conectado a la BD `postgres` como administrador):
--   psql "host=<ANFITRION_ERP> dbname=postgres user=<ADMIN_ERP>" -v nombre_bd="<NOMBRE_BD_ERP>" -v clave_replica="$CLAVE_REPLICA_ERP" -f 01_rol_replicacion.sql
-- Nota de uso por pegado: si lo ejecuta pegando en psql interactivo,
-- sustituya :"nombre_bd" por el nombre real entre comillas dobles y
-- :'clave_replica' por la clave real entre comillas simples.
--
-- Idempotente: re-ejecutable sin fallar. Si el rol ya existe, reafirma sus
-- atributos y su clave (caso: restauracion logica del ERP, ver
-- `despliegue/manual_recuperacion.md` escenario B).
-- Usa `\gexec` de psql (la sentencia se genera condicionalmente y se ejecuta
-- fuera de bloque; las `:'variables'` NO se interpolan dentro de bloques
-- dollar-quoted).
--
-- Salida esperada: una fila con rolreplication=t, rolconnlimit=1,
-- rolsuper=f; y tablas_con_select=18.

SELECT CASE
    WHEN EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_replicacion_intercambio')
    THEN $$ALTER ROLE rol_replicacion_intercambio WITH LOGIN REPLICATION
        NOSUPERUSER NOCREATEDB NOCREATEROLE CONNECTION LIMIT 1
        PASSWORD $$ || quote_literal(:'clave_replica') || $$;$$
    ELSE $$CREATE ROLE rol_replicacion_intercambio WITH LOGIN REPLICATION
        NOSUPERUSER NOCREATEDB NOCREATEROLE CONNECTION LIMIT 1
        PASSWORD $$ || quote_literal(:'clave_replica') || $$;$$
END \gexec

GRANT CONNECT ON DATABASE :"nombre_bd" TO rol_replicacion_intercambio;
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

-- Verificacion embebida (esperado: t / 1 / f, y 18).
SELECT rolname, rolreplication, rolconnlimit, rolsuper FROM pg_roles
WHERE rolname = 'rol_replicacion_intercambio';
SELECT count(*) AS tablas_con_select FROM information_schema.role_table_grants
WHERE grantee = 'rol_replicacion_intercambio' AND privilege_type = 'SELECT';
