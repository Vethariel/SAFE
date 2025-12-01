from django.shortcuts import render, redirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from accounts.models import AppUser
from courses.models import Course
from enrollments.models import CourseInscription, PathInscription
from . import models
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from enrollments.services import get_courses_for_user, get_paths_for_user


@login_required
def home(request):
    return render(request, "enrollments/home.html")

@login_required
@require_POST
def enroll_user(request):
    user_id = request.POST.get('user_id')
    course_id = request.POST.get('course_id')
    
    user = get_object_or_404(AppUser, pk=user_id)
    course = get_object_or_404(Course, pk=course_id)
    
    exists = CourseInscription.objects.filter(app_user=user, course=course).exists()
    
    if exists:
        # Mensaje de advertencia exacto
        messages.warning(request, "El colaborador ya se encuentra inscrito a este curso.")
    else:
        CourseInscription.objects.create(
            app_user=user,
            course=course,
            status='enrolled',
            enrollment_date=timezone.now(),
            progress=0
        )
        # Mensaje de éxito exacto (el emoji lo pondremos visualmente en el HTML)
        messages.success(request, "Colaborador inscrito exitosamente.")
    
    # Redirigir asegurando que volvemos a la pestaña de usuarios
    return redirect(reverse('admin_panel') + '?tab=usuarios')
    """Dashboard básico de aprendizaje usando visibilidad RF5."""
    courses = get_courses_for_user(request.user)
    paths = get_paths_for_user(request.user)
    return render(
        request,
        "enrollments/home.html",
        {"courses": courses, "paths": paths},
    )
