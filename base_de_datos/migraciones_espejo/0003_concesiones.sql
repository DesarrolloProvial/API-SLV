-- 0003: concesiones al rol lector. Ejecutar TRAS crear las vistas y re-ejecutar
-- en cada despliegue de vistas (como migrador o superusuario del espejo):
--   psql "host=<espejo> dbname=<bd> user=<admin>" -f 0003_concesiones.sql
-- El lector obtiene SELECT solo en las vistas del contrato; nunca en tablas
-- base, nunca escritura ni DDL. Las pruebas de privilegios lo verifican.
REVOKE ALL ON ALL TABLES IN SCHEMA public, intercambio FROM rol_lector_intercambio;

GRANT USAGE ON SCHEMA intercambio TO rol_lector_intercambio;

GRANT SELECT ON
    intercambio.vista_busqueda_v1,
    intercambio.vista_expediente_v1,
    intercambio.vista_generales_v1,
    intercambio.vista_propietario_v1,
    intercambio.vista_empresa_v1,
    intercambio.vista_refrendos_v1,
    intercambio.vista_historial_v1,
    intercambio.vista_busqueda,
    intercambio.vista_expediente,
    intercambio.vista_generales,
    intercambio.vista_propietario,
    intercambio.vista_empresa,
    intercambio.vista_refrendos,
    intercambio.vista_historial
    TO rol_lector_intercambio;

-- Las futuras vistas versionadas heredan el mismo mínimo sin pasos manuales.
ALTER DEFAULT PRIVILEGES FOR ROLE rol_migrador_intercambio IN SCHEMA intercambio
    GRANT SELECT ON TABLES TO rol_lector_intercambio;

-- Endurecimiento de sesión del lector (patrón del ERP, §20 del PLAN).
ALTER ROLE rol_lector_intercambio SET search_path = intercambio, pg_catalog;
ALTER ROLE rol_lector_intercambio SET statement_timeout = '5s';
ALTER ROLE rol_lector_intercambio SET idle_in_transaction_session_timeout = '10s';
