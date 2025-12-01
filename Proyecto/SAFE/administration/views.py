from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.urls import reverse
from django.db import transaction
from courses.models import Course, Module, Content, Exam
from administration.services import change_role
from learning_paths.models import LearningPath, CourseInPath
from accounts.models import AppUser
from django.contrib import messages
from .forms import (
    CourseForm,
    ModuleForm,
    ContentForm,
    MaterialForm,
    LearningPathForm,
    ExamUploadForm,
)
from courses.views import parse_evaluacion
from teams.models import Team, TeamUser


@login_required
def admin_panel(request):
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


@login_required
def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.created_by = request.user
            course.save()
            messages.success(request, f"Curso '{course.name}' creado exitosamente")
            return redirect("course_detail", pk=course.pk)
    else:
        form = CourseForm()

    return render(
        request,
        "administration/course_form.html",
        {"form": form, "title": "Crear Curso"},
    )


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    modules = course.modules.all().order_by("id")  # pyright: ignore[reportAttributeAccessIssue]
    exam_module = modules.filter(name__iexact="Examen").first()

    selected_module = None
    module_contents = None
    selected_content = None
    content_edit_form = None
    material_edit_form = None
    module_id = request.GET.get("module")
    if module_id:
        try:
            selected_module = modules.get(pk=module_id)
        except Module.DoesNotExist:
            selected_module = None
        else:
            module_contents = selected_module.contents.select_related(
                "material", "exam"
            ).order_by("order", "created_at")
            content_id = request.GET.get("content")
            if module_contents.exists() and content_id:
                selected_content = module_contents.filter(pk=content_id).first()

            if selected_content:
                content_edit_form = ContentForm(instance=selected_content)
                if selected_content.material:
                    material_edit_form = MaterialForm(
                        instance=selected_content.material
                    )
                else:
                    material_edit_form = MaterialForm()

    # forms for inline use
    module_form = ModuleForm()
    content_form = ContentForm()
    material_form = MaterialForm()

    context = {
        "course": course,
        "modules": modules,
        "selected_module": selected_module,
        "module_contents": module_contents,
        "selected_content": selected_content,
        "module_form": module_form,
        "content_form": content_form,
        "material_form": material_form,
        "content_edit_form": content_edit_form,
        "material_edit_form": material_edit_form,
        "exam_module": exam_module,
    }
    return render(request, "administration/course_detail.html", context)


@login_required
def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            new_status = form.cleaned_data.get("status")

            if new_status != Course.CourseStatus.ACTIVE:
                active_paths = LearningPath.objects.filter(
                    courses__course=course, status=LearningPath.PathStatus.ACTIVE
                ).distinct()

                if active_paths.exists():
                    if request.POST.get("confirm_deactivate_paths") == "true":
                        active_paths.update(status=LearningPath.PathStatus.DRAFT)
                    else:
                        messages.warning(
                            request,
                            "Este curso pertenece a rutas activas. Debes desactivar las rutas primero.",
                        )
                        return render(
                            request,
                            "administration/course_form.html",
                            {
                                "form": form,
                                "title": "Editar Curso",
                                "course": course,
                                "affected_paths": active_paths,
                            },
                        )

            form.save()
            messages.success(request, f"Curso '{course.name}' actualizado")
            return redirect("course_detail", pk=course.pk)
    else:
        form = CourseForm(instance=course)

    return render(
        request,
        "administration/course_form.html",
        {"form": form, "title": "Editar Curso", "course": course},
    )


@login_required
@require_POST
def user_change_role(request, user_id):
    target_user = get_object_or_404(AppUser, pk=user_id)
    new_role = request.POST.get("role", "")

    success = change_role(request.user, target_user, new_role)
    if not success:
        return HttpResponse("No tienes permisos para realizar esta acción", status=403)

    return redirect(reverse("admin_panel") + "?tab=usuarios")


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if request.method == "POST":
        course.delete()
        messages.success(request, f"Curso '{course.name}' eliminado")
        return redirect("admin_panel")

    return render(request, "administration/admin_panel.html")


# vistas de modulos


@login_required
def module_create(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)

    if request.method == "POST":
        form = ModuleForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.course = course
            module.save()
            messages.success(request, f"Módulo '{module.name}' agregado")
            # redirigir y seleccionar el módulo creado
            return redirect(
                reverse("course_detail", kwargs={"pk": course.pk})
                + f"?module={module.pk}"
            )
    else:
        form = ModuleForm()

    return render(
        request,
        "administration/module_form.html",
        {"form": form, "course": course, "title": "Agregar Módulo"},
    )


@login_required
@require_POST
def module_delete(request, pk):
    module = get_object_or_404(Module, pk=pk)
    course_pk = module.course.pk

    with transaction.atomic():
        module.delete()
    messages.success(request, "Módulo eliminado")
    return redirect("course_detail", pk=course_pk)


