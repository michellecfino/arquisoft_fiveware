from flask import Flask, request, jsonify
from database import get_db_connection

app = Flask(__name__)

@app.route('/reporte-mensual', methods=['GET'])
def obtener_reporte():
    # JMeter enviará estos parámetros: ?empresa_id=1&proyecto_id=10&anio=2026&mes=3
    empresa_id = request.args.get('empresa_id')
    proyecto_id = request.args.get('proyecto_id')
    anio = request.args.get('anio')
    mes = request.args.get('mes')

    if not all([empresa_id, proyecto_id, anio, mes]):
        return jsonify({"error": "Faltan parámetros de consulta"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # CONSULTA MAESTRA: Unimos la tabla agregada con nombres de empresa y proyecto
        # Esta consulta es O(1) gracias al índice compuesto (PK)
        query = """
            SELECT 
                e.nombre AS empresa, 
                p.nombre AS proyecto, 
                r.anio, 
                r.mes, 
                r.costo_total,
                r.ultima_actualizacion
            FROM analytics.resumen_mensual_costos r
            JOIN core.empresas e ON r.empresa_id = e.id_empresa
            JOIN core.proyectos p ON r.proyecto_id = p.id_proyecto
            WHERE r.empresa_id = %s 
              AND r.proyecto_id = %s 
              AND r.anio = %s 
              AND r.mes = %s;
        """
        
        cur.execute(query, (empresa_id, proyecto_id, anio, mes))
        row = cur.fetchone()
        
        cur.close()
        conn.close()

        if row:
            return jsonify({
                "empresa": row[0],
                "proyecto": row[1],
                "periodo": f"{row[2]}-{row[3]:02d}",
                "costo_total": float(row[4]),
                "actualizado_el": row[5].strftime("%Y-%m-%d %H:%M:%S"),
                "status": "success"
            }), 200
        else:
            return jsonify({"message": "No hay datos para este periodo"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Importante: host='0.0.0.0' para que AWS lo deje ver desde afuera
    app.run(host='0.0.0.0', port=8001)