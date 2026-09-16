"""Modelos de solo lectura del contexto empresa (tarea 3.3).

Lee solo `intercambio.vista_empresa`. Columnas tomadas de
`base_de_datos/vistas/vista_empresa_v1.sql`; no inventar columnas.
Puede traer varias filas por placa (periodos); el selector toma la
vigente (`activa` primero). `placa_norma` es solo llave de mapeo ORM.

Diferimiento documentado (compuerta PR5): ver `propietario/modelos.py`
(`.values()` sin identidad ORM; `CompositePrimaryKey` solo si se
instanciaran modelos).
"""
from django.db import models


class VistaEmpresa(models.Model):
    """Empresa implementadora por placa (el selector resuelve la vigente)."""

    placa_norma = models.TextField(primary_key=True)
    placa = models.TextField(null=True)
    codigo_correlativo = models.TextField(null=True)
    estado_aprobacion = models.TextField(null=True)
    activa = models.BooleanField(null=True)
    nombre_empresa = models.TextField(null=True)
    numero_autorizacion = models.TextField(null=True)
    esta_autorizada = models.BooleanField(null=True)
    fecha_autorizacion = models.DateField(null=True)

    class Meta:
        managed = False
        db_table = 'intercambio"."vista_empresa'
