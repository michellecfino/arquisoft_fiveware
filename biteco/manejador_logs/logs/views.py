from django.http import JsonResponse
from django.shortcuts import render # <--- Nueva importación
from .models import AuditLog
import json

# SOLO USO INTERNO (no usuarios)
def registrar_log(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

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

        print(f"[AUDIT LOG] {log.created_at} - {log.user_id} ({log.role}) - {log.service} -> {log.action}")
        print(f"[RAW JSON] {json.dumps(data)}")

        return JsonResponse({"message": "Log registrado"}, status=200)

    except Exception as e:
        print(f"[AUDIT LOG ERROR] {e}")
        return JsonResponse({"error": str(e)}, status=500)

def listar_logs(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Permitimos ADMIN vía Header o vía URL (?role=ADMIN) para que lo veas en el navegador
    user_role = request.headers.get("X-User-Role") or request.GET.get("role")

    if user_role != "ADMIN":
        return JsonResponse({"error": "Forbidden", "message": "Solo ADMIN puede ver logs"}, status=403)

    logs_queryset = AuditLog.objects.all().order_by('-created_at')

    # Si entras desde el navegador, devolvemos el HTML
    if 'text/html' in request.headers.get('Accept', ''):
        return render(request, 'templates/lista_logs.html', {'logs': logs_queryset})

    # Si es una app/petición técnica, devolvemos JSON
    return JsonResponse(list(logs_queryset.values()), safe=False)