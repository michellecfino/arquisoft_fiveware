from django.http import JsonResponse
from django.shortcuts import render
from .logic.reportes_logic import obtener_reporte_y_notificar, obtener_empresa_de_proyecto
from .logic.log_client import registrar_accion

# IPs bloqueadas (Revoke Access Handler en memoria)
_ips_bloqueadas = set()
_intentos_fallidos = {}
MAX_INTENTOS = 5001


def get_user(request):
    return {
        "user_id": request.headers.get("X-User", "anon"),
        "role":    request.headers.get("X-Role", "user"),
        # X-Empresa-Id: empresa a la que pertenece el usuario autenticado
        "empresa_id": request.headers.get("X-Empresa-Id", None),
    }


def get_client_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def verificar_autorizacion(user, id_proyecto, ip):
    """
    Tactica Limit Exposure + Revoke Access:
    Verifica que el usuario solo acceda a proyectos de SU empresa.
    Si falla 3 veces, bloquea la IP.
    """
    # ── Tactica: Revoke Access — IP ya bloqueada ──
    if ip in _ips_bloqueadas:
        return False, "IP bloqueada por accesos no autorizados"

    empresa_del_proyecto = obtener_empresa_de_proyecto(id_proyecto)
    empresa_del_usuario = user.get("empresa_id")

    if empresa_del_usuario is None:
        return False, "Token sin empresa asignada"

    if str(empresa_del_proyecto) != str(empresa_del_usuario):
        # Registrar intento fallido
        _intentos_fallidos[ip] = _intentos_fallidos.get(ip, 0) + 1

        if _intentos_fallidos[ip] >= MAX_INTENTOS:
            _ips_bloqueadas.add(ip)
            registrar_accion(
                user["user_id"],
                "IP_BLOQUEADA",
                f"IP {ip} bloqueada tras {MAX_INTENTOS} intentos no autorizados"
            )
            return False, f"IP bloqueada tras {MAX_INTENTOS} intentos no autorizados"

        return False, (
            f"Acceso no autorizado: empresa del proyecto ({empresa_del_proyecto}) "
            f"no coincide con empresa del usuario ({empresa_del_usuario}). "
            f"Intento {_intentos_fallidos[ip]}/{MAX_INTENTOS}"
        )

    # Acceso autorizado — limpiar intentos fallidos si los había
    if ip in _intentos_fallidos:
        del _intentos_fallidos[ip]

    return True, "ok"


def resumen_reporte_api(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    user = get_user(request)
    ip   = get_client_ip(request)

    # ── Validacion de autorizacion por empresa ──
    autorizado, motivo = verificar_autorizacion(user, id_proyecto, ip)
    if not autorizado:
        registrar_accion(
            user["user_id"],
            "ACCESO_NO_AUTORIZADO",
            f"ip={ip}, proyecto={id_proyecto}, motivo={motivo}"
        )
        return JsonResponse({"error": motivo}, status=403)

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


def resumen_reporte_vista(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    user = get_user(request)
    ip   = get_client_ip(request)

    autorizado, motivo = verificar_autorizacion(user, id_proyecto, ip)
    if not autorizado:
        registrar_accion(user["user_id"], "ACCESO_NO_AUTORIZADO",
                         f"ip={ip}, proyecto={id_proyecto}, motivo={motivo}")
        return JsonResponse({"error": motivo}, status=403)

    try:
        data = obtener_reporte_y_notificar(
            id_proyecto=int(id_proyecto),
            anio=int(anio),
            mes=int(mes),
        )

        registrar_accion(user["user_id"], "CONSULTA_REPORTE_VISTA",
                         f"proyecto={id_proyecto}, periodo={anio}-{mes}")

        return render(request, "reportes/resumen_reporte.html",
                      {"reporte": data["reporte"]})

    except Exception as exc:
        registrar_accion(user["user_id"], "ERROR_CONSULTA_REPORTE_VISTA", str(exc))
        return JsonResponse({"error": str(exc)}, status=400)