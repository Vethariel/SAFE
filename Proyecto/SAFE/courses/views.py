import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import AppUser
from enrollments.models import ContentProgress, CourseInscription
from enrollments.services import (
    get_catalog_courses_for_user,
    get_contents_for_user_in_course,
    get_course_progress,
)
from .services import get_ordered_contents, get_ordered_modules
from .forms import QuestionUploadForm
from .models import Content, Course, Exam


def _to_json_safe(value):
    """
    Convierte estructuras anidadas (listas, diccionarios, sets) a una forma
    segura para JSONField (los sets se transforman en listas).
    """
    if isinstance(value, set):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_json_safe(v) for k, v in value.items()}
    return value


def parse_evaluacion(texto: str):
    """Parsea preguntas tipo 'Q:' y opciones 'O:' desde un texto."""
    preguntas = []
    pregunta_actual = None

    for line in texto.splitlines():
        line = line.strip()
        if not line:
            # Línea vacía: separador entre preguntas
            continue

        if line.startswith("Q:"):
            # Guardar pregunta anterior, si había
            if pregunta_actual is not None:
                preguntas.append(pregunta_actual)

            _, resto = line.split("Q:", 1)
            qid, texto_preg = resto.split("|", 1)

            pregunta_actual = {
                "id": qid.strip(),
                "texto": texto_preg.strip(),
                "opciones": [],
            }

        elif line.startswith("O:"):
            if pregunta_actual is None:
                raise ValueError("Opción sin pregunta previa")

            _, resto = line.split("O:", 1)
            oid, texto_opt, flag = resto.split("|", 2)

            es_correcta = flag.strip() == "1"

            pregunta_actual["opciones"].append(
                {
                    "id": oid.strip(),
                    "texto": texto_opt.strip(),
                    "es_correcta": es_correcta,
                }
            )

        else:
            raise ValueError(f"Línea con formato inválido: {line}")

    # Agregar la última pregunta si existe
    if pregunta_actual is not None:
        preguntas.append(pregunta_actual)

    # Validación extra: cada pregunta con al menos una correcta
    for p in preguntas:
        if not any(o["es_correcta"] for o in p["opciones"]):
            raise ValueError(f"La pregunta '{p['id']}' no tiene opción correcta")

    return preguntas


def is_txt_file(uploaded_file) -> bool:
    """
    Verifica si el archivo subido corresponde a un .txt
    usando la extensión del nombre del archivo.
    """
    if not hasattr(uploaded_file, "name"):
        return False
    return uploaded_file.name.lower().endswith(".txt")


def create_exam_view(request):
    if request.method == "POST":
        form = QuestionUploadForm(request.POST, request.FILES)

        if form.is_valid():
            course = form.cleaned_data["course"]
            difficulty = form.cleaned_data["difficulty"]
            uploaded_file = form.cleaned_data["file"]

            # Placeholder: aquí iría la lógica de negocio para analizar el .txt
            messages.success(
                request,
                f"¡Formulario válido! Archivo '{uploaded_file.name}' listo para procesar.",
            )

            return redirect("create_exam")
        else:
            messages.error(request, "El formulario tiene errores. Por favor, revísalo.")

    else:
        form = QuestionUploadForm()

    return render(request, "courses/create_exam.html", {"form": form})


@login_required
def catalog(request):
    """Catálogo visible según el rol del usuario (RF5)."""
    course_cards = get_catalog_courses_for_user(request.user)
    return render(request, "courses/catalog.html", {"course_cards": course_cards})


@login_required
def course_detail_accessible(request, pk):
    """
    Course detail with module navigation and content progress.
    - First module unlocked; following modules unlock when previous is completed.
    - Content status is tracked via ContentProgress.
    """
    course = get_object_or_404(Course, pk=pk)
    modules = get_ordered_modules(course)

    progress_info = get_course_progress(request.user, course)
    inscription = progress_info["inscription"]

    completed_ids = set()
    content_progress_map = {}
    if inscription:
        completed_qs = ContentProgress.objects.filter(course_inscription=inscription)
        for cp in completed_qs:
            if cp.is_completed:
                completed_ids.add(cp.content_id)  # pyright: ignore[reportAttributeAccessIssue]
            content_progress_map[cp.content_id] = cp  # pyright: ignore[reportAttributeAccessIssue]

    # determine unlocked modules
    unlocked_ids = set()
    module_states = []
    prev_completed = True
    # Permitir navegación libre a Analistas y Supervisores
    unrestricted_mode = request.user.role in [
        AppUser.UserRole.ANALISTA_TH,
        AppUser.UserRole.SUPERVISOR,
    ]

    for module in modules:
        contents_list = list(module.contents.all())
        module_content_ids = [c.id for c in contents_list]
        module_completed = not module_content_ids or all(
            cid in completed_ids for cid in module_content_ids
        )

        is_unlocked = unrestricted_mode or prev_completed
        if is_unlocked:
            unlocked_ids.add(module.id)
        prev_completed = prev_completed and module_completed

        module_states.append(
            {
                "module": module,
                "total_contents": len(module_content_ids),
                "completed_contents": sum(
                    1 for cid in module_content_ids if cid in completed_ids
                ),
                "completed": module_completed,
            }
        )

    # selected module
    default_module_id = modules[0].id if modules else None
    selected_module_id = (
        int(request.GET.get("module", default_module_id)) if default_module_id else None
    )
    selected_module = next((m for m in modules if m.id == selected_module_id), None)

    selected_contents = (
        get_ordered_contents(selected_module) if selected_module else []
    )
    visible_contents = get_contents_for_user_in_course(request.user, course)
    visible_ids = {c.id for c in visible_contents}

    content_rows = []
    for content in selected_contents:
        cp = content_progress_map.get(content.id)
        content_rows.append(
            {
                "content": content,
                "completed": content.id in completed_ids,
                "visible": content.id in visible_ids
                and selected_module_id in unlocked_ids,
                "progress": cp,
                "render_questions": normalize_exam_questions(content.exam),
            }
        )

    context = {
        "course": course,
        "modules_state": module_states,
        "unlocked_module_ids": unlocked_ids,
        "selected_module": selected_module,
        "content_rows": content_rows,
        "progress": progress_info,
    }
    return render(request, "courses/course_detail_accessible.html", context)


