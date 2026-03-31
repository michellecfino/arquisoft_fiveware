from flask import Flask, request, jsonify
from database import get_db_connection

app = Flask(__name__)

@app.route('/ingresar-gasto', methods=['POST'])
def ingresar_gasto():
    data = request.get_json()
    
    # Extraer datos del JSON enviado por el Integrador
    empresa_id = data.get('empresa_id')
    proyecto_id = data.get('proyecto_id')
    servicio = data.get('servicio', 'AWS-Generic')
    costo = data.get('costo')
    fecha = data.get('fecha')

    if not all([empresa_id, proyecto_id, costo, fecha]):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insertamos en la tabla CRUDA (billing)
        # El Trigger se dispara solo después de este INSERT
        cur.execute("""
            INSERT INTO billing.consumo_cloud (empresa_id, proyecto_id, servicio, costo, fecha)
            VALUES (%s, %s, %s, %s, %s)
        """, (empresa_id, proyecto_id, servicio, costo, fecha))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"status": "Gasto registrado y procesado por Trigger"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)