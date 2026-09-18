# Orden de aplicación de las migraciones del espejo

> Prerrequisito de esquema (una vez, antes del paso 2): el espejo nace vacío
> y `copy_data` NO crea tablas (solo copia datos en tablas existentes).
> 1. `CREATE EXTENSION IF NOT EXISTS btree_gist;` como superusuario del
>    espejo. Sin ella fallan las 3 restricciones EXCLUDE de no-solape
>    (`excl_*_no_solape_por_vehiculo`, GiST sobre bigint).
> 2. Volcado solo-esquema de las 18 tablas publicadas desde el ERP con el rol
>    réplica (`pg_dump -O -x --schema-only -t <las 18>`) y restaurarlo en el
>    espejo. Las FK hacia tablas fuera de las 18 fallan y se ignoran
>    (esperado: el espejo nunca lleva usuarios ni tablas fuera de publicación).

1. `0001_roles.sql` como superusuario del espejo (crea esquema, roles y revokes).
2. Ventana del ERP + suscripción (`despliegue/manual_espejo.md` §3–§5): las
   tablas deben existir antes de los pasos 3 y 4.
3. `0002_indices.sql` como propietario de las tablas tras el snapshot inicial
   (`CONCURRENTLY`, fuera de transacción).
4. `vistas/*.sql` como migrador; `vista_expediente_v1.sql` antes que
   `vista_generales_v1.sql` (generales lee el expediente).
5. `0003_concesiones.sql` tras las vistas; re-ejecutar en cada cambio de vistas.

Verificación: `\dv intercambio.*`, privilegios con `has_table_privilege` y
`python manage.py test pruebas.privilegios` con `URL_ESPEJO_PRUEBAS` definida.
