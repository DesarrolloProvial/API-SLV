-- Vista de refrendos del contrato v1 (ámbito vehiculos.refrendos.lectura).
-- Fuente: historial de refrendos con placa resuelta por el periodo.
-- Orden y paginación con cursor los aplica la API (fase 3), no esta vista.
-- Excluye por construcción: observacion y motivo_anulacion (criterio interno).
CREATE SCHEMA IF NOT EXISTS intercambio;

CREATE OR REPLACE VIEW intercambio.vista_refrendos_v1 AS
SELECT
    UPPER(REGEXP_REPLACE(b.placa, '[\s-]', '', 'g')) AS placa_norma,
    b.placa AS placa,
    f.codigo_refrendo AS codigo_refrendo,
    f.fecha_refrendo AS fecha_refrendo,
    f.fecha_vencimiento AS fecha_vencimiento,
    f.estado AS estado,
    f.vigencia_anios AS vigencia_anios
FROM slv_historialrefrendovehiculo AS f
JOIN slv_vehiculoimplementacionperiodo AS r
    ON r.id = f.relacion_vehiculo_id AND r.deleted_at IS NULL
JOIN slv_vehiculobase AS b ON b.id = r.vehiculo_base_id AND b.deleted_at IS NULL
WHERE f.deleted_at IS NULL;

-- Alias sin versión: la API lee el alias; la v1 conserva el contrato.
CREATE OR REPLACE VIEW intercambio.vista_refrendos AS
SELECT * FROM intercambio.vista_refrendos_v1;
