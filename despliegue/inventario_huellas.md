# Inventario de huellas (plantilla sin secretos)

> Plantilla viva: SIN secretos ni llaves, solo huellas públicas SHA-256.
> Cierra el concepto "inventario de huellas" de la tarea 0.2: cada rotación
> actualiza esta tabla y el procedimiento de abajo.

## Tabla

| Servicio | CN/SAN | Huella SHA-256 | Emitido | Expira | Estado |
|---|---|---|---|---|---|
| `postgres-espejo` (servidor) | `<ESPEJO_INTERNO>` | `<HUELLA>` | `<AAAA-MM-DD>` | `<AAAA-MM-DD>` | vigente |
| `api` (cliente PG) | `<USUARIO_LECTOR>` | `<HUELLA>` | `<AAAA-MM-DD>` | `<AAAA-MM-DD>` | vigente |
| `nginx` (servidor) | `<NGINX_INTERNO>` | `<HUELLA>` | `<AAAA-MM-DD>` | `<AAAA-MM-DD>` | vigente |
| `api` (servidor) | `<API_INTERNA>` | `<HUELLA>` | `<AAAA-MM-DD>` | `<AAAA-MM-DD>` | vigente |
| `keycloak` (servidor) | `<IDP_INTERNO>` | `<HUELLA>` | `<AAAA-MM-DD>` | `<AAAA-MM-DD>` | vigente |
| intermedia CA | `<PKI_INTERNA>` intermedia | `<HUELLA>` | `<AAAA-MM-DD>` | `<AAAA-MM-DD>` | vigente |

Obtener una huella (sin exponer la llave):

```sh
step certificate fingerprint <RUTA_CRT>
openssl x509 -in <RUTA_CRT> -noout -sha256 -fingerprint
```

## Procedimiento tras cada rotación

1. Emitir la hoja nueva (doble validez con la vigente, ver
   `despliegue/manual_pki.md` §4) y anotar su huella con estado
   `nueva (doble validez)`.
2. Conmutar clientes a la hoja nueva y verificar (`openssl s_client` /
   `step certificate inspect` según el servicio).
3. Retirar la hoja vieja: cambiar su estado a `retirada` (no borrar la
   fila; el historial queda para auditoría).
4. Ante revocación: estado `revocada` + fecha + referencia al registro del
   incidente (sin secretos).
5. Ante rotación de intermedia: actualizar la fila de intermedia y TODAS
   las hojas reemitidas en el mismo cambio.
6. Verificación: `HUELLA_CA_INTERMEDIA` del ambiente coincide con la fila
   vigente de intermedia; ninguna hoja vigente está expirada.
