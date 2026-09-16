# Orden de aplicación de las migraciones del espejo

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
