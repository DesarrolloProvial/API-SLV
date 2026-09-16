"""Modelos de solo lectura del contexto propietario (tarea 3.3).

Lee solo `intercambio.vista_propietario`. Columnas tomadas de
`base_de_datos/vistas/vista_propietario_v1.sql`; no inventar columnas.
La vista puede traer varias filas por placa (historial de titularidad);
el selector toma la vigente. `placa_norma` es solo llave de mapeo ORM.

Diferimiento documentado (compuerta PR5): `CompositePrimaryKey` no se
adopta porque los selectores usan `.values()` (diccionarios, sin
identidad ORM que colisione); el `pk` simple es inocuo hoy. Si algun
selector llegara a instanciar modelos, revaluar llave compuesta.
"""
from django.db import models


class VistaPropietario(models.Model):
    """Titularidad por placa (el selector resuelve la vigente)."""

    placa_norma = models.TextField(primary_key=True)
    placa = models.TextField(null=True)
    vigente_desde = models.DateField(null=True)
    vigente_hasta = models.DateField(null=True)
    nombre_empresa = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'intercambio"."vista_propietario'