# vista de contenido


@login_required
@require_POST
def content_create(request, module_pk):
    module = get_object_or_404(Module, pk=module_pk)
    redirect_url = (
        reverse("course_detail", kwargs={"pk": module.course.pk})
        + f"?module={module.pk}#content-block-new"
    )

    form_data = request.POST.copy()
    block_type = form_data.get("block_type")
    is_exam_module = module.name.strip().lower() == "examen"

    if is_exam_module:
        block_type = Content.BlockType.QUIZ
        form_data["block_type"] = Content.BlockType.QUIZ

    content_form = ContentForm(form_data)

    # Determinar el tipo esperado según el block_type
    expected_type = None
    if block_type == Content.BlockType.IMAGE:
        expected_type = "jpg"
    elif block_type == Content.BlockType.VIDEO:
        expected_type = "mp4"
    elif block_type == Content.BlockType.PDF:
        expected_type = "pdf"

    # Agregar expected_type a los datos del formulario
    material_data = request.POST.copy()
    if expected_type:
        material_data["expected_type"] = expected_type

    material_form = MaterialForm(material_data, request.FILES)

    if content_form.is_valid():
        content = content_form.save(commit=False)
        content.module = module

        if is_exam_module:
            content.block_type = Content.BlockType.QUIZ

        block_type = content.block_type
        content.content_type = Content.ContentType.MATERIAL

        if block_type == Content.BlockType.QUIZ:
            # Obtener las preguntas del formulario
            import json

            quiz_questions = request.POST.get("quiz_questions", "[]")
            try:
                questions = json.loads(quiz_questions)
                exam = Exam.objects.create(
                    questions=questions, total_questions=len(questions)
                )
                content.exam = exam
                content.content_type = Content.ContentType.EXAM
            except json.JSONDecodeError:
                messages.error(
                    request, "Error al procesar las preguntas del cuestionario."
                )
                return redirect(redirect_url)
        elif block_type in (
            Content.BlockType.IMAGE,
            Content.BlockType.VIDEO,
            Content.BlockType.PDF,
        ):
            if material_form.is_valid() and material_form.cleaned_data.get("file"):
                material = material_form.save(commit=False)
                # Asignar tipo automáticamente según block_type
                if block_type == Content.BlockType.IMAGE:
                    material.type = "jpg"
                elif block_type == Content.BlockType.VIDEO:
                    material.type = "mp4"
                elif block_type == Content.BlockType.PDF:
                    material.type = "pdf"
                material.save()
                content.material = material
            else:
                # Mostrar errores específicos del formulario de material
                if material_form.errors:
                    for field, field_errors in material_form.errors.items():
                        for error in field_errors:
                            messages.error(request, f"Archivo: {error}")
                else:
                    messages.error(
                        request,
                        "Adjunta un archivo para imágenes, videos o PDFs.",
                    )
                return redirect(redirect_url)

        content.save()
        messages.success(request, "Contenido agregado al módulo.")
        return redirect(redirect_url)

    for field, field_errors in content_form.errors.items():
        for error in field_errors:
            messages.error(request, f"{field}: {error}")

    return redirect(redirect_url)


