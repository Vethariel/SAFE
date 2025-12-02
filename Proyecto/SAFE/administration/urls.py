from django.urls import path
from .views import dashboard, courses, users, paths, teams

urlpatterns = [
    path("", dashboard.admin_panel, name="admin_panel"),
    path("course/create/", courses.course_create, name="course_create"),
    path("course/<int:pk>/", courses.course_detail, name="course_detail"),
    path("course/<int:pk>/edit/", courses.course_update, name="course_update"),
    path("course/<int:pk>/delete/", courses.course_delete, name="course_delete"),
    path(
        "course/<int:course_pk>/modules/create/",
        courses.module_create,
        name="module_create",
    ),
    path(
        "modules/<int:pk>/move/<str:direction>/",
        courses.module_move,
        name="module_move",
    ),
    path(
        "modules/<int:module_pk>/content/create/",
        courses.content_create,
        name="content_create",
    ),
    path(
        "modules/content/<int:content_pk>/move/<str:direction>/",
        courses.content_move,
        name="content_move",
    ),
    path(
        "modules/content/<int:content_pk>/update/",
        courses.content_update,
        name="content_update",
    ),
    path(
        "modules/content/<int:content_pk>/delete/",
        courses.content_delete,
        name="content_delete",
    ),
    path("modules/<int:pk>/delete/", courses.module_delete, name="module_delete"),
    # Learning Paths
    path("paths/create/", paths.path_create, name="path_create"),
    path("paths/<int:pk>/", paths.path_detail, name="path_detail"),
    path("paths/<int:pk>/edit/", paths.path_update, name="path_update"),
    path("paths/<int:pk>/delete/", paths.path_delete, name="path_delete"),
    path("paths/<int:pk>/add-course/", paths.path_add_course, name="path_add_course"),
    path(
        "paths/<int:pk>/remove-course/<int:course_id>/",
        paths.path_remove_course,
        name="path_remove_course",
    ),
    path(
        "paths/<int:pk>/move-up/<int:course_id>/",
        paths.path_move_up,
        name="path_move_up",
    ),
    path(
        "paths/<int:pk>/move-down/<int:course_id>/",
        paths.path_move_down,
        name="path_move_down",
    ),
    path("delete/<int:pk>/", users.user_delete, name="user_del"),
    path(
        "course/<int:course_pk>/exam/create/",
        courses.create_exam_for_course,
        name="create_exam_for_course",
    ),
    path(
        "course/<int:course_pk>/exam/create/manual/",
        views.create_exam_manual,
        name="create_exam_manual",
    ),
    path("users/<int:user_id>/role/", views.user_change_role, name="user_change_role"),
    # Teams
    path("teams/create/", teams.team_create, name="team_create"),
    path("teams/<int:pk>/update/", teams.team_update, name="team_update"),
    path("teams/<int:pk>/delete/", teams.team_delete, name="team_delete"),
    path("teams/<int:pk>/add_member/", teams.team_add_member, name="team_add_member"),
    path(
        "teams/<int:pk>/remove_member/<int:user_id>/",
        teams.team_remove_member,
        name="team_remove_member",
    ),
]
