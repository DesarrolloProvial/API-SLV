-- Vista de generales del contrato v1: caracterización operativa sin identificadores
-- restringidos ni vínculos sensibles (ámbito base vehiculos.lectura).
-- Reutiliza el expediente como única fuente para no duplicar reglas de vigencia.
-- Excluye por construcción todo lo que el expediente ya excluye; además omite
-- aquí vin, tarjeta_circulacion, refrendo, propietario y empresa (van por sus
-- vistas y ámbitos propios).
CREATE SCHEMA IF NOT EXISTS intercambio;

CREATE OR REPLACE VIEW intercambio.vista_generales_v1 AS
SELECT
    placa_norma,
    placa,
    chasis,
    marca,
    linea,
    modelo,
    serie,
    tipo_placa,
    clasificacion,
    tipo_vehiculo,
    uso,
    color,
    departamento,
    municipio,
    motor,
    asientos,
    ejes,
    cilindraje,
    centimetros_cubicos,
    toneladas,
    codigo_correlativo,
    estado_aprobacion,
    activa
FROM intercambio.vista_expediente_v1;

-- Alias sin versión: la API lee el alias; la v1 conserva el contrato.
CREATE OR REPLACE VIEW intercambio.vista_generales AS
SELECT * FROM intercambio.vista_generales_v1;