@login_required
def content_update(request, content_pk):
    content = get_object_or_404(Content, pk=content_pk)
    module = content.module

    if request.method != "POST":
        return redirect(
            reverse("course_detail", kwargs={"pk": module.course.pk})
            + f"?module={module.pk}&content={content.pk}#content-inspector"
        )

    is_exam_module = content.module.name.strip().lower() == "examen"

    form_data = request.POST.copy()
    if is_exam_module:
        form_data["block_type"] = Content.BlockType.QUIZ

    content_form = ContentForm(form_data, instance=content)
    material_instance = content.material if content.material else None

    # Determinar el tipo esperado según el block_type
    block_type = form_data.get("block_type")
    expected_type = None
    if block_type == Content.BlockType.IMAGE:
        expected_type = "jpg"
    elif block_type == Content.BlockType.VIDEO:
        expected_type = "mp4"
    elif block_type == Content.BlockType.PDF:
        expected_type = "pdf"

    # Agregar expected_type a los datos del formulario
    material_data = request.POST.copy()
    if expected_type:
        material_data["expected_type"] = expected_type

    material_form = MaterialForm(
        material_data, request.FILES, instance=material_instance
    )

    material_checked = False

    if content_form.is_valid():
        updated_content = content_form.save(commit=False)
        if is_exam_module:
            updated_content.block_type = Content.BlockType.QUIZ
        block_type = updated_content.block_type
        updated_content.content_type = Content.ContentType.MATERIAL

        if block_type == Content.BlockType.QUIZ:
            import json

            quiz_questions = request.POST.get("quiz_questions", "[]")

            if not content.exam:
                content.exam = Exam.objects.create(questions=[], total_questions=0)

            try:
                questions = json.loads(quiz_questions)
                # solo actualizar si recibimos preguntas (para evitar borrar si el campo viene vacío por error)
                # a si es una lista vacía intencional
                # asumimos que el frontend siempre envía el estado actual xd
                content.exam.questions = questions
                content.exam.total_questions = len(questions)
                content.exam.save()
            except json.JSONDecodeError:
                messages.error(
                    request, "Error al procesar las preguntas del cuestionario."
                )

            updated_content.exam = content.exam
            updated_content.material = None
            updated_content.content_type = Content.ContentType.EXAM
        elif not is_exam_module and block_type in (
            Content.BlockType.IMAGE,
            Content.BlockType.VIDEO,
            Content.BlockType.PDF,
        ):
            material_checked = True
            if material_form.is_valid():
                existing_file = material_form.cleaned_data.get("file") or (
                    material_form.instance and material_form.instance.file
                )
                if not existing_file:
                    material_form.add_error(
                        "file",
                        "Adjunta un archivo para imágenes, videos o PDFs.",
                    )
                else:
                    material = material_form.save(commit=False)
                    # Asignar tipo automáticamente según block_type
                    if block_type == Content.BlockType.IMAGE:
                        material.type = "jpg"
                    elif block_type == Content.BlockType.VIDEO:
                        material.type = "mp4"
                    elif block_type == Content.BlockType.PDF:
                        material.type = "pdf"
                    material.save()
                    updated_content.material = material
                    updated_content.exam = None
            # Si el formulario no es válido, no continuar
        else:
            updated_content.material = None
            updated_content.exam = None

        # Solo guardar si no hay errores en el material form cuando se verificó
        if not material_checked or not material_form.errors:
            updated_content.save()
            messages.success(request, "Contenido actualizado.")
    else:
        for field, field_errors in content_form.errors.items():
            for error in field_errors:
                messages.error(request, f"{field}: {error}")

    if material_checked and material_form.errors:
        for field, field_errors in material_form.errors.items():
            for error in field_errors:
                messages.error(request, f"Archivo: {error}")

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)

    return redirect(
        reverse("course_detail", kwargs={"pk": module.course.pk})
        + f"?module={module.pk}&content={content.pk}#content-inspector"
    )


@login_required
@require_POST
def content_delete(request, content_pk):
    content = get_object_or_404(Content, pk=content_pk)
    module = content.module
    course_pk = module.course.pk

    with transaction.atomic():
        content.delete()

    messages.success(request, "Contenido eliminado.")
    return redirect(
        reverse("course_detail", kwargs={"pk": course_pk}) + f"?module={module.pk}"
    )


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


@login_required
def user_delete(request, pk):
    """
    Elimina un usuario basado en su ID (pk).
    Solo permite acceso a usuarios logueados (idealmente validar rol también).
    """
    # Buscamos el usuario o devolvemos error 404 si no existe
    user_to_delete = get_object_or_404(AppUser, pk=pk)

    # Protección: Evitar que el usuario se elimine a sí mismo
    if user_to_delete == request.user:
        messages.error(request, "No puedes eliminar tu propio usuario.")
        return redirect("admin_panel")  # Redirige de vuelta al panel

    if request.method == "POST":
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f"Usuario '{username}' eliminado correctamente.")

    # Redirigimos al panel de administración (asegúrate que 'admin_panel' sea el name en administration/urls.py)
    return redirect("admin_panel")


# administration/views.py


