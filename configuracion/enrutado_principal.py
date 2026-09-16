"""Enrutado principal: solo delega a enrutadores por contexto."""
from django.http import JsonResponse
from django.urls import path


def vista_salud(peticion):
    """Responde el estado interno del servicio.

    Args:
        peticion: Peticion HTTP entrante.

    Returns:
        JsonResponse: Estado correcto del servicio.
    """
    return JsonResponse({"estado": "correcto"})


urlpatterns = [
    path("salud", vista_salud, name="salud"),
]