@login_required
@require_POST
def mark_content_complete(request, content_pk):
    """Marks a read-only content as completed for the current user."""
    content = get_object_or_404(Content, pk=content_pk)
    course = content.module.course

    if (
        content.block_type == Content.BlockType.QUIZ
        or content.content_type == Content.ContentType.ASSIGNMENT
    ):
        messages.error(
            request, "Este tipo de contenido se completa desde su flujo específico."
        )
        return redirect("course_detail_accessible", pk=course.id)

    try:
        inscription = CourseInscription.objects.get(
            app_user=request.user, course=course
        )
    except CourseInscription.DoesNotExist:
        messages.error(
            request, "Necesitas estar inscrito en este curso para marcar progreso."
        )
        return redirect("course_detail_accessible", pk=course.id)

    allowed_contents = get_contents_for_user_in_course(request.user, course)
    if content not in allowed_contents:
        messages.error(request, "Este contenido aún no está disponible.")
        return redirect("course_detail_accessible", pk=course.id)

    progress, _created = ContentProgress.objects.get_or_create(
        content=content, course_inscription=inscription
    )
    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.started_at = progress.started_at or timezone.now()
    progress.save(update_fields=["is_completed", "completed_at", "started_at"])
    messages.success(request, "Contenido marcado como completado.")

    # Redirigir al mismo módulo donde estaba el usuario
    base_url = reverse("course_detail_accessible", kwargs={"pk": course.id})
    return redirect(f"{base_url}?module={content.module.id}")


@login_required
@require_POST
def submit_assignment(request, content_pk):
    """Allows a collaborator to upload an assignment file."""
    content = get_object_or_404(Content, pk=content_pk)
    course = content.module.course
    if content.content_type != Content.ContentType.ASSIGNMENT:
        return HttpResponse(status=404)

    try:
        inscription = CourseInscription.objects.get(
            app_user=request.user, course=course
        )
    except CourseInscription.DoesNotExist:
        return HttpResponseForbidden()

    allowed_contents = get_contents_for_user_in_course(request.user, course)
    if content not in allowed_contents:
        return HttpResponseForbidden()

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        messages.error(request, "Debes adjuntar un archivo para enviar la tarea.")
        return redirect(
            f"{request.META.get('HTTP_REFERER', request.build_absolute_uri())}"
        )

    progress, _created = ContentProgress.objects.get_or_create(
        content=content, course_inscription=inscription
    )
    progress.file = uploaded_file.read()
    progress.started_at = progress.started_at or timezone.now()
    progress.completed_at = timezone.now()
    progress.is_completed = True
    progress.save(update_fields=["file", "started_at", "completed_at", "is_completed"])
    messages.success(request, "Tarea enviada correctamente.")
    return redirect(f"{request.META.get('HTTP_REFERER', request.build_absolute_uri())}")


@login_required
def assignment_submissions(request, content_pk):
    """List submissions for an assignment so an Analista TH can score them."""
    if request.user.role != AppUser.UserRole.ANALISTA_TH:
        return HttpResponseForbidden()

    content = get_object_or_404(Content, pk=content_pk)
    if content.content_type != Content.ContentType.ASSIGNMENT:
        return HttpResponse(status=404)
    submissions = (
        ContentProgress.objects.filter(content=content)
        .select_related("course_inscription__app_user")
        .order_by("-completed_at")
    )
    return render(
        request,
        "courses/assignment_submissions.html",
        {
            "content": content,
            "submissions": submissions,
            "course": content.module.course,
        },
    )


