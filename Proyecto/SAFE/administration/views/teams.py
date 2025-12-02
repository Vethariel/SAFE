from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.urls import reverse
from django.contrib import messages
from teams.models import Team, TeamUser
from accounts.models import AppUser


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
