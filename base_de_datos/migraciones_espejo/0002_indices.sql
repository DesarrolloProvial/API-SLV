-- 0002: índices del espejo sobre la tabla base replicada.
-- Ejecutar como propietario de las tablas (rol administrador del espejo, NO el
-- migrador): CONCURRENTLY no corre dentro de un bloque de transacción.
--   psql "host=<espejo> dbname=<bd> user=<admin>" -f 0002_indices.sql
-- Las expresiones deben coincidir literalmente con las vistas y con los
-- selectores de la API (fase 3); si cambian, el planificador deja de usarlos.
-- Son índices funcionales nuevos: no duplican (placa), (vigente_desde) ni
-- (deleted_at, placa) del ERP. Un btree simple sobre placa no sirve para el
-- sufijo: ordena de izquierda a derecha y un sufijo derivaría en Seq Scan.
-- El orden determinista activa DESC, placa_norma ASC lo aplica la consulta
-- (activa vive en el periodo, no en la base); estos índices resuelven el
-- filtro por sufijo y la igualdad exacta con un Index Scan.
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_base_sufijo6_norma
    ON slv_vehiculobase (
        RIGHT(UPPER(REGEXP_REPLACE(placa, '[\s-]', '', 'g')), 6),
        UPPER(REGEXP_REPLACE(placa, '[\s-]', '', 'g'))
    )
    WHERE deleted_at IS NULL;

-- Igualdad exacta por placa normalizada (expediente y extranjeras exactas).
-- El filtro tipo_placa = 'extranjera' se aplica tras unir la versión
-- administrativa (la base no contiene tipo_placa); si el convenio autoriza
-- extranjeras con volumen, revaluar un parcial dedicado (ver manual_espejo).
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_base_norma_exacta
    ON slv_vehiculobase (UPPER(REGEXP_REPLACE(placa, '[\s-]', '', 'g')))
    WHERE deleted_at IS NULL;
