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

def listar_logs(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    user_role = request.headers.get("X-User-Role") 

    if user_role != "ADMIN":
        return JsonResponse({
            "error": "Access Denied", 
            "message": "Solo usuarios con rol ADMIN pueden ver los logs."
        }, status=403)

    logs = AuditLog.objects.all().order_by('-created_at').values()
    return JsonResponse(list(logs), safe=False)
