from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("api/resolver/", views.resolver, name="resolver"),
    path("salud/", views.salud, name="salud"),
]
