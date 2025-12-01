from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Team, TeamUser
from enrollments.models import CourseInscription, PathInscription
from courses.models import Course
from learning_paths.models import LearningPath
from accounts.models import AppUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def supervisor_panel(request):
    if request.user.role != "supervisor":
        return HttpResponse("No tienes permisos", status=403)

    active_tab = request.GET.get("tab", "equipo")

    # Obtener equipos del supervisor
    teams = Team.objects.filter(supervisor=request.user)

    # Obtener progreso (inscripciones) de los miembros de sus equipos
    team_progress = (
        CourseInscription.objects.filter(app_user__team_memberships__team__in=teams)
        .select_related("app_user", "course")
        .order_by("app_user__username", "-enrollment_date")
    )

    # Obtener miembros únicos para la gestión
    team_members = (
        AppUser.objects.filter(team_memberships__team__in=teams)
        .distinct()
        .order_by("first_name", "last_name")
    )

    # Cursos y Rutas disponibles para inscribir
    available_courses = Course.objects.filter(status=Course.CourseStatus.ACTIVE)
    available_paths = LearningPath.objects.filter(status=LearningPath.PathStatus.ACTIVE)

    context = {
        "active_tab": active_tab,
        "team_progress": team_progress,
        "teams": teams,
        "team_members": team_members,
        "available_courses": available_courses,
        "available_paths": available_paths,
    }
    return render(request, "teams/supervisor_panel.html", context)


@login_required
@require_POST
def enroll_user_course(request):
    user_id = request.POST.get("user_id")
    course_id = request.POST.get("course_id")

    # Verificar permisos: el usuario debe pertenecer a un equipo del supervisor
    if not TeamUser.objects.filter(
        team__supervisor=request.user, app_user_id=user_id
    ).exists():
        messages.error(request, "No tienes permiso para gestionar a este usuario.")
        return redirect("supervisor_panel")

    user = get_object_or_404(AppUser, pk=user_id)
    course = get_object_or_404(Course, pk=course_id)

    if CourseInscription.objects.filter(app_user=user, course=course).exists():
        messages.warning(
            request, f"{user.username} ya está inscrito en el curso {course.name}."
        )
    else:
        CourseInscription.objects.create(app_user=user, course=course)
        messages.success(
            request, f"{user.username} inscrito exitosamente en {course.name}."
        )

    return redirect("supervisor_panel")


@login_required
@require_POST
def enroll_user_path(request):
    user_id = request.POST.get("user_id")
    path_id = request.POST.get("path_id")

    if not TeamUser.objects.filter(
        team__supervisor=request.user, app_user_id=user_id
    ).exists():
        messages.error(request, "No tienes permiso para gestionar a este usuario.")
        return redirect("supervisor_panel")

    user = get_object_or_404(AppUser, pk=user_id)
    learning_path = get_object_or_404(LearningPath, pk=path_id)

    if PathInscription.objects.filter(
        app_user=user, learning_path=learning_path
    ).exists():
        messages.warning(
            request,
            f"{user.username} ya está inscrito en la ruta {learning_path.name}.",
        )
    else:
        PathInscription.objects.create(app_user=user, learning_path=learning_path)
        messages.success(
            request,
            f"{user.username} inscrito exitosamente en la ruta {learning_path.name}.",
        )

    return redirect("supervisor_panel")


@login_required
@require_POST
def unenroll_user_course(request, inscription_id):
    inscription = get_object_or_404(CourseInscription, pk=inscription_id)

    # Verificar permisos
    if not TeamUser.objects.filter(
        team__supervisor=request.user, app_user=inscription.app_user
    ).exists():
        messages.error(request, "No tienes permiso para gestionar a este usuario.")
        return redirect("supervisor_panel")

    inscription.delete()  # O cambiar estado a WITHDRAWN
    messages.success(request, "Inscripción eliminada.")
    return redirect(reverse("supervisor_panel") + "?tab=estadisticas")
