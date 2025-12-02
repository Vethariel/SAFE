from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from accounts.models import AppUser
from courses.models import Course
from enrollments.models import CourseInscription

from enrollments.services import get_courses_for_user
from learning_paths.models import LearningPath
from enrollments.services import _build_catalog_card_for_course, _build_inscriptions_prefetch


@login_required
def home(request):
    """Dashboard de aprendizaje (My learning)."""
    # Rutas primero
    paths = LearningPath.objects.all().order_by("-created_at")

    # Cursos visibles para el usuario con datos de tarjeta estilo catálogo
    courses_qs = (
        get_courses_for_user(request.user)
        .annotate(
            modules_count=Count("modules", distinct=True),
            contents_count=Count("modules__contents", distinct=True),
        )
        .order_by("-created_at")
    )
    prefetch = _build_inscriptions_prefetch(request.user)
    if prefetch is not None:
        courses_qs = courses_qs.prefetch_related(prefetch)
    course_cards = [_build_catalog_card_for_course(course, request.user) for course in courses_qs]

    return render(
        request,
        "enrollments/home.html",
        {"courses": courses_qs, "paths": paths, "course_cards": course_cards},
    )


@login_required
@require_POST
def enroll_user(request):
    user_id = request.POST.get("user_id")
    course_id = request.POST.get("course_id")

    user = get_object_or_404(AppUser, pk=user_id)
    course = get_object_or_404(Course, pk=course_id)

    exists = CourseInscription.objects.filter(app_user=user, course=course).exists()

    if exists:
        # Mensaje de advertencia exacto
        messages.warning(
            request, "El colaborador ya se encuentra inscrito a este curso."
        )
    else:
        CourseInscription.objects.create(
            app_user=user,
            course=course,
            status="enrolled",
            enrollment_date=timezone.now(),
            progress=0,
        )
        # Mensaje de éxito exacto (el emoji lo pondremos visualmente en el HTML)
        messages.success(request, "Colaborador inscrito exitosamente.")

    # Redirigir asegurando que volvemos a la pestaña de usuarios
    return redirect(reverse("admin_panel") + "?tab=usuarios")
