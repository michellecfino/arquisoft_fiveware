from flask import Flask, request, jsonify
from database import get_db_connection 

app = Flask(__name__)

@app.route('/ingresar-gasto', methods=['POST'])
def ingresar_gasto():
    data = request.get_json()
    
    id_empresa = data.get('id_empresa')
    id_proyecto = data.get('id_proyecto')
    servicio = data.get('servicio', 'AWS-Generic')
    costo = data.get('costo')
    fecha = data.get('fecha')

    if not all([id_empresa, id_proyecto, costo, fecha]):
        return jsonify({"error": "Faltan datos obligatorios (id_empresa, id_proyecto, costo, fecha)"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO nube.consumos_crudos 
            (id_empresa, id_proyecto, tipo_servicio, costo, fecha_consumo, moneda, id_recurso_crudo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id_empresa, id_proyecto, servicio, costo, fecha, 'USD', 'AUTO-GEN'))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "Gasto registrado en nube.consumos_crudos"
        }), 201

    except Exception as e:
        print(f"Error en DB: {e}")
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)