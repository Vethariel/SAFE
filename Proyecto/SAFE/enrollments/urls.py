from django.urls import path
from . import views

urlpatterns = [
    # Dashboard de aprendizaje (My Learning)
    path("my-learning/", views.home, name="my_learning"),
    path("", views.home, name="home"),
    path("enroll-user/", views.enroll_user, name="enroll_user"),
]
