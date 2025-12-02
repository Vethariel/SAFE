from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from accounts.models import AppUser
from administration.services import change_role


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
