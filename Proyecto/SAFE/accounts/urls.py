from django.urls import path
from . import views

urlpatterns = [
    path("", views.login, name="home"),
    path("login/", views.login, name="login"),
    path("profile/", views.profile, name="profile"),
    path("users/log", views.log, name="log"),
    path("signup/", views.to_signup, name="to_signup"),
    path("users/add/", views.user_add, name="user_add"),
    path('admin-create-user/', views.admin_create_user, name='admin_create_user'),
    path("logout/", views.logout, name="logout"),
    path('update-role/<int:pk>/', views.user_update_role, name='user_update_role'),
    path('toggle-status/<int:pk>/', views.user_toggle_status, name='user_toggle_status'),
]
