from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from courses.models import Course, Module
from learning_paths.models import LearningPath
from accounts.models import AppUser
from teams.models import Team


@login_required
def admin_panel(request):
    """
    Vista principal del panel de administración.
    Muestra cursos, rutas de aprendizaje, usuarios y equipos.
    """
    if request.user.role != "analistaTH":
        return HttpResponse("No tienes permisos", status=403)

    active_tab = request.GET.get("tab", "cursos")

    courses = Course.objects.all().order_by("-created_at")
    selected_course = None
    selected_module = None

    course_id = request.GET.get("course")
    if course_id:
        selected_course = get_object_or_404(Course, id=course_id)

        module_id = request.GET.get("module")
        if module_id:
            selected_module = get_object_or_404(
                Module, id=module_id, course=selected_course
            )

    learning_paths = LearningPath.objects.all().order_by("-created_at")

    usuarios = AppUser.objects.all().order_by("id")

    # Equipos
    teams = Team.objects.all().select_related("supervisor").prefetch_related("members")
    supervisors = AppUser.objects.filter(role="supervisor")

    context = {
        "active_tab": active_tab,
        "courses": courses,
        "selected_course": selected_course,
        "selected_module": selected_module,
        "learning_paths": learning_paths,
        "usuarios": usuarios,
        "role_choices": AppUser.UserRole.choices,
        "teams": teams,
        "supervisors": supervisors,
    }
    return render(request, "administration/admin_panel.html", context)
