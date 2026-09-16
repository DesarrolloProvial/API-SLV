-- Vista de expediente del contrato v1: ficha acotada por placa exacta.
-- Fuentes replicadas: base, periodos de implementación y titularidad, versión
-- administrativa vigente, último refrendo, empresas y catálogos (nombres exactos
-- del diseño §2; las tablas llegan por replicación).
-- «activa» se calcula como (fecha_baja IS NULL); el refrendo vigente sigue la
-- regla de la vista interna del ERP (último por fecha_refrendo).
-- Columnas restringidas (la API las filtra por ámbito): vin, tarjeta_circulacion.
-- Excluye por construcción: CUI, teléfonos, correo, domicilio, póliza,
-- licencias, registro_dgt, observación/motivo, snapshots con nit, datos_extra,
-- rutas, sha256 y secretos.
-- Pendiente de convenio (no incluir hasta firma): direccion operativa,
-- nit parcial, nombre_propietario, numero_registro, folio de cupo y tríada
-- documental (tipo+estado+fecha).
CREATE SCHEMA IF NOT EXISTS intercambio;

CREATE OR REPLACE VIEW intercambio.vista_expediente_v1 AS
SELECT
    UPPER(REGEXP_REPLACE(b.placa, '[\s-]', '', 'g')) AS placa_norma,
    b.placa AS placa,
    b.chasis AS chasis,
    b.vin AS vin,
    adm.numero_tarjeta_circulacion AS tarjeta_circulacion,
    marca.nombre AS marca,
    adm.linea AS linea,
    adm.modelo AS modelo,
    adm.serie AS serie,
    adm.tipo_placa AS tipo_placa,
    clas.nombre AS clasificacion,
    tipo.nombre AS tipo_vehiculo,
    uso.nombre AS uso,
    adm.color AS color,
    depto.nombre AS departamento,
    muni.nombre AS municipio,
    adm.motor AS motor,
    adm.asientos AS asientos,
    adm.ejes AS ejes,
    adm.cilindraje AS cilindraje,
    adm.centimetros_cubicos AS centimetros_cubicos,
    adm.toneladas AS toneladas,
    r.codigo_correlativo AS codigo_correlativo,
    r.estado_aprobacion AS estado_aprobacion,
    (r.fecha_baja IS NULL) AS activa,
    r.fecha_codigo_correlativo AS fecha_codigo,
    tiposlv.codigo AS tipo_slv_codigo,
    tiposlv.nombre AS tipo_slv_nombre,
    f.codigo_refrendo AS refrendo_codigo,
    f.fecha_refrendo AS refrendo_fecha,
    f.fecha_vencimiento AS refrendo_vencimiento,
    f.estado AS refrendo_estado,
    m.nombre_empresa AS propietario_nombre,
    e.nombre_empresa AS empresa_nombre,
    e.numero_autorizacion AS empresa_autorizacion,
    e.esta_autorizada AS empresa_esta_autorizada
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
LEFT JOIN LATERAL (
    SELECT t1.*
    FROM slv_vehiculotitularidadperiodo AS t1
    WHERE t1.vehiculo_base_id = b.id AND t1.deleted_at IS NULL
        AND (t1.vigente_hasta IS NULL OR t1.vigente_hasta >= CURRENT_DATE)
    ORDER BY t1.vigente_desde DESC, t1.id DESC
    LIMIT 1
) AS t ON TRUE
LEFT JOIN LATERAL (
    SELECT f1.codigo_refrendo, f1.fecha_refrendo, f1.fecha_vencimiento, f1.estado
    FROM slv_historialrefrendovehiculo AS f1
    WHERE f1.relacion_vehiculo_id = r.id AND f1.deleted_at IS NULL
    ORDER BY f1.fecha_refrendo DESC, f1.id DESC
    LIMIT 1
) AS f ON TRUE
LEFT JOIN slv_empresaimplementadora AS e
    ON e.id = r.empresa_implementadora_id AND e.deleted_at IS NULL
LEFT JOIN slv_empresaimplementada AS m
    ON m.id = t.empresa_implementada_id AND m.deleted_at IS NULL
LEFT JOIN slv_dispositivocatalogo AS tiposlv ON tiposlv.id = r.tipo_slv_id
LEFT JOIN slv_marcavehiculo AS marca ON marca.id = adm.marca_id
LEFT JOIN slv_clasificacionvehiculo AS clas ON clas.id = adm.clasificacion_id
LEFT JOIN slv_tipovehiculo AS tipo ON tipo.id = adm.tipo_vehiculo_id
LEFT JOIN slv_usovehiculo AS uso ON uso.id = adm.uso_id
LEFT JOIN slv_departamento AS depto ON depto.id = adm.departamento_id
LEFT JOIN slv_municipio AS muni ON muni.id = adm.municipio_id
WHERE b.deleted_at IS NULL;

-- Alias sin versión: la API lee el alias; la v1 conserva el contrato.
CREATE OR REPLACE VIEW intercambio.vista_expediente AS
SELECT * FROM intercambio.vista_expediente_v1;