@login_required
@require_POST
def grade_assignment(request, progress_id):
    """Score an assignment submission."""
    if request.user.role != AppUser.UserRole.ANALISTA_TH:
        return HttpResponseForbidden()

    progress = get_object_or_404(ContentProgress, pk=progress_id)
    if progress.content.content_type != Content.ContentType.ASSIGNMENT:
        return HttpResponse(status=404)
    try:
        score = int(request.POST.get("score"))
    except (TypeError, ValueError):
        messages.error(request, "Ingresa un puntaje válido.")
        return redirect("assignment_submissions", content_pk=progress.content_id)

    progress.score = score
    progress.is_completed = True
    progress.completed_at = progress.completed_at or timezone.now()
    progress.save(update_fields=["score", "is_completed", "completed_at"])
    messages.success(request, "Tarea calificada.")
    return redirect("assignment_submissions", content_pk=progress.content_id)


@login_required
def take_exam(request, content_pk):
    """Permite responder un examen y registra progreso básico."""
    content = get_object_or_404(Content, pk=content_pk)
    course = content.module.course

    # Validar que sea un examen y que el usuario tenga acceso al contenido
    if content.block_type != Content.BlockType.QUIZ or not content.exam:
        return HttpResponse(status=404)

    permitted_contents = get_contents_for_user_in_course(request.user, course)
    if content not in permitted_contents:
        return HttpResponse(status=403)

    questions = normalize_exam_questions(content.exam)
    if request.method == "GET":
        return render(
            request,
            "courses/take_exam.html",
            {"course": course, "content": content, "questions": questions},
        )

    # POST: evaluar
    submitted = {}
    for q in questions:
        qid = q.get("id")
        # Guardar siempre listas; la lógica de corrección
        # internamente convierte a set cuando lo necesita.
        submitted[qid] = request.POST.getlist(f"q-{qid}")

    correct_count, total, results = evaluate_exam_submission(questions, submitted)

    # Registrar progreso si hay inscripción
    try:
        inscription = CourseInscription.objects.get(
            app_user=request.user, course=course
        )
    except CourseInscription.DoesNotExist:
        inscription = None

    if inscription:
        progress, _created = ContentProgress.objects.get_or_create(
            content=content, course_inscription=inscription
        )
        progress.score = correct_count
        # Asegurar que lo que guardamos en JSONField sea 100% serializable.
        progress.results = _to_json_safe(results)
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save(
            update_fields=["score", "results", "is_completed", "completed_at"]
        )

    messages.success(
        request,
        f"Examen enviado. Puntaje: {correct_count}/{total}",
    )
    return render(
        request,
        "courses/take_exam.html",
        {
            "course": course,
            "content": content,
            "questions": questions,
            "results": results,
            "score": correct_count,
            "total": total,
        },
    )


def normalize_exam_questions(exam: Exam):
    """Normaliza preguntas de un examen a un formato uniforme."""
    if not exam or not exam.questions:
        return []

    raw_questions = exam.questions
    if isinstance(raw_questions, str):
        try:
            raw_questions = json.loads(raw_questions)
        except Exception:
            return []

    normalized = []
    if isinstance(raw_questions, list):
        for idx, q in enumerate(raw_questions):
            if not isinstance(q, dict):
                continue
            qid = str(q.get("id") or q.get("question_id") or idx)
            text = q.get("text") or q.get("texto") or q.get("question") or ""
            # Soportar distintos formatos de almacenamiento:
            # - "options" / "opciones" (formatos previos)
            # - "answers" (formato usado por el editor de cuestionarios en administración)
            options = q.get("options") or q.get("opciones") or q.get("answers") or []
            norm_opts = []
            if isinstance(options, list):
                for o_idx, opt in enumerate(options):
                    if not isinstance(opt, dict):
                        continue
                    opt_id = str(opt.get("id") or opt.get("option_id") or o_idx)
                    norm_opts.append(
                        {
                            "id": opt_id,
                            "text": opt.get("text")
                            or opt.get("texto")
                            or opt.get("option")
                            or "",
                            "is_correct": bool(
                                opt.get("is_correct")
                                or opt.get("es_correcta")
                                or opt.get("correct")
                            ),
                        }
                    )
            allows_multiple = sum(1 for opt in norm_opts if opt["is_correct"]) != 1
            normalized.append(
                {
                    "id": qid,
                    "text": text,
                    "options": norm_opts,
                    "allows_multiple": allows_multiple,
                }
            )
    return normalized


def evaluate_exam_submission(questions, submitted_answers):
    """
    Evalúa la selección del usuario.
    submitted_answers: dict de question_id -> set(option_id)
    """
    results = []
    correct_count = 0

    for q in questions:
        qid = q.get("id")
        # Convertir la selección del usuario a set solo para comparar,
        # pero no guardar sets en los resultados (JSONField).
        selected = set(submitted_answers.get(qid, []))
        correct_ids = {
            opt["id"] for opt in q.get("options", []) if opt.get("is_correct")
        }

        is_correct = selected == correct_ids and (correct_ids or not selected)
        if is_correct:
            correct_count += 1

        results.append(
            {
                "question": q.get("text", ""),
                "selected": list(selected),
                "correct_ids": list(correct_ids),
                "is_correct": is_correct,
                "options": q.get("options", []),
            }
        )

    total = len(questions)
    return correct_count, total, results
