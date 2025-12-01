from django.urls import path
from . import views

urlpatterns = [
    path("paths/", views.paths, name="paths"),
    path("paths/<int:pk>/", views.path_detail, name="learning_path_detail"),
]
