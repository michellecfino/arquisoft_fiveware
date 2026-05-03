from django.http import JsonResponse
from django.shortcuts import render
from .logic.reportes_logic import obtener_reporte_y_notificar


def resumen_reporte_api(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        data = obtener_reporte_y_notificar(
            id_proyecto=int(id_proyecto),
            anio=int(anio),
            mes=int(mes),
        )
        return JsonResponse(data, status=200)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


def resumen_reporte_vista(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        data = obtener_reporte_y_notificar(
            id_proyecto=int(id_proyecto),
            anio=int(anio),
            mes=int(mes),
        )
        return render(request, "reportes/resumen_reporte.html", {"reporte": data["reporte"]})
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)