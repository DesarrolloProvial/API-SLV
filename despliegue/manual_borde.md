# Manual del borde (tunel + WAF + nginx)

## 1. Crear el tunel

1. En el panel Cloudflare: `Zero Trust > Networks > Tunnels > Create`.
2. Nombre: `intercambio-dgt`; instala `cloudflared` en el anfitrion.
3. `Public Hostnames > Add`: subdominio `intercambio.provial.gob.gt`
   (confirmar en fase 0) hacia `http://nginx:80`.
4. Guarda el identificador en el gestor externo como `TUNEL_ID`
   (nunca en el repo ni en la imagen).

## 2. Certificados de cliente (CA gestionada)

1. `SSL > Client Certificates`: crea la CA gestionada del hostname.
2. Asocia la CA solo a `intercambio.provial.gob.gt`.
3. Emite un certificado por institucion (`dgt-intercambio`); sin compartidos.
4. Revoca desde este mismo panel ante incidente (paso 2 del kill-switch).

## 3. Reglas WAF (5 del plan free)

| Regla | Condicion | Accion |
|-------|-----------|--------|
| R1 | Hostname del intercambio Y certificado de cliente invalido/ausente | Bloquear |
| R2 | Metodo distinto de `GET` O ruta fuera de `/api/v1/vehiculos/*` | Bloquear |
| R3 | Reserva: refuerzo por IP si la DGT confirma egress fijo | Omitir o bloquear |
| R4 | Reserva: puntuacion de bot alta | Bloquear |
| R5 | Reserva: respuesta uniforme de bloqueo | Responder |

## 4. Limite de ritmo sobre `buscar`

1. `Security > Rate Limiting > Create rule`: solo
   `GET intercambio.provial.gob.gt/api/v1/vehiculos/buscar`.
2. Tope inicial a calibrar en convenio; respuesta `429` con `Retry-After`.
3. `nginx` aplica su propio `limit_req` como segunda capa.

## 5. Lista de verificacion de despliegue (no ejecutar aqui)

- [ ] Sin certificado → bloqueo en borde con error uniforme y correlacion.
- [ ] Certificado revocado/expirado → bloqueo sin llegar a la API.
- [ ] `POST` o ruta fuera de allowlist → denegado y registrado sin personales.
- [ ] `/salud` y `/metricas` solo responden en red interna.
- [ ] Registro JSON sin `Authorization`, secretos ni placas.
