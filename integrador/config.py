# config.py

# URL del Agregador (IP Pública o Privada de la instancia EC2 donde corre Flask)
AGREGADOR_URL = "http://54.xx.xx.xx:8000/ingresar-gasto"

# Rango de gastos aleatorios
MONTO_MIN = 500
MONTO_MAX = 5000

# Tiempo de espera entre envíos (en segundos)
# 0.1 = 10 gastos por segundo
# 1.0 = 1 gasto por segundo
DELAY = 0.5 

# Servicios simulados para dar variedad a la tabla cruda
SERVICIOS = ["EC2", "S3", "RDS", "Lambda", "CloudFront", "DynamoDB"]