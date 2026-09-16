"""Esquemas de expediente y generales (tarea 3.2)."""
from datetime import date

from ninja import Schema


class EsquemaVehiculo(Schema):
    """Caracterizacion operativa (sin `vin` ni tarjeta: restringidos)."""

    chasis: str | None = None
    marca: str | None = None
    linea: str | None = None
    modelo: str | None = None
    serie: str | None = None
    tipo_placa: str | None = None
    clasificacion: str | None = None
    tipo_vehiculo: str | None = None
    uso: str | None = None
    color: str | None = None
    departamento: str | None = None
    municipio: str | None = None
    motor: str | None = None
    asientos: int | None = None
    ejes: int | None = None
    cilindraje: float | None = None
    centimetros_cubicos: float | None = None
    toneladas: float | None = None
    codigo_correlativo: str | None = None
    estado_aprobacion: str | None = None
    activa: bool | None = None
    fecha_codigo: date | None = None
    tipo_slv_codigo: str | None = None
    tipo_slv_nombre: str | None = None


class EsquemaVinculacion(Schema):
    """Vinculacion vigente con propietario y empresa."""

    propietario_nombre: str | None = None
    empresa_nombre: str | None = None
    empresa_autorizacion: str | None = None
    empresa_esta_autorizada: bool | None = None


class EsquemaRefrendoVigente(Schema):
    """Ultimo refrendo por fecha (None si no hay vigente)."""

    codigo: str | None = None
    fecha: date | None = None
    vencimiento: date | None = None
    estado: str | None = None


class EsquemaVinculos(Schema):
    """Lo implementado hasta 3.3 (el candado por ambitos llega en 3.4)."""

    expediente: str
    generales: str
    propietario: str
    empresa: str
    refrendos: str
    historial: str


class EsquemaExpediente(Schema):
    """Respuesta 200 de expediente por placa exacta."""

    codigo_correlacion: str
    placa: str
    vehiculo: EsquemaVehiculo
    vinculacion: EsquemaVinculacion
    refrendo_vigente: EsquemaRefrendoVigente | None = None
    vinculos: EsquemaVinculos


class EsquemaGenerales(Schema):
    """Respuesta 200 de generales (subconjunto sin restringidos)."""

    codigo_correlacion: str
    placa: str
    generales: EsquemaVehiculo
    vinculos: EsquemaVinculos
