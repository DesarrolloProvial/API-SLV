-- Suscripcion del espejo hacia el ERP (snapshot inicial incluido).
--
-- Proposito: crear `sub_intercambio` contra `pub_intercambio` del ERP con
-- copia inicial (copy_data) y slot dedicado, y verificar que el flujo quedo
-- activo. Version ejecutable de `despliegue/manual_espejo.md` §5.
--
-- Prerequisitos: ventana del ERP completa y verificada (04 en verde);
-- conectividad espejo→ERP probada (ver `despliegue/manual_recuperacion.md`
-- §checklist, sin eso la suscripcion no levanta); tablas del intercambio
-- AUN NO existentes en el espejo (copy_data las crea); superusuario del
-- espejo en la BD espejo.
--
-- Como ejecutarlo (la cadena se arma con los valores del gestor; nunca se
-- guarda en el repo ni en el historial en claro):
--   psql "host=<ESPEJO> dbname=<BD_ESPEJO> user=<ADMIN_ESPEJO>" -v cadena_conexion="host=<ANFITRION_ERP> port=<PUERTO_ERP> dbname=<NOMBRE_BD_ERP> user=rol_replicacion_intercambio password=<CLAVE_REPLICA_ERP>" -f suscripcion.sql
-- Nota de uso por pegado: sustituya :'cadena_conexion' por la cadena literal
-- entre comillas simples. Los nombres fijos (sub_intercambio,
-- pub_intercambio, slot_intercambio) coinciden con PUBLICACION_INTERCAMBIO y
-- SLOT_INTERCAMBIO de `despliegue/archivo_ambiente_ejemplo`.
--
-- Idempotente: si `sub_intercambio` ya existe, avisa y no hace nada (CREATE
-- SUBSCRIPTION no admite IF NOT EXISTS ni correr dentro de bloque, por eso
-- la sentencia se genera condicionalmente con \gexec; requiere psql con
-- \gexec, disponible desde PostgreSQL 9.6).
--
-- Salida esperada: aviso de existencia previa, o CREATE SUBSCRIPTION; luego
-- una fila activa en pg_stat_subscription y el conteo del espejo
-- convergiendo con el del ERP (04) con rezago acotado.
-- Siguiente paso: `base_de_datos/migraciones_espejo/orden_aplicacion.md`
-- (indices → vistas → concesiones) y pruebas gated con URL_ESPEJO_PRUEBAS.

SELECT CASE
    WHEN EXISTS (SELECT 1 FROM pg_subscription WHERE subname = 'sub_intercambio')
    THEN $$SELECT 'sub_intercambio ya existe: no se hace nada (idempotente)' AS aviso$$
    ELSE $$CREATE SUBSCRIPTION sub_intercambio CONNECTION $$ || :'cadena_conexion' || $$ PUBLICATION pub_intercambio WITH (copy_data = true, create_slot = true, slot_name = 'slot_intercambio')$$
END \gexec

-- Verificacion embebida: una fila activa (subname=sub_intercambio).
TABLE pg_stat_subscription;
-- Conteo local: comparar a mano con filas_vehiculobase_erp del 04.
SELECT count(*) AS filas_vehiculobase_espejo FROM slv_vehiculobase;
