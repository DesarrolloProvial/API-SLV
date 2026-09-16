"""Modelos de solo lectura del contexto refrendos (tarea 3.3).

Lee solo `intercambio.vista_refrendos`. Columnas tomadas de
`base_de_datos/vistas/vista_refrendos_v1.sql`; no inventar columnas.
Varias filas por placa; el selector pagina con orden determinista.
`placa_norma` es solo llave de mapeo ORM.

Diferimiento documentado (compuerta PR5): ver `propietario/modelos.py`
(`.values()` sin identidad ORM; `CompositePrimaryKey` solo si se
instanciaran modelos).
"""
from django.db import models


class VistaRefrendo(models.Model):
    """Refrendo por placa (el selector pagina con cursor opaco)."""

    placa_norma = models.TextField(primary_key=True)
    placa = models.TextField(null=True)
    codigo_refrendo = models.TextField(null=True)
    fecha_refrendo = models.DateField(null=True)
    fecha_vencimiento = models.DateField(null=True)
    estado = models.TextField(null=True)
    vigencia_anios = models.IntegerField(null=True)

    class Meta:
        managed = False
        db_table = 'intercambio"."vista_refrendos'
