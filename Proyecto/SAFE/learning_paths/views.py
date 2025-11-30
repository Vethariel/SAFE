from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from enrollments.services import (
    get_courses_in_learning_path_for_user,
    get_paths_for_user,
)
from .models import LearningPath


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
