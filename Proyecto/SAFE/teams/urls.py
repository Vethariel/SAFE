from django.urls import path
from . import views

urlpatterns = [
    path("supervisor/", views.supervisor_panel, name="supervisor_panel"),
]
