-- Vista de búsqueda del contrato v1: candidatas por placa normalizada.
-- Fuentes replicadas: slv_vehiculobase, slv_vehiculoimplementacionperiodo,
-- slv_vehiculoadministrativoversion, slv_empresaimplementadora.
-- Convenciones verificadas en el ERP: FK como <campo>_id; catálogos con
-- codigo+nombre; «activa» es propiedad (fecha_baja IS NULL) y se calcula aquí.
-- Excluye por construcción: CUI, contactos, póliza, licencias,
-- observación/motivo, datos_extra, rutas, sha256 y secretos (no están en el SELECT).
-- Pendiente de convenio (no incluir hasta firma): nit parcial,
-- nombre_propietario, numero_registro, direccion operativa y vin en la búsqueda.
CREATE SCHEMA IF NOT EXISTS intercambio;

CREATE OR REPLACE VIEW intercambio.vista_busqueda_v1 AS
SELECT
    UPPER(REGEXP_REPLACE(b.placa, '[\s-]', '', 'g')) AS placa_norma,
    RIGHT(UPPER(REGEXP_REPLACE(b.placa, '[\s-]', '', 'g')), 6) AS placa_sufijo6,
    COALESCE(adm.tipo_placa, 'guatemalteca') AS tipo,
    (r.fecha_baja IS NULL) AS activa,
    b.placa AS placa,
    b.chasis AS chasis,
    r.codigo_correlativo AS codigo_correlativo,
    r.estado_aprobacion AS estado_aprobacion,
    e.nombre_empresa AS empresa_implementadora,
    marca.nombre AS marca,
    adm.linea AS linea,
    adm.modelo AS modelo
FROM slv_vehiculobase AS b
LEFT JOIN LATERAL (
    SELECT r1.*
    FROM slv_vehiculoimplementacionperiodo AS r1
    WHERE r1.vehiculo_base_id = b.id AND r1.deleted_at IS NULL
    ORDER BY (r1.fecha_baja IS NULL) DESC, r1.fecha_inicio DESC, r1.id DESC
    LIMIT 1
) AS r ON TRUE
LEFT JOIN LATERAL (
    SELECT a1.*
    FROM slv_vehiculoadministrativoversion AS a1
    WHERE a1.vehiculo_base_id = b.id AND a1.deleted_at IS NULL
        AND (a1.vigente_hasta IS NULL OR a1.vigente_hasta >= CURRENT_DATE)
    ORDER BY a1.vigente_desde DESC, a1.id DESC
    LIMIT 1
) AS adm ON TRUE
LEFT JOIN slv_empresaimplementadora AS e
    ON e.id = r.empresa_implementadora_id AND e.deleted_at IS NULL
LEFT JOIN slv_marcavehiculo AS marca ON marca.id = adm.marca_id
WHERE b.deleted_at IS NULL;

-- Alias sin versión: la API lee el alias; la v1 conserva el contrato.
CREATE OR REPLACE VIEW intercambio.vista_busqueda AS
SELECT * FROM intercambio.vista_busqueda_v1;
