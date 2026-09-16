# Manual de resincronización selectiva y anti-drift

> **EJECUCIÓN MANUAL GUIADA — NO AUTOMÁTICA.**
> Todo se opera en el espejo; el ERP no se toca (sigue sirviendo sin
> interrupción). Cada comando lo corre un operador autorizado y verifica
> antes de seguir.

## 1. Cuándo usarlo

- Alerta `TablasFueraDeReplica` o `SuscripcionIntercambioCaida` con una tabla
  detenida (`srsubstate` distinto de `r` en `pg_subscription_rel`).
- Alerta de WAL (`RezagoSlotIntercambioAlto`, `RetencionWALSlotAlta`) cuando la
  causa es una tabla atascada y no un suscriptor caído.
- Tras reconciliar un drift rompiente (§6).

## 2. Precondiciones

- Suscripción `sub_intercambio` existe; publicación del ERP intacta.
- Espacio en disco del espejo para la recopia de la tabla.
- Lecturas de la API: la tabla en recopia responde parcial; si el caso lo
  exige, anunciar degradación antes de empezar.

## 3. Resincronización selectiva (una tabla, sin tocar el ERP)

```sql
-- 1. Estado actual de la tabla (ejemplo: slv_historialrefrendovehiculo).
SELECT srrelid::regclass AS tabla, srsubstate AS estado, srsublsn AS lsn
FROM pg_subscription_rel
WHERE srsubid = (SELECT oid FROM pg_subscription WHERE subname = 'sub_intercambio');
-- estado esperado tras recopia: r (lista). i = inicializando.

-- 2. Soltar solo la copia local (la publicación del ERP no cambia).
DROP TABLE <tabla>;

-- 3. Pedir el snapshot nuevo de la tabla faltante.
ALTER SUBSCRIPTION sub_intercambio REFRESH PUBLICATION WITH (copy_data = true);

-- 4. Vigilar hasta estado r y conteo convergente.
SELECT srrelid::regclass AS tabla, srsubstate AS estado
FROM pg_subscription_rel
WHERE srsubid = (SELECT oid FROM pg_subscription WHERE subname = 'sub_intercambio');
SELECT count(*) FROM <tabla>;
```

Puerta de validación: la semántica exacta de recopia es de PostgreSQL 18;
**validarla en preproducción** con una tabla de prueba antes de usarla en
producción. Si la tabla no pasa a `i` ni se recopia, usar el §4.

## 4. Reserva: recrear la suscripción (ventana de mantenimiento)

```sql
DROP SUBSCRIPTION sub_intercambio;
CREATE SUBSCRIPTION sub_intercambio
    CONNECTION 'host=<ANFITRION_ERP> port=<PUERTO_ERP> dbname=<NOMBRE_BD_ERP>
        user=rol_replicacion_intercambio password=<CLAVE_REPLICA_ERP>'
    PUBLICATION pub_intercambio
    WITH (copy_data = true, create_slot = true, slot_name = 'slot_intercambio');
```

Luego re-aplicar índices y concesiones
(`base_de_datos/migraciones_espejo/orden_aplicacion.md` pasos 3–5).

## 5. Verificación (siempre)

- `pg_subscription_rel`: todas las tablas en `r`.
- Conteos espejo contra primario (comparación manual de dos `count(*)`
  y de `max(id)` por tabla).
- Columnas del contrato: `\d intercambio.vista_*` sin columnas de más.
- `python manage.py test pruebas.privilegios` con `URL_ESPEJO_PRUEBAS`.
- Registrar el incidente (§7).

## 6. Anti-drift (DDL en el origen sin romper el contrato)

1. **Detectar**: errores del worker de suscripción + comparación de esquema
   origen contra espejo (columnas por tabla, semanal o ante alerta).
2. **Clasificar**: aditivo (columna/tabla nueva, nada se elimina) o rompiente
   (renombre, cambio de tipo, eliminación).
3. **Bloquear**: no desplegar vistas hasta reconciliar; la API sigue sirviendo
   el contrato vigente con los datos replicados.
4. **Migrar o conservar**: aditivo → nueva versión de vista solo si el
   convenio lo autoriza (Anexo C); rompiente → conservar la columna del
   contrato (anulable o por defecto) y no tocar lo externo.
5. **Resincronizar** la tabla afectada (§3) y **verificar** (§5).
6. El retiro de un campo solo por Anexo C con doble vigencia.

## 7. Registro del incidente

Fecha, tabla, síntoma y alerta, clasificación (aditivo/rompiente), pasos
ejecutados (§3 o §4), verificación (§5) y responsable. Vive con el parte
operativo del turno; lo esencial queda en el historial del repo.
