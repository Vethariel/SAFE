from django.urls import path
from . import views

urlpatterns = [
    path("paths/", views.paths, name="paths"),
]
