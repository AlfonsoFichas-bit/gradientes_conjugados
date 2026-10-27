"""Rutas raíz del proyecto."""

from django.urls import include, path

urlpatterns = [
    path("", include("simulador.urls")),
]
