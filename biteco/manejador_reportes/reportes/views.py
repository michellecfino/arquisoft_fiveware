from django.http import JsonResponse
from .logic.reportes_logic import obtener_reporte


def resumen_reporte(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        data = obtener_reporte(int(id_proyecto), int(anio), int(mes))
        return JsonResponse(data, status=200)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)