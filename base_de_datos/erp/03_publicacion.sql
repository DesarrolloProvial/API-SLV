-- 03: publicacion de las tablas del intercambio (lado ERP).
--
-- Proposito: publicar las 18 tablas que replica el espejo, con filas
-- completas a proposito: la exclusion de sensibles vive en las vistas del
-- espejo, asi una columna nueva no rompe la replicacion (anti-drift).
-- Version ejecutable de `despliegue/manual_espejo.md` §3.
--
-- Prerequisitos: superusuario del ERP; 01 aplicado (rol) y 02 aplicado con
-- reinicio verificado (`SHOW wal_level;` = logical). Sin variables psql.
--
-- Como ejecutarlo (conectado a la BD del ERP como administrador):
--   psql "host=<ANFITRION_ERP> dbname=<NOMBRE_BD_ERP> user=<ADMIN_ERP>" -f 03_publicacion.sql
-- Nota de uso por pegado: el archivo no recibe parametros; puede pegarse
-- tal cual en psql interactivo conectado a la BD del ERP.
--
-- Idempotente: si `pub_intercambio` ya existe no se recrea (aviso NOTICE) y
-- la verificacion confirma el estado. Si ya existia con menos de 18 tablas,
-- NO se auto-modifica: conciliar a mano con
-- `ALTER PUBLICATION pub_intercambio ADD TABLE <tabla>;` y re-verificar.
--
-- Salida esperada: tablas_publicadas=18 y la lista de las 18.

DO $bloque$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'pub_intercambio') THEN
        CREATE PUBLICATION pub_intercambio FOR TABLE
            slv_vehiculobase, slv_vehiculoimplementacionperiodo,
            slv_vehiculotitularidadperiodo, slv_vehiculoadministrativoversion,
            slv_historialrefrendovehiculo, slv_empresaimplementada,
            slv_empresaimplementadora, slv_dispositivocatalogo,
            slv_clasificacionvehiculo, slv_tipovehiculo, slv_usovehiculo,
            slv_marcavehiculo, slv_departamento, slv_municipio,
            slv_eventoimplementacion, slv_vehiculoevento,
            slv_cuposolicitudvehiculo, slv_documentoexpediente;
    ELSE
        RAISE NOTICE 'La publicacion pub_intercambio ya existe: no se recrea (verificacion abajo).';
    END IF;
END
$bloque$;

-- Verificacion embebida (esperado: 18).
SELECT count(*) AS tablas_publicadas FROM pg_publication_tables
WHERE pubname = 'pub_intercambio';
SELECT schemaname, tablename FROM pg_publication_tables
WHERE pubname = 'pub_intercambio' ORDER BY 1, 2;
