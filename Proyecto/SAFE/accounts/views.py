from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Count
from .models import AppUser
from enrollments.models import CourseInscription
from django.contrib.auth import update_session_auth_hash
from .password_validator import is_valid_password
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from enrollments.services import (
    get_courses_for_user,
    _build_catalog_card_for_course,
    _build_inscriptions_prefetch,
)


def login(request):
    "Muestra el formulario de inicio de sesion"
    if request.user.is_authenticated:
        return redirect("catalog")
    return render(request, "accounts/login.html")


@require_POST
def log(request):
    "Loguea al usuario si el email y contrasena son correctos"

    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    if not exisit_email(email):
        messages.error(request, "Email no existente")
        return redirect("login")

    user = AppUser.objects.get(email=email)
    if not user.check_password(password):
        messages.error(request, "Contraseña incorrecta")
        return redirect("login")

    auth_login(request, user)
    return redirect("catalog")


def exisit_email(email):
    "Verifica si el email existe en la base de datos"
    try:
        AppUser.objects.get(email=email)
    except AppUser.DoesNotExist:
        return False
    return True


def unique_email(email):
    """Retorna True si existe un usuario con el email dado."""

    return AppUser.objects.filter(email=email).exists()


def to_signup(request):
    return render(request, "accounts/sign_up.html")


def to_login(request):
    return render(request, "accounts/login.html")


