-- 0001: roles del espejo. Idempotente; ejecutar como superusuario del espejo:
--   psql "host=<espejo> dbname=<bd> user=<admin>" -f 0001_roles.sql
-- Las claves se fijan con variables psql (nunca hay valores en el repo):
--   psql ... -v clave_migrador="$CLAVE_MIGRADOR" -v clave_lector="$CLAVE_LECTOR" -f 0001_roles.sql
-- El migrador administra vistas; el lector solo lee vistas (la API usa el lector).
CREATE SCHEMA IF NOT EXISTS intercambio;

DO $bloque$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_migrador_intercambio') THEN
        CREATE ROLE rol_migrador_intercambio WITH LOGIN
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION CONNECTION LIMIT 5;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rol_lector_intercambio') THEN
        CREATE ROLE rol_lector_intercambio WITH LOGIN
            NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION CONNECTION LIMIT 5;
    END IF;
END
$bloque$;

-- Punto de partida: el lector no posee nada en ningún esquema.
REVOKE ALL ON SCHEMA public, intercambio FROM rol_lector_intercambio;
REVOKE ALL ON ALL TABLES IN SCHEMA public, intercambio FROM rol_lector_intercambio;

-- El migrador crea y reemplaza vistas en el esquema del contrato.
GRANT USAGE, CREATE ON SCHEMA intercambio TO rol_migrador_intercambio;

-- Claves (exigen -v; sin valores reales en el repo).
ALTER ROLE rol_migrador_intercambio WITH PASSWORD :'clave_migrador';
ALTER ROLE rol_lector_intercambio WITH PASSWORD :'clave_lector';
