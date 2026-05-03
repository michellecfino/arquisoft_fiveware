from django.http import JsonResponse
from django.shortcuts import render
from .logic.reportes_logic import obtener_reporte_y_notificar
from .logic.log_client import registrar_accion  # 👈 NUEVO


def get_user(request):
    return {
        "user_id": request.headers.get("X-User", "anon"),
        "role": request.headers.get("X-Role", "user")
    }


def resumen_reporte_api(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    user = get_user(request)

    try:
        data = obtener_reporte_y_notificar(
            id_proyecto=int(id_proyecto),
            anio=int(anio),
            mes=int(mes),
        )

        # REGISTRO DE AUDITORÍA (ÉXITO)
        registrar_accion(
            user["user_id"],
            "CONSULTA_REPORTE_API",
            f"proyecto={id_proyecto}, periodo={anio}-{mes}"
        )

        return JsonResponse(data, status=200)

    except Exception as exc:
        # REGISTRO DE AUDITORÍA (ERROR)
        registrar_accion(
            user["user_id"],
            "ERROR_CONSULTA_REPORTE_API",
            str(exc)
        )

        return JsonResponse({"error": str(exc)}, status=400)


def resumen_reporte_vista(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    user = get_user(request)

    try:
        data = obtener_reporte_y_notificar(
            id_proyecto=int(id_proyecto),
            anio=int(anio),
            mes=int(mes),
        )

        # REGISTRO DE AUDITORÍA (ÉXITO)
        registrar_accion(
            user["user_id"],
            "CONSULTA_REPORTE_VISTA",
            f"proyecto={id_proyecto}, periodo={anio}-{mes}"
        )

        return render(request, "reportes/resumen_reporte.html", {"reporte": data["reporte"]})

    except Exception as exc:
        registrar_accion(
            user["user_id"],
            "ERROR_CONSULTA_REPORTE_VISTA",
            str(exc)
        )

        return JsonResponse({"error": str(exc)}, status=400)