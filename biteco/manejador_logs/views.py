from django.http import JsonResponse
from .models import AuditLog
import json


def registrar_log(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)

        AuditLog.objects.create(
            user_id=data.get("user_id"),
            role=data.get("role"),
            service=data.get("service"),
            action=data.get("action")
        )

        return JsonResponse({"message": "Log registrado"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)