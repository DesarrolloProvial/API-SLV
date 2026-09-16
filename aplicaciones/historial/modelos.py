"""Modelos de solo lectura del contexto historial (tarea 3.3).

Lee solo `intercambio.vista_historial`. Columnas tomadas de
`base_de_datos/vistas/vista_historial_v1.sql`; no inventar columnas.
Varias filas por placa (periodos vigentes y dados de baja); el selector
pagina con orden determinista. `placa_norma` es solo llave de mapeo ORM.

Diferimiento documentado (compuerta PR5): ver `propietario/modelos.py`
(`.values()` sin identidad ORM; `CompositePrimaryKey` solo si se
instanciaran modelos).
"""
from django.db import models


class VistaHistorial(models.Model):
    """Periodo de implementacion por placa (paginado con cursor opaco)."""

    placa_norma = models.TextField(primary_key=True)
    placa = models.TextField(null=True)
    codigo_correlativo = models.TextField(null=True)
    estado_aprobacion = models.TextField(null=True)
    activa = models.BooleanField(null=True)
    vigente_desde = models.DateField(null=True)
    fecha_baja = models.DateField(null=True)
    motivo_baja_codigo = models.TextField(null=True)
    empresa_implementadora = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'intercambio"."vista_historial'
