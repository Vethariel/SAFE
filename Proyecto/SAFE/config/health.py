from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

def db_health(request):
    conn = connections["default"]
    try:
        conn.close_if_unusable_or_obsolete()
        conn.ensure_connection()
        ok = conn.is_usable()
    except OperationalError:
        ok = False

    return JsonResponse(
        {"db_status": "Healthy" if ok else "Unhealthy"},
        status=200 if ok else 500,
    ) 