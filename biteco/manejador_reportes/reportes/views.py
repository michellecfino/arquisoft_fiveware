from django.http import JsonResponse
from django.shortcuts import render, redirect
from .logic.reportes_logic import obtener_reporte_y_notificar
from .logic.log_client import registrar_accion

def get_user(request):
    user_id = request.headers.get("X-User", "anon")
    role = request.headers.get("X-Role", "user")
    return {
        "user_id": user_id,
        "role": role
    }

def resumen_reporte_api(request, id_proyecto, anio, mes):
    # Guardar la URL actual para después del login
    request.session['next_url'] = request.get_full_path()
    
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    user = get_user(request)

    try:
        data = obtener_reporte_y_notificar(
            id_proyecto=int(id_proyecto),
            anio=int(anio),
            mes=int(mes),
        )

        registrar_accion(
            user["user_id"],
            "CONSULTA_REPORTE_API",
            f"proyecto={id_proyecto}, periodo={anio}-{mes}"
        )

        return JsonResponse(data, status=200)

    except Exception as exc:
        registrar_accion(
            user["user_id"],
            "ERROR_CONSULTA_REPORTE_API",
            str(exc)
        )
        return JsonResponse({"error": str(exc)}, status=400)


def resumen_reporte_vista(request, id_proyecto=None, anio=None, mes=None):
    # Si vino sin parámetros (después de Cognito)
    if id_proyecto is None:
        # Recuperar la URL original guardada en sesión
        next_url = request.session.pop('next_url', None)
        if next_url:
            return redirect(next_url)
        # Si no hay URL guardada, usar valores por defecto
        return redirect('/reportes/1/2026/5/')
    
    # Guardar la URL actual para después del login
    request.session['next_url'] = request.get_full_path()
    
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    user = get_user(request)

    try:
        data = obtener_reporte_y_notificar(
            id_proyecto=int(id_proyecto),
            anio=int(anio),
            mes=int(mes),
        )

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