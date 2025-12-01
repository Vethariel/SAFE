from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from . import models
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def supervisor_panel(request):
    if request.user.role != "supervisor":
        return HttpResponse("No tienes permisos", status=403)

    return render(request, "teams/supervisor_panel.html")
