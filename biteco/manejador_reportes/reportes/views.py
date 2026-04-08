from django.http import JsonResponse
from django.shortcuts import render
from .logic.reportes_logic import obtener_reporte_y_notificar


def resumen_reporte_api(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        id_empresa = int(request.GET["id_empresa"])
        id_area = int(request.GET["id_area"])
        id_usuario = int(request.GET["id_usuario"])
        correo_destino = request.GET["correo_destino"]

        data = obtener_reporte_y_notificar(
            id_empresa=id_empresa,
            id_area=id_area,
            id_proyecto=int(id_proyecto),
            id_usuario=id_usuario,
            correo_destino=correo_destino,
            anio=int(anio),
            mes=int(mes),
        )
        return JsonResponse(data, status=200)
    except KeyError as exc:
        return JsonResponse({"error": f"Falta parametro requerido: {exc}"}, status=400)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


def resumen_reporte_vista(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        id_empresa = int(request.GET["id_empresa"])
        id_area = int(request.GET["id_area"])
        id_usuario = int(request.GET["id_usuario"])
        correo_destino = request.GET["correo_destino"]

        data = obtener_reporte_y_notificar(
            id_empresa=id_empresa,
            id_area=id_area,
            id_proyecto=int(id_proyecto),
            id_usuario=id_usuario,
            correo_destino=correo_destino,
            anio=int(anio),
            mes=int(mes),
        )
        return render(request, "reportes/resumen_reporte.html", {"reporte": data["reporte"]})
    except KeyError as exc:
        return JsonResponse({"error": f"Falta parametro requerido: {exc}"}, status=400)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)