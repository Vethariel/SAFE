from django.urls import path
from . import views

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
    # Learning Paths
    path("paths/create/", views.path_create, name="path_create"),
    path("paths/<int:pk>/", views.path_detail, name="path_detail"),
    path("paths/<int:pk>/edit/", views.path_update, name="path_update"),
    path("paths/<int:pk>/delete/", views.path_delete, name="path_delete"),
    path("paths/<int:pk>/add-course/", views.path_add_course, name="path_add_course"),
    path(
        "paths/<int:pk>/remove-course/<int:course_id>/",
        views.path_remove_course,
        name="path_remove_course",
    ),
    path(
        "paths/<int:pk>/move-up/<int:course_id>/",
        views.path_move_up,
        name="path_move_up",
    ),
    path(
        "paths/<int:pk>/move-down/<int:course_id>/",
        views.path_move_down,
        name="path_move_down",
    ),
]
