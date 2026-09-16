#!/usr/bin/env bash
# Exporta el rango caliente del intercambio a frio comprimido.
# Falla sin exportar si algo sale mal: sin exito aqui, nada se purga.
set -euo pipefail

: "${URL_LOKI:?defina URL_LOKI del Loki operativo}"
: "${DESDE:?defina DESDE en RFC3339 (p. ej. 2026-09-01T00:00:00Z)}"
: "${HASTA:?defina HASTA en RFC3339 (p. ej. 2026-09-02T00:00:00Z)}"
: "${DIR_FRIO:?defina DIR_FRIO (destino NO productivo)}"
ETIQUETAS="${ETIQUETAS:-{origen=\"intercambio.consulta\"}}"

mkdir -p "$DIR_FRIO"
BASE="intercambio-${DESDE//:/-}-${HASTA//:/-}"
SALIDA="$DIR_FRIO/$BASE.json"

logcli query-range --addr="$URL_LOKI" --from="$DESDE" --to="$HASTA" \
  "$ETIQUETAS" --output=jsonl > "$SALIDA"
gzip -f "$SALIDA"
sha256sum "$SALIDA.gz" > "$SALIDA.gz.sha256"
echo "Frio listo: $SALIDA.gz"
