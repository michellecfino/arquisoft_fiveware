import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .logic.reportes_logic import obtener_reporte, generar_reporte_y_encolar


def resumen_reporte_api(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        data = obtener_reporte(int(id_proyecto), int(anio), int(mes))
        return JsonResponse(data, status=200)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


def resumen_reporte_vista(request, id_proyecto, anio, mes):
    try:
        data = obtener_reporte(int(id_proyecto), int(anio), int(mes))
        return render(request, "reportes/resumen_reporte.html", {"reporte": data})
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@csrf_exempt
def generar_reporte(request):
    if request.method != "POST":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        payload = json.loads(request.body)
        resultado = generar_reporte_y_encolar(
            id_empresa=int(payload["id_empresa"]),
            id_area=int(payload["id_area"]),
            id_proyecto=int(payload["id_proyecto"]),
            id_usuario=int(payload["id_usuario"]),
            correo_destino=payload["correo_destino"],
            anio=int(payload["anio"]),
            mes=int(payload["mes"]),
        )
        return JsonResponse(resultado, status=202)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)