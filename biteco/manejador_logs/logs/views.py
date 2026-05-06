from django.http import JsonResponse
from .models import AuditLog
import json

# SOLO USO INTERNO (no usuarios)
def registrar_log(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Token interno (cámbialo luego por variable de entorno)
    internal_token = request.headers.get("X-Internal-Token")
    if internal_token != "super-secret":
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body)

        log = AuditLog.objects.create(
            user_id=request.headers.get("X-User-Id", "system"),
            role=request.headers.get("X-User-Role", "SYSTEM"),
            service=data.get("service"),
            action=data.get("action")
        )

        # Imprimir en consola cada log recibido
        print(f"[AUDIT LOG] {log.created_at} - {log.user_id} ({log.role}) - {log.service} -> {log.action}")
        print(f"[RAW JSON] {json.dumps(data)}")  # Muestra el JSON completo recibido

        return JsonResponse({"message": "Log registrado"}, status=200)

    except Exception as e:
        print(f"[AUDIT LOG ERROR] {e}")
        return JsonResponse({"error": str(e)}, status=500)


# SOLO ADMIN PUEDE VER
def listar_logs(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    user_role = request.headers.get("X-User-Role", "USER")

    if user_role != "ADMIN":
        return JsonResponse({
            "error": "Access Denied",
            "message": "Solo ADMIN puede ver logs"
        }, status=403)

    logs = AuditLog.objects.all().order_by('-created_at').values()

    return JsonResponse(list(logs), safe=False)