from django.urls import path
from . import views

urlpatterns = [
    path("catalog/", views.catalog, name="catalog"),
    path("courses/<int:pk>/", views.course_detail_accessible, name="course_detail_accessible"),
    path("contents/<int:content_pk>/exam/", views.take_exam, name="take_exam"),
    path("contents/<int:content_pk>/complete/", views.mark_content_complete, name="mark_content_complete"),
    path("contents/<int:content_pk>/assignment/submit/", views.submit_assignment, name="submit_assignment"),
    path(
        "contents/<int:content_pk>/assignment/submissions/",
        views.assignment_submissions,
        name="assignment_submissions",
    ),
    path("content-progress/<int:progress_id>/grade/", views.grade_assignment, name="grade_assignment"),
    path("create-exam/", views.create_exam_view, name="create_exam"),
]
