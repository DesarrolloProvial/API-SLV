-- Vista de propietario del contrato v1 (ámbito vehiculos.propietario.lectura).
-- Fuente: titularidad vigente (vigente_hasta nulo o futuro) + empresa implementada.
-- Expone solo identidad jurídica mínima. Excluye por construcción: cui,
-- teléfonos, correo_electronico, domicilio, fecha_nacimiento y observación.
-- Pendiente de convenio (no incluir hasta firma):
-- m.numero_registro AS numero_registro,
-- m.nit AS nit_parcial,
-- m.nombre_propietario AS nombre_propietario,
CREATE SCHEMA IF NOT EXISTS intercambio;

CREATE OR REPLACE VIEW intercambio.vista_propietario_v1 AS
SELECT
    UPPER(REGEXP_REPLACE(b.placa, '[\s-]', '', 'g')) AS placa_norma,
    b.placa AS placa,
    t.vigente_desde AS vigente_desde,
    t.vigente_hasta AS vigente_hasta,
    m.nombre_empresa AS nombre_empresa
FROM slv_vehiculotitularidadperiodo AS t
JOIN slv_vehiculobase AS b ON b.id = t.vehiculo_base_id AND b.deleted_at IS NULL
JOIN slv_empresaimplementada AS m ON m.id = t.empresa_implementada_id AND m.deleted_at IS NULL
WHERE t.deleted_at IS NULL;

-- Alias sin versión: la API lee el alias; la v1 conserva el contrato.
CREATE OR REPLACE VIEW intercambio.vista_propietario AS
SELECT * FROM intercambio.vista_propietario_v1;
