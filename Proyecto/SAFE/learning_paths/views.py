from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from enrollments.services import (
    get_courses_in_learning_path_for_user,
    get_paths_for_user,
    _build_catalog_card_for_course,
    _build_inscriptions_prefetch,
)
from .models import LearningPath
from courses.models import Course


@login_required
def paths(request):
    """Listado de rutas visibles según el rol del usuario (RF5)."""
    paths = get_paths_for_user(request.user)

    # Para cada ruta, traer cursos visibles para el usuario
    path_cards = []
    for path in paths:
        courses = get_courses_in_learning_path_for_user(request.user, path)
        path_cards.append((path, courses))

    return render(request, "learning_paths/paths.html", {"path_cards": path_cards})


@login_required
def path_detail(request, pk: int):
    """
    Detalle de una ruta de aprendizaje: muestra todos los cursos de la ruta,
    pero solo permite abrir aquellos en los que el usuario tiene acceso.
    """
    learning_path = get_object_or_404(LearningPath, pk=pk)

    courses_qs = (
        Course.objects.filter(in_paths__learning_path=learning_path)
        .annotate(
            modules_count=Count("modules", distinct=True),
            contents_count=Count("modules__contents", distinct=True),
        )
        .order_by("name")
        .distinct()
    )

    prefetch = _build_inscriptions_prefetch(request.user)
    if prefetch is not None:
        courses_qs = courses_qs.prefetch_related(prefetch)

    course_cards = [
        _build_catalog_card_for_course(course, request.user) for course in courses_qs
    ]

    context = {
        "path": learning_path,
        "course_cards": course_cards,
    }
    return render(request, "learning_paths/path_detail.html", context)