@require_POST
def user_add(request):
    username = request.POST.get("username", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "").strip()
    confirm_password = request.POST.get("confirm_password", "").strip()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()

    if not (username and email and password and confirm_password):
        return redirect("signup")

    if AppUser.objects.filter(username=username).exists():
        error_msg = (
            "Este nombre de usuario ya existe. \n Intenta con un nombre distinto"
        )
        return render(
            request,
            "accounts/sign_up.html",
            {
                "usuarios": list(
                    AppUser.objects.order_by("id").values(
                        "id", "username", "email", "password"
                    )
                ),
                "error_msg": error_msg,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

    if exisit_email(email):
        error_msg = "Este email ya está registrado. \n Intenta con un email distinto"
        print(error_msg)
        return render(
            request,
            "accounts/sign_up.html",
            {
                "usuarios": list(
                    AppUser.objects.order_by("id").values(
                        "id", "username", "email", "password"
                    )
                ),
                "error_msg": error_msg,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
    if password != confirm_password:
        error_msg = "Las contraseñas no coinciden."
        return render(
            request,
            "accounts/sign_up.html",
            {
                "usuarios": list(
                    AppUser.objects.order_by("id").values(
                        "id", "username", "email", "password"
                    )
                ),
                "error_msg": error_msg,
                "username": username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )

    if not is_valid_password(password):
        error_msg = (
            "La contraseña debe cumplir con todos los requisitos:\n"
            "- Mínimo 8 caracteres\n"
            "- Mínimo una mayúscula\n"
            "- Mínimo una minúscula\n"
            "- Mínimo un número\n"
            "- No contener espacios"
        )
        return render(
            request,
            "accounts/sign_up.html",
            {
                "usuarios": list(
                    AppUser.objects.order_by("id").values(
                        "id", "username", "email", "password"
                    )
                ),
                "error_msg": error_msg,
                "username": username,
                "email": email,
            },
        )

    with transaction.atomic():
        user = AppUser.objects.create_user(
            username=username, email=email, password=password
        )

        # Asignación manual de atributos
        user.name = f"{first_name} {last_name}".strip()
        user.first_name = first_name
        user.last_name = last_name

        user.save()

    messages.success(request, "Registro exitoso. Por favor inicia sesión.")
    return redirect("login")


@login_required
@require_POST
def admin_create_user(request):
    username = request.POST.get("username", "").strip()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    role = request.POST.get("role", "colaborador")
    password = request.POST.get("password", "").strip()
    confirm_password = request.POST.get("confirm_password", "").strip()

    # --- Validaciones Básicas ---
    if not (username and email and password):
        messages.error(request, "Todos los campos obligatorios deben llenarse.")
        return redirect("admin_panel")

    if password != confirm_password:
        messages.error(request, "Las contraseñas no coinciden.")
        return redirect("admin_panel")

    if AppUser.objects.filter(username=username).exists():
        messages.error(request, f"El usuario '{username}' ya existe.")
        return redirect("admin_panel")

    if not is_valid_password(password):
        msg = "La contraseña es muy débil. Requiere: 8 caracteres, mayúscula, minúscula, número y sin espacios."
        messages.error(request, msg)
        return redirect(reverse("admin_panel") + "?tab=usuarios")
    # -------------------------------------------------------------

    # --- Creación Segura ---
    try:
        with transaction.atomic():
            user = AppUser.objects.create_user(
                username=username, email=email, password=password
            )

            # Asignación manual de atributos
            user.name = f"{first_name} {last_name}".strip()
            user.first_name = first_name
            user.last_name = last_name
            user.role = role
            user.status = "active"

            user.save()

        messages.success(request, "Usuario creado con éxito.")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        messages.error(request, f"Error del sistema: {e}")

    return redirect(reverse("admin_panel") + "?tab=usuarios")


@login_required
@require_POST
def user_update_role(request, pk):
    """
    Actualiza el rol de un usuario específico.
    Se activa automáticamente al cambiar el select en el panel de admin.
    """
    user_to_update = get_object_or_404(AppUser, pk=pk)

    if user_to_update == request.user:
        messages.error(request, "No puedes cambiar tu propio rol desde aquí.")
        return redirect("admin_panel")

    new_role = request.POST.get("role")
    allowed_roles = ["colaborador", "supervisor", "analistaTH"]

    if new_role in allowed_roles:
        user_to_update.role = new_role
        user_to_update.save()
        messages.success(
            request,
            f"Rol de {user_to_update.username} actualizado a '{user_to_update.get_role_display()}'.",
        )
    else:
        messages.error(request, "Rol no válido.")

    return redirect("admin_panel")


@require_POST
def user_toggle_status(request, pk):
    """
    Cambia el estado del usuario:
    - Si está 'active' -> lo pasa a 'inactive'
    - Si está 'inactive' o 'pending' -> lo pasa a 'active'
    """
    user_to_update = get_object_or_404(AppUser, pk=pk)

    if user_to_update == request.user:
        messages.error(request, "No puedes desactivar tu propio usuario.")
        return redirect(reverse("admin_panel") + "?tab=usuarios")

    if user_to_update.status == "active":
        user_to_update.status = "inactive"
        messages.warning(request, f"Usuario {user_to_update.username} desactivado.")
    else:
        user_to_update.status = "active"
        messages.success(request, f"Usuario {user_to_update.username} activado.")

    user_to_update.save()

    return redirect(reverse("admin_panel") + "?tab=usuarios")


@login_required
def profile(request):
    """Renderiza la vista de perfil."""
    inscriptions = CourseInscription.objects.filter(
        app_user=request.user
    ).select_related("course")

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
    course_cards = [
        _build_catalog_card_for_course(course, request.user) for course in courses_qs
    ]

    return render(
        request,
        "accounts/profile.html",
        {
            "user": request.user,
            "inscriptions": inscriptions,
            "course_cards": course_cards,
        },
    )


@login_required
@require_POST
def update_profile_data(request):
    user = request.user
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()

    if not first_name or not last_name or not email:
        messages.error(request, "Nombre, Apellido y Correo son obligatorios.")
        return redirect("profile")

    if AppUser.objects.filter(email=email).exclude(pk=user.pk).exists():
        messages.error(request, "Ese correo electrónico ya está en uso.")
        return redirect("profile")

    try:
        with transaction.atomic():
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.name = f"{first_name} {last_name}".strip()
            user.save()

        messages.success(
            request,
            "Información actualizada con éxito. Por favor inicia sesión nuevamente.",
            extra_tags="logout-required",
        )

        return redirect("profile")

    except Exception as e:
        messages.error(request, f"Error al actualizar: {e}")
        return redirect("profile")


@login_required
@require_POST
def change_password(request):
    user = request.user
    current_pass = request.POST.get("current_password", "")
    new_pass = request.POST.get("new_password", "")
    confirm_pass = request.POST.get("confirm_password", "")

    if not user.check_password(current_pass):
        messages.error(request, "La contraseña actual es incorrecta.")
        return redirect("profile")

    if new_pass != confirm_pass:
        messages.error(request, "Las nuevas contraseñas no coinciden.")
        return redirect("profile")

    if not is_valid_password(new_pass):
        messages.error(
            request, "La nueva contraseña no cumple con los requisitos de seguridad."
        )
        return redirect("profile")

    try:
        user.set_password(new_pass)
        user.save()

        update_session_auth_hash(request, user)

        messages.success(
            request,
            "Contraseña actualizada con éxito. Por favor inicia sesión nuevamente.",
            extra_tags="logout-required",
        )

        return redirect("profile")
        
    except Exception:
        messages.error(request, "Error al cambiar la contraseña.")
        return redirect("profile")


def logout(request):
    auth_logout(request)
    return redirect("login")
