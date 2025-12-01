from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Team, TeamUser
from enrollments.models import CourseInscription, PathInscription, ContentProgress
from enrollments.services import update_inscription_progress
from courses.models import Course
from learning_paths.models import LearningPath
from accounts.models import AppUser
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Count, Avg, Max
from django.db.models.functions import TruncDate
import json
from django.core.serializers.json import DjangoJSONEncoder


@login_required
def supervisor_panel(request):
    if request.user.role != "supervisor":
        return HttpResponse("No tienes permisos", status=403)

    active_tab = request.GET.get("tab", "equipo")

    # Obtener equipos del supervisor
    teams = Team.objects.filter(supervisor=request.user)

    # Obtener progreso (inscripciones) de los miembros de sus equipos
    base_queryset = CourseInscription.objects.filter(
        app_user__team_memberships__team__in=teams
    )

    # Filtros
    filter_course = request.GET.get("course_id")
    filter_student = request.GET.get("student_id")
    filter_status = request.GET.get("status")
    filter_date_start = request.GET.get("date_start")
    filter_date_end = request.GET.get("date_end")

    if filter_course:
        base_queryset = base_queryset.filter(course_id=filter_course)
    if filter_student:
        base_queryset = base_queryset.filter(app_user_id=filter_student)
    if filter_status:
        base_queryset = base_queryset.filter(status=filter_status)
    if filter_date_start:
        base_queryset = base_queryset.filter(enrollment_date__gte=filter_date_start)
    if filter_date_end:
        base_queryset = base_queryset.filter(enrollment_date__lte=filter_date_end)

    # Recalcular progreso en tiempo real para asegurar consistencia
    # Esto corrige discrepancias entre el progreso real (ContentProgress) y el campo almacenado
    for inscription in base_queryset:
        update_inscription_progress(inscription)

    team_progress = (
        base_queryset.select_related("app_user", "course")
        .annotate(last_activity=Max("content_progress__completed_at"))
        .order_by("app_user__username", "-enrollment_date")
    )

    # Datos para gráficas

    # 1. Progreso promedio por curso
    course_progress = list(
        base_queryset.values("course__name")
        .annotate(avg_progress=Avg("progress"))
        .order_by("-avg_progress")
    )

    # 2. Progreso promedio por estudiante
    student_progress = list(
        base_queryset.values("app_user__username")
        .annotate(avg_progress=Avg("progress"))
        .order_by("-avg_progress")
    )

    # 3. Actividad por fecha (Contenidos completados)
    activity_queryset = ContentProgress.objects.filter(
        course_inscription__in=base_queryset, completed_at__isnull=False
    )
    timeline_data = list(
        activity_queryset.annotate(date=TruncDate("completed_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    # Serializar datos para JS
    charts_data = {
        "course_progress": course_progress,
        "student_progress": student_progress,
        "timeline": timeline_data,
    }
    charts_json = json.dumps(charts_data, cls=DjangoJSONEncoder)

    # Obtener miembros únicos para la gestión
    team_members = (
        AppUser.objects.filter(team_memberships__team__in=teams)
        .distinct()
        .order_by("first_name", "last_name")
        .prefetch_related(
            "course_inscriptions__course", "path_inscriptions__learning_path"
        )
    )

    # Estadísticas básicas (KPIs) - Usamos el queryset filtrado para que los KPIs respondan a los filtros
    total_members = team_members.count()  # Este se mantiene global del equipo
    total_inscriptions = base_queryset.count()
    completed_courses = base_queryset.filter(status="completed").count()
    in_progress_courses = base_queryset.filter(status="in_progress").count()

    stats = {
        "total_members": total_members,
        "total_inscriptions": total_inscriptions,
        "completed_courses": completed_courses,
        "in_progress_courses": in_progress_courses,
        "completion_rate": round((completed_courses / total_inscriptions * 100), 1)
        if total_inscriptions > 0
        else 0,
    }

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
        "stats": stats,
        "charts_data": charts_json,
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
    return redirect(reverse("supervisor_panel") + "?tab=equipo")
