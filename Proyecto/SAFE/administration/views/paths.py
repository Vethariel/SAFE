from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib import messages
from courses.models import Course
from learning_paths.models import LearningPath, CourseInPath
from administration.forms import LearningPathForm


@login_required
def path_create(request):
    if request.method == "POST":
        form = LearningPathForm(request.POST, request.FILES)
        if form.is_valid():
            path = form.save(commit=False)
            path.created_by = request.user
            path.save()
            messages.success(request, f"Ruta '{path.name}' creada exitosamente")
            return redirect("path_detail", pk=path.pk)
    else:
        form = LearningPathForm()

    return render(
        request,
        "administration/path_form.html",
        {"form": form, "title": "Crear Ruta de Aprendizaje"},
    )


@login_required
def path_detail(request, pk):
    learning_path = get_object_or_404(LearningPath, pk=pk)

    courses_in_path = CourseInPath.objects.filter(
        learning_path=learning_path
    ).select_related("course")

    ordered_courses = []
    if courses_in_path.exists():
        current = courses_in_path.filter(previous_course__isnull=True).first()

        next_map = {cip.course_id: cip for cip in courses_in_path}  # pyright: ignore[reportAttributeAccessIssue]

        while current:
            ordered_courses.append(current)
            if current.next_course_id:  # pyright: ignore[reportAttributeAccessIssue]
                next_course_id = current.next_course_id  # pyright: ignore[reportAttributeAccessIssue]

                current = next_map.get(next_course_id)
            else:
                current = None

    existing_course_ids = [cip.course.id for cip in courses_in_path]  # pyright: ignore[reportAttributeAccessIssue]
    available_courses = Course.objects.exclude(id__in=existing_course_ids).order_by(
        "name"
    )

    return render(
        request,
        "administration/path_detail.html",
        {
            "learning_path": learning_path,
            "ordered_courses": ordered_courses,
            "available_courses": available_courses,
        },
    )


@login_required
def path_update(request, pk):
    path = get_object_or_404(LearningPath, pk=pk)
    if request.method == "POST":
        form = LearningPathForm(request.POST, request.FILES, instance=path)
        if form.is_valid():
            new_status = form.cleaned_data.get("status")

            if new_status == LearningPath.PathStatus.ACTIVE:
                inactive_courses = (
                    Course.objects.filter(in_paths__learning_path=path)
                    .exclude(status=Course.CourseStatus.ACTIVE)
                    .distinct()
                )

                if inactive_courses.exists():
                    if request.POST.get("confirm_activate_courses") == "true":
                        inactive_courses.update(status=Course.CourseStatus.ACTIVE)
                    else:
                        messages.warning(
                            request,
                            "Esta ruta contiene cursos inactivos. Debes activarlos primero.",
                        )
                        return render(
                            request,
                            "administration/path_form.html",
                            {
                                "form": form,
                                "title": "Editar Ruta",
                                "learning_path": path,
                                "inactive_courses": inactive_courses,
                            },
                        )

            form.save()
            messages.success(request, "Ruta actualizada exitosamente")
            return redirect("path_detail", pk=pk)
    else:
        form = LearningPathForm(instance=path)

    return render(
        request,
        "administration/path_form.html",
        {"form": form, "title": "Editar Ruta", "learning_path": path},
    )


@login_required
def path_delete(request, pk):
    path = get_object_or_404(LearningPath, pk=pk)
    if request.method == "POST":
        path.delete()
        messages.success(request, "Ruta eliminada exitosamente")
        return redirect("admin_panel")
    return redirect("admin_panel")


