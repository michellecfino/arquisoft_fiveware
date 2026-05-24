import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .logic.agregacion_logic import agregar_consumo
from django.db import connection

@csrf_exempt
def agregar_registro(request):
    print("\n[AGREGADOR] ===== Nueva solicitud =====")
    print(f"[AGREGADOR] Metodo: {request.method}")
    print(f"[AGREGADOR] Path: {request.path}")

    if request.method != "POST":
        print("[AGREGADOR] Metodo no permitido")
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        raw_body = request.body.decode("utf-8")
        print(f"[AGREGADOR] Body crudo: {raw_body}")

        payload = json.loads(raw_body)
        print(f"[AGREGADOR] Payload parseado: {payload}")

        resultado = agregar_consumo(payload)

        print(f"[AGREGADOR] Resultado logica: {resultado}")
        print("[AGREGADOR] ===== Solicitud completada =====\n")

        return JsonResponse(resultado, status=201)

    except Exception as exc:
        print(f"[AGREGADOR] ERROR: {exc}")
        return JsonResponse({"error": str(exc)}, status=400)


def consultar_resumen(request, id_proyecto, anio, mes):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_resumen, id_empresa, id_area, id_proyecto, anio, mes, moneda, costo_total, cantidad_registros
                FROM reportes.resumen_mensual_costos
                WHERE id_proyecto = %s AND anio = %s AND mes = %s
                """,
                [id_proyecto, anio, mes],
            )
            row = cursor.fetchone()

        if not row:
            return JsonResponse({"error": "Resumen no encontrado"}, status=404)

        return JsonResponse({
            "id_resumen": row[0],
            "id_empresa": row[1],
            "id_area": row[2],
            "id_proyecto": row[3],
            "anio": row[4],
            "mes": row[5],
            "moneda": row[6],
            "costo_total": float(row[7]),
            "cantidad_registros": row[8],
        })
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)