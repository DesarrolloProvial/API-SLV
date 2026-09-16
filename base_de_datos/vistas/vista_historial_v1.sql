-- Vista de historial del contrato v1 (ámbito vehiculos.historial.lectura).
-- Fuente: periodos de implementación históricos (vigentes y dados de baja).
-- «activa» se calcula como (fecha_baja IS NULL). El motivo de baja se expone
-- solo como código convenido; el detalle y el contexto quedan excluidos.
-- Excluye por construcción: motivo_baja_detalle, motivo_baja_contexto,
-- motivo_aprobacion, motivo_rechazo y snapshots con nit.
CREATE SCHEMA IF NOT EXISTS intercambio;

CREATE OR REPLACE VIEW intercambio.vista_historial_v1 AS
SELECT
    UPPER(REGEXP_REPLACE(b.placa, '[\s-]', '', 'g')) AS placa_norma,
    b.placa AS placa,
    r.codigo_correlativo AS codigo_correlativo,
    r.estado_aprobacion AS estado_aprobacion,
    (r.fecha_baja IS NULL) AS activa,
    r.vigente_desde AS vigente_desde,
    r.fecha_baja AS fecha_baja,
    r.motivo_baja_codigo AS motivo_baja_codigo,
    e.nombre_empresa AS empresa_implementadora
FROM slv_vehiculoimplementacionperiodo AS r
JOIN slv_vehiculobase AS b ON b.id = r.vehiculo_base_id AND b.deleted_at IS NULL
LEFT JOIN slv_empresaimplementadora AS e
    ON e.id = r.empresa_implementadora_id AND e.deleted_at IS NULL
WHERE r.deleted_at IS NULL;

-- Alias sin versión: la API lee el alias; la v1 conserva el contrato.
CREATE OR REPLACE VIEW intercambio.vista_historial AS
SELECT * FROM intercambio.vista_historial_v1;
