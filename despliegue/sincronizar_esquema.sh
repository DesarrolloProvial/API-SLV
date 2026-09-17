#!/bin/sh
# Deriva de esquema ERP -> espejo (SOLO aditivo).
# Lo ejecuta el servicio `deriva-esquema` cada 15 min (cron) y al arrancar.
# - Agrega columnas que falten en el espejo (nullable, sin default).
# - JAMAS borra ni modifica: sobrantes y tipos distintos solo se AVISAN.
# - Si agrego columnas, imprime el one-liner de backfill historico (manual,
#   una vez). Sin secretos literales: todo llega por environment.
set -u
: "${PGPASSWORD_REPLICA:?falta env PGPASSWORD_REPLICA (clave del rol replica en el ERP)}"
: "${PGPASSWORD_ADMIN:?falta env PGPASSWORD_ADMIN (clave admin del espejo)}"
: "${NOMBRE_BD:?falta env NOMBRE_BD}"
: "${USUARIO_ADMIN_BD:?falta env USUARIO_ADMIN_BD}"
ERP="host=erp_postgres port=5432 dbname=ERP_UTIPRV user=rol_replicacion_intercambio"
ESP="host=postgres-espejo port=5432 dbname=$NOMBRE_BD user=$USUARIO_ADMIN_BD"
TABLAS="slv_vehiculobase slv_vehiculoimplementacionperiodo slv_vehiculotitularidadperiodo slv_vehiculoadministrativoversion slv_historialrefrendovehiculo slv_empresaimplementada slv_empresaimplementadora slv_dispositivocatalogo slv_clasificacionvehiculo slv_tipovehiculo slv_usovehiculo slv_marcavehiculo slv_departamento slv_municipio slv_eventoimplementacion slv_vehiculoevento slv_cuposolicitudvehiculo slv_documentoexpediente"
Q="SELECT a.attname, format_type(a.atttypid,a.atttypmod) FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname='%s' AND a.attnum>0 AND NOT a.attisdropped ORDER BY 1;"
AGREGADAS=0; AVISOS=0; FALLOS=0
for T in $TABLAS; do
  if ! PGPASSWORD="$PGPASSWORD_REPLICA" psql "$ERP" -tA -F'|' -c "$(printf "$Q" "$T")" > /tmp/c_erp.txt 2>/tmp/e_erp.txt; then
    echo "deriva [$T] ERROR leyendo ERP (se omite)"; FALLOS=$((FALLOS+1)); continue
  fi
  if ! PGPASSWORD="$PGPASSWORD_ADMIN" psql "$ESP" -tA -F'|' -c "$(printf "$Q" "$T")" > /tmp/c_esp.txt 2>/tmp/e_esp.txt; then
    echo "deriva [$T] ERROR leyendo espejo (se omite)"; FALLOS=$((FALLOS+1)); continue
  fi
  if [ ! -s /tmp/c_erp.txt ]; then
    echo "deriva [$T] sin columnas en ERP (raro, se omite)"; FALLOS=$((FALLOS+1)); continue
  fi
  cut -d'|' -f1 /tmp/c_erp.txt | sort > /tmp/n_erp.txt
  cut -d'|' -f1 /tmp/c_esp.txt | sort > /tmp/n_esp.txt
  comm -23 /tmp/n_erp.txt /tmp/n_esp.txt > /tmp/faltan.txt
  if [ -s /tmp/faltan.txt ]; then
    while read -r C; do
      TIPO=$(awk -F'|' -v c="$C" '$1==c{print $2}' /tmp/c_erp.txt)
      if PGPASSWORD="$PGPASSWORD_ADMIN" psql "$ESP" -c "ALTER TABLE public.$T ADD COLUMN \"$C\" $TIPO;"; then
        echo "deriva [$T] agregada $C ($TIPO)"; AGREGADAS=$((AGREGADAS+1))
      else
        echo "deriva [$T] FALLO agregando $C"; FALLOS=$((FALLOS+1))
      fi
    done < /tmp/faltan.txt
  fi
  DIF=$(awk -F'|' 'NR==FNR{e[$1]=$2;next} ($1 in e)&&e[$1]!=$2{print "deriva AVISO tipo distinto: '"$T"'."$1" ERP="$2" espejo="e[$1]}' /tmp/c_esp.txt /tmp/c_erp.txt)
  if [ -n "$DIF" ]; then echo "$DIF"; AVISOS=$((AVISOS+1)); fi
  SOB=$(comm -13 /tmp/n_erp.txt /tmp/n_esp.txt)
  if [ -n "$SOB" ]; then echo "$SOB" | sed "s/^/deriva AVISO sobrante en espejo (no se borra): $T./"; AVISOS=$((AVISOS+1)); fi
done
echo "deriva resumen: agregadas=$AGREGADAS avisos=$AVISOS fallos=$FALLOS"
if [ "$AGREGADAS" -gt 0 ]; then
  echo "deriva BACKFILL historico (una vez, manual, como admin del espejo):"
  echo "  DROP SUBSCRIPTION sub_intercambio;"
  echo "  SELECT pg_drop_replication_slot('slot_intercambio');"
  echo "  CREATE SUBSCRIPTION sub_intercambio CONNECTION 'host=erp_postgres port=5432 dbname=ERP_UTIPRV user=rol_replicacion_intercambio password=<CLAVE_REPLICA>' PUBLICATION pub_intercambio WITH (copy_data = true, create_slot = true, slot_name = 'slot_intercambio');"
fi
