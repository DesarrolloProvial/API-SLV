# API de intercambio de vehiculos

API de solo lectura para consulta de vehiculos entre PROVIAL y DGT.
Repo e infra dedicados; este servicio solo lee el espejo dia 0.

## Estructura

- `configuracion/`: ajustes por entorno y enrutado principal.
- `aplicaciones/`: un paquete por contexto (vehiculos, propietario, empresa,
  refrendos, historial, seguridad, auditoria).
- `base_de_datos/`: migraciones del espejo y vistas `*_v1`.
- `contratos/`: OpenAPI generado e instantaneas del Anexo C.
- `pruebas/`: unidad, contrato y privilegios.
- `despliegue/`: composicion de desarrollo, ambiente ejemplo y contenedor.
- `observabilidad/`: tablero, alertas y exportacion (fase 4).

## Desarrollo local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python manage.py check
python manage.py test
```

Sin secretos en el repo: copia `despliegue/archivo_ambiente_ejemplo`
a `.env` y completa los valores solo en tu maquina.
