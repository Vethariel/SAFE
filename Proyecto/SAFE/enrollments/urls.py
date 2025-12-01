from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('enroll-user/', views.enroll_user, name='enroll_user'),
]