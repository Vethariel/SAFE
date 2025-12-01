from django.urls import path
from . import views

urlpatterns = [
    path("supervisor/", views.supervisor_panel, name="supervisor_panel"),
    path(
        "supervisor/enroll/course/", views.enroll_user_course, name="enroll_user_course"
    ),
    path("supervisor/enroll/path/", views.enroll_user_path, name="enroll_user_path"),
    path(
        "supervisor/unenroll/course/<int:inscription_id>/",
        views.unenroll_user_course,
        name="unenroll_user_course",
    ),
]
