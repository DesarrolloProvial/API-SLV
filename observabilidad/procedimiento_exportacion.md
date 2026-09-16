# Procedimiento de exportacion caliente → frio

Nivel caliente: Loki operativo (30 d base, ajustable por convenio).
Nivel frio: respaldo comprimido NO productivo, consultable bajo demanda.
La purga del caliente ocurre SOLO tras export exitoso al frio.

## 1. Requisitos

- Acceso de lectura al Loki operativo y de escritura al destino frio.
- `logcli` configurado con `URL_LOKI` (por ambiente, nunca en el repo).
- El registro trae `codigo_correlacion` como campo JSON de primer nivel
  (`aplicaciones/auditoria/registrador_consulta.py`): toda reconstruccion
  `FW→GW→API→PG→Loki` se filtra por ese campo, nunca por placa.

## 2. Exportar un rango (diario sugerido, `observabilidad/exportar_frio.sh`)

```bash
URL_LOKI="https://loki-interno:3100" \
DESDE="2026-09-01T00:00:00Z" HASTA="2026-09-02T00:00:00Z" \
DIR_FRIO="/respaldo/intercambio" \
observabilidad/exportar_frio.sh
```

El guion descarga el rango en JSON, lo comprime a `.json.gz` y deja su
`.sha256` al lado. Sin export exitoso (codigo de salida distinto de 0),
NADA se purga.

## 3. Verificar el frio

1. `sha256sum -c <archivo>.sha256` → `correcto`.
2. `zgrep -c codigo_correlacion <archivo>.json.gz` → conteo mayor que 0.
3. `zgrep -o '"codigo_correlacion":"[^"]*"' <archivo>.json.gz | head` →
   muestra codigos reconstruibles.

## 4. Purga condicionada del caliente

Solo si el paso 3 esta en verde, aplicar la retencion del Loki operativo
para el `stream` del intercambio (politica del Loki, no borrado a mano).
Si el export fallo, el caliente se conserva intacto y se reintenta.

## 5. Consulta bajo demanda en el frio

```bash
zgrep -h '<codigo_correlacion>' /respaldo/intercambio/*.json.gz | head
```

Cada linea trae recurso/estado/cliente/volumen/duracion para reconstruir
el caso (entregado, no encontrado, denegado, limitado o error).

## 6. Roles

Ejecuta: operador de turno. Verifica: responsable de datos. Los plazos
finales (caliente/frio) los fija el convenio; este procedimiento no los
inventa, solo los opera.
