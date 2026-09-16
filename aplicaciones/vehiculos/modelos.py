"""Modelos de solo lectura sobre las vistas del contrato v1.

La API nunca toca tablas base: cada modelo es `managed=False` sobre el
alias sin version (`intercambio.vista_*`); la `*_v1` conserva el contrato.
Columnas tomadas de `base_de_datos/vistas/vista_*_v1.sql` (verificadas
contra el ERP); no inventar columnas aqui.
"""
from django.db import models


class VistaBusqueda(models.Model):
    """Candidata de busqueda por sufijo (vista_busqueda)."""

    placa_norma = models.TextField(primary_key=True)
    placa_sufijo6 = models.CharField(max_length=6)
    tipo = models.CharField(max_length=15)
    activa = models.BooleanField()
    placa = models.TextField(null=True)
    chasis = models.TextField(null=True)
    codigo_correlativo = models.TextField(null=True)
    estado_aprobacion = models.TextField(null=True)
    empresa_implementadora = models.TextField(null=True)
    marca = models.TextField(null=True)
    linea = models.TextField(null=True)
    modelo = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'intercambio"."vista_busqueda'


class VistaExpediente(models.Model):
    """Ficha acotada por placa exacta (vista_expediente; base de generales)."""

    placa_norma = models.TextField(primary_key=True)
    placa = models.TextField(null=True)
    chasis = models.TextField(null=True)
    # Restringidas por ambito: mapeadas por fidelidad al SQL, jamas expuestas
    # en respuestas hasta la tarea 3.4 (el armador las excluye por defecto).
    vin = models.TextField(null=True)
    tarjeta_circulacion = models.TextField(null=True)
    marca = models.TextField(null=True)
    linea = models.TextField(null=True)
    modelo = models.TextField(null=True)
    serie = models.TextField(null=True)
    tipo_placa = models.CharField(max_length=15, null=True)
    clasificacion = models.TextField(null=True)
    tipo_vehiculo = models.TextField(null=True)
    uso = models.TextField(null=True)
    color = models.TextField(null=True)
    departamento = models.TextField(null=True)
    municipio = models.TextField(null=True)
    motor = models.TextField(null=True)
    asientos = models.IntegerField(null=True)
    ejes = models.IntegerField(null=True)
    cilindraje = models.FloatField(null=True)
    centimetros_cubicos = models.FloatField(null=True)
    toneladas = models.FloatField(null=True)
    codigo_correlativo = models.TextField(null=True)
    estado_aprobacion = models.TextField(null=True)
    activa = models.BooleanField()
    fecha_codigo = models.DateField(null=True)
    tipo_slv_codigo = models.TextField(null=True)
    tipo_slv_nombre = models.TextField(null=True)
    refrendo_codigo = models.TextField(null=True)
    refrendo_fecha = models.DateField(null=True)
    refrendo_vencimiento = models.DateField(null=True)
    refrendo_estado = models.TextField(null=True)
    propietario_nombre = models.TextField(null=True)
    empresa_nombre = models.TextField(null=True)
    empresa_autorizacion = models.TextField(null=True)
    empresa_esta_autorizada = models.BooleanField(null=True)

    class Meta:
        managed = False
        db_table = 'intercambio"."vista_expediente'