@login_required
@require_POST
def path_add_course(request, pk):
    learning_path = get_object_or_404(LearningPath, pk=pk)
    course_id = request.POST.get("course_id")
    course = get_object_or_404(Course, pk=course_id)

    # Check if course is already in path
    if CourseInPath.objects.filter(learning_path=learning_path, course=course).exists():
        messages.error(request, "El curso ya está en la ruta.")
        return redirect("path_detail", pk=pk)

    with transaction.atomic():
        # Find the last course in the path
        last_cip = CourseInPath.objects.filter(
            learning_path=learning_path, next_course__isnull=True
        ).first()

        # Create new CIP
        new_cip = CourseInPath(
            learning_path=learning_path,
            course=course,
            previous_course=last_cip.course if last_cip else None,
            next_course=None,
        )
        new_cip.save()

        # Update the old last course to point to the new one
        if last_cip:
            last_cip.next_course = course
            last_cip.save()

    messages.success(request, "Curso agregado a la ruta.")
    return redirect("path_detail", pk=pk)


@login_required
@require_POST
def path_remove_course(request, pk, course_id):
    learning_path = get_object_or_404(LearningPath, pk=pk)
    cip_to_remove = get_object_or_404(
        CourseInPath, learning_path=learning_path, course_id=course_id
    )

    with transaction.atomic():
        prev_course = cip_to_remove.previous_course
        next_course = cip_to_remove.next_course

        # Update previous CIP if it exists
        if prev_course:
            prev_cip = CourseInPath.objects.get(
                learning_path=learning_path, course=prev_course
            )
            prev_cip.next_course = next_course
            prev_cip.save()

        # Update next CIP if it exists
        if next_course:
            next_cip = CourseInPath.objects.get(
                learning_path=learning_path, course=next_course
            )
            next_cip.previous_course = prev_course
            next_cip.save()

        cip_to_remove.delete()

    messages.success(request, "Curso eliminado de la ruta.")
    return redirect("path_detail", pk=pk)


def _swap_with_previous(learning_path, current_cip):
    """
    Swaps current_cip with its predecessor.
    Assumes current_cip.previous_course is NOT None.
    """
    prev_course = current_cip.previous_course
    prev_cip = CourseInPath.objects.get(learning_path=learning_path, course=prev_course)

    pre_prev_course = prev_cip.previous_course
    next_course = current_cip.next_course

    # 1. Update current_cip pointers
    current_cip.previous_course = pre_prev_course
    current_cip.next_course = prev_course

    # 2. Update prev_cip pointers
    prev_cip.previous_course = current_cip.course
    prev_cip.next_course = next_course

    # 3. Update pre_prev_cip (if exists)
    if pre_prev_course:
        pre_prev_cip = CourseInPath.objects.get(
            learning_path=learning_path, course=pre_prev_course
        )
        pre_prev_cip.next_course = current_cip.course
        pre_prev_cip.save()

    # 4. Update next_cip (if exists)
    if next_course:
        next_cip = CourseInPath.objects.get(
            learning_path=learning_path, course=next_course
        )
        next_cip.previous_course = prev_cip.course
        next_cip.save()

    current_cip.save()
    prev_cip.save()


@login_required
@require_POST
def path_move_up(request, pk, course_id):
    learning_path = get_object_or_404(LearningPath, pk=pk)
    current_cip = get_object_or_404(
        CourseInPath, learning_path=learning_path, course_id=course_id
    )

    if not current_cip.previous_course:
        messages.warning(request, "El curso ya está al inicio.")
        return redirect("path_detail", pk=pk)

    with transaction.atomic():
        _swap_with_previous(learning_path, current_cip)

    messages.success(request, "Orden actualizado.")
    return redirect("path_detail", pk=pk)


@login_required
@require_POST
def path_move_down(request, pk, course_id):
    learning_path = get_object_or_404(LearningPath, pk=pk)
    current_cip = get_object_or_404(
        CourseInPath, learning_path=learning_path, course_id=course_id
    )

    if not current_cip.next_course:
        messages.warning(request, "El curso ya está al final.")
        return redirect("path_detail", pk=pk)

    # Moving A down is same as moving B (A's next) up
    next_cip = CourseInPath.objects.get(
        learning_path=learning_path, course=current_cip.next_course
    )

    with transaction.atomic():
        _swap_with_previous(learning_path, next_cip)

    messages.success(request, "Orden actualizado.")
    return redirect("path_detail", pk=pk)
