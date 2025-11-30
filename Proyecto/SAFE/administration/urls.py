from django.urls import path
from . import views
from accounts import views as av

urlpatterns = [
    path("", views.admin_panel, name="admin_panel"),
    path("course/create/", views.course_create, name="course_create"),
    path("course/<int:pk>/", views.course_detail, name="course_detail"),
    path("course/<int:pk>/edit/", views.course_update, name="course_update"),
    path("course/<int:pk>/delete/", views.course_delete, name="course_delete"),
    path(
        "course/<int:course_pk>/modules/create/",
        views.module_create,
        name="module_create",
    ),
    path(
        "modules/<int:module_pk>/content/create/",
        views.content_create,
        name="content_create",
    ),
    path(
        "modules/content/<int:content_pk>/update/",
        views.content_update,
        name="content_update",
    ),
    path(
        "modules/content/<int:content_pk>/delete/",
        views.content_delete,
        name="content_delete",
    ),
    path("modules/<int:pk>/delete/", views.module_delete, name="module_delete"),
    path('delete/<int:pk>/', views.user_delete, name='user_del'),
    path(
        "course/<int:course_pk>/exam/create/",
        views.create_exam_for_course,
        name="create_exam_for_course",
    ),
    path("users/<int:user_id>/role/", views.user_change_role, name="user_change_role"),
]
