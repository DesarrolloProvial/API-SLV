-- 02: configuracion WAL para replicacion logica (lado ERP).
--
-- Proposito: dejar el primario listo para publicar (wal_level=logical y
-- emisores/slots de reserva). Version ejecutable de
-- `despliegue/manual_espejo.md` §2.
--
-- Prerequisitos: superusuario del ERP; ventana de reinicio agendada y
-- comunicada; respaldo reciente verificado. Sin variables psql.
--
-- Como ejecutarlo (conectado como administrador, cualquier BD):
--   psql "host=<ANFITRION_ERP> dbname=postgres user=<ADMIN_ERP>" -f 02_configuracion_wal.sql
-- Nota de uso por pegado: el archivo no recibe parametros; puede pegarse
-- tal cual en psql interactivo.
--
-- ATENCION — REQUIERE REINICIAR EL SERVICIO POSTGRES DEL ERP (ventana):
-- ALTER SYSTEM solo escribe `postgresql.auto.conf`; los valores nuevos
-- rigen tras reiniciar. Como verificarlo despues: `SHOW wal_level;` debe
-- decir `logical` y `pending_restart` debe ser f en la consulta de abajo.
-- Revertir exige OTRA ventana; por eso el monitoreo del slot es dia 0
-- (`observabilidad/reglas_alertas.yaml`).
--
-- Salida esperada antes del reinicio: wal_level=logical con
-- pending_restart=t; despues del reinicio: lo mismo con pending_restart=f.

ALTER SYSTEM SET wal_level = 'logical';
ALTER SYSTEM SET max_wal_senders = 5;
ALTER SYSTEM SET max_replication_slots = 5;
ALTER SYSTEM SET max_slot_wal_keep_size = '10GB'; -- partida interna, calibrar en convenio

-- Verificacion embebida: valor actual, valor pendiente y si falta reinicio.
SHOW wal_level; -- hoy: replica; tras reiniciar: logical
SELECT name, setting, pending_restart FROM pg_settings
WHERE name IN ('wal_level', 'max_wal_senders', 'max_replication_slots', 'max_slot_wal_keep_size')
ORDER BY 1;
