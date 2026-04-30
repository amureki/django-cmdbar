from django.urls import path

from . import views

app_name = "djangonaut"

urlpatterns = [
    path("commands/", views.commands, name="commands"),
]