@login_required
@require_POST
def create_exam_for_course(request, course_pk):
    """
    Recibe un archivo .txt, valida su extensión y crea un Examen
    dentro de un módulo automático llamado 'Examen'.
    """
    course = get_object_or_404(Course, pk=course_pk)

    # 1.Buscar o Crear el módulo "Examen"
    exam_module, created = Module.objects.get_or_create(
        course=course,
        name="Examen",
        defaults={
            "description": "Módulo dedicado a las evaluaciones del curso.",
            # Si tienes un campo 'order' o 'duration', puedes poner defaults aquí
        },
    )

    form = ExamUploadForm(request.POST, request.FILES)

    if form.is_valid():
        uploaded_file = request.FILES["file"]
        title = form.cleaned_data["title"]
        difficulty = form.cleaned_data["difficulty"]

        # 2. Validación de extensión (Backend)
        if not uploaded_file.name.lower().endswith(".txt"):
            messages.error(request, "Error: El archivo debe ser tipo .txt")
            return redirect("course_detail", pk=course.pk)

        try:
            # 3. Leer y parsear el archivo de preguntas
            raw_content = uploaded_file.read()
            try:
                text_content = raw_content.decode("utf-8")
            except UnicodeDecodeError:
                text_content = raw_content.decode("latin-1")

            parsed_questions = parse_evaluacion(text_content)

            # Adaptar al formato que usa el frontend (questions/answers)
            questions = []
            for pregunta in parsed_questions:
                opciones = pregunta.get("opciones", [])
                correctas = sum(1 for o in opciones if o.get("es_correcta"))
                q_type = "single" if correctas <= 1 else "multiple"

                answers = [
                    {
                        "id": opcion.get("id"),
                        "text": opcion.get("texto"),
                        "is_correct": opcion.get("es_correcta"),
                    }
                    for opcion in opciones
                ]

                questions.append(
                    {
                        "id": pregunta.get("id"),
                        "text": pregunta.get("texto"),
                        "type": q_type,
                        "answers": answers,
                    }
                )

            with transaction.atomic():
                # 4. Crear el Exam con las preguntas parseadas
                exam = Exam.objects.create(
                    questions=questions,
                    total_questions=len(questions),
                    passing_score=60,
                    max_tries=3,
                )

                # 5. Crear el Content vinculado al módulo "Examen"
                Content.objects.create(
                    module=exam_module,
                    title=title,
                    description=(
                        f"Examen importado desde archivo: {uploaded_file.name}. "
                        f"Dificultad: {difficulty}. "
                        f"Preguntas: {len(questions)}."
                    ),
                    content_type=Content.ContentType.EXAM,
                    block_type=Content.BlockType.QUIZ,
                    exam=exam,
                    is_mandatory=True,
                )

            messages.success(
                request,
                f"Examen '{title}' creado desde '{uploaded_file.name}' con {len(questions)} pregunta(s).",
            )

        except ValueError as e:
            # Errores de formato de parse_evaluacion
            messages.error(request, f"Error en el formato del archivo: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error al procesar el examen: {str(e)}")

    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    # Redirigir al curso, abriendo específicamente el módulo de exámenes
    return redirect(
        reverse("course_detail", kwargs={"pk": course.pk}) + f"?module={exam_module.pk}"
    )


# --- GESTIÓN DE EQUIPOS ---


@login_required
@require_POST
def team_create(request):
    if request.user.role != "analistaTH":
        return HttpResponse("No tienes permisos", status=403)

    name = request.POST.get("name")
    description = request.POST.get("description")
    supervisor_id = request.POST.get("supervisor_id")

    supervisor = None
    if supervisor_id:
        supervisor = get_object_or_404(AppUser, pk=supervisor_id)

    Team.objects.create(name=name, description=description, supervisor=supervisor)

    messages.success(request, "Equipo creado exitosamente.")
    return redirect(reverse("admin_panel") + "?tab=equipos")


@login_required
@require_POST
def team_update(request, pk):
    if request.user.role != "analistaTH":
        return HttpResponse("No tienes permisos", status=403)

    team = get_object_or_404(Team, pk=pk)

    team.name = request.POST.get("name")
    team.description = request.POST.get("description")
    supervisor_id = request.POST.get("supervisor_id")

    if supervisor_id:
        team.supervisor = get_object_or_404(AppUser, pk=supervisor_id)
    else:
        team.supervisor = None

    team.save()

    messages.success(request, "Equipo actualizado exitosamente.")
    return redirect(reverse("admin_panel") + "?tab=equipos")


@login_required
@require_POST
def team_delete(request, pk):
    if request.user.role != "analistaTH":
        return HttpResponse("No tienes permisos", status=403)

    team = get_object_or_404(Team, pk=pk)
    team.delete()

    messages.success(request, "Equipo eliminado exitosamente.")
    return redirect(reverse("admin_panel") + "?tab=equipos")


@login_required
@require_POST
def team_add_member(request, pk):
    if request.user.role != "analistaTH":
        return HttpResponse("No tienes permisos", status=403)

    team = get_object_or_404(Team, pk=pk)
    user_id = request.POST.get("user_id")
    user = get_object_or_404(AppUser, pk=user_id)

    if TeamUser.objects.filter(team=team, app_user=user).exists():
        messages.warning(request, "El usuario ya es miembro del equipo.")
    else:
        TeamUser.objects.create(team=team, app_user=user)
        messages.success(request, "Miembro añadido exitosamente.")

    return redirect(reverse("admin_panel") + "?tab=equipos")


@login_required
@require_POST
def team_remove_member(request, pk, user_id):
    if request.user.role != "analistaTH":
        return HttpResponse("No tienes permisos", status=403)

    team = get_object_or_404(Team, pk=pk)
    user = get_object_or_404(AppUser, pk=user_id)

    TeamUser.objects.filter(team=team, app_user=user).delete()

    messages.success(request, "Miembro eliminado del equipo.")
    return redirect(reverse("admin_panel") + "?tab=equipos")
