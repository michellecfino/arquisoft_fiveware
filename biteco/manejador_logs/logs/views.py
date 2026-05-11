from django.http import JsonResponse
from django.shortcuts import render
from .models import AuditLog
import json

def registrar_log(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    if request.headers.get("X-Internal-Token") != "super-secret":
        return JsonResponse({"error": "Forbidden"}, status=403)

    try:
        data = json.loads(request.body)
        log = AuditLog.objects.create(
            user_id=request.headers.get("X-User-Id", "system"),
            role=request.headers.get("X-User-Role", "SYSTEM"),
            service=data.get("service"),
            action=data.get("action")
        )
        print(f"[AUDIT LOG] {log.created_at} - {log.action}")
        return JsonResponse({"message": "Log registrado"}, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def listar_logs(request):
    # Ahora usamos el header de email que Kong envía
    user_email = request.headers.get("X-User-Email")

    # Validamos directamente por el email del administrador
    if user_email != "admin@biteco.com":
        return JsonResponse({"error": "Access Denied"}, status=403)

    logs_queryset = AuditLog.objects.all().order_by('-created_at')

    if 'text/html' in request.headers.get('Accept', ''):
        return render(request, 'lista_logs.html', {'logs': logs_queryset})

    return JsonResponse(list(logs_queryset.values()), safe=False)
