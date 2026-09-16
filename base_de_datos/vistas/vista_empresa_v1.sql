-- Vista de empresa del contrato v1 (ámbito vehiculos.empresa.lectura).
-- Fuente: periodos de implementación + empresa implementadora.
-- Expone autorización operativa. Excluye por construcción: nit, direcciones,
-- teléfonos, correo y todo dato de representantes.
CREATE SCHEMA IF NOT EXISTS intercambio;

CREATE OR REPLACE VIEW intercambio.vista_empresa_v1 AS
SELECT
    UPPER(REGEXP_REPLACE(b.placa, '[\s-]', '', 'g')) AS placa_norma,
    b.placa AS placa,
    r.codigo_correlativo AS codigo_correlativo,
    r.estado_aprobacion AS estado_aprobacion,
    (r.fecha_baja IS NULL) AS activa,
    e.nombre_empresa AS nombre_empresa,
    e.numero_autorizacion AS numero_autorizacion,
    e.esta_autorizada AS esta_autorizada,
    e.fecha_autorizacion AS fecha_autorizacion
FROM slv_vehiculoimplementacionperiodo AS r
JOIN slv_vehiculobase AS b ON b.id = r.vehiculo_base_id AND b.deleted_at IS NULL
JOIN slv_empresaimplementadora AS e ON e.id = r.empresa_implementadora_id AND e.deleted_at IS NULL
WHERE r.deleted_at IS NULL;

-- Alias sin versión: la API lee el alias; la v1 conserva el contrato.
CREATE OR REPLACE VIEW intercambio.vista_empresa AS
SELECT * FROM intercambio.vista_empresa_v1;
