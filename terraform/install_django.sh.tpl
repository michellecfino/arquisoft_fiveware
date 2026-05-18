#!/bin/bash
set -e

# =============================================================================
# install_django.sh.tpl — Instalación de Django Server en Ubuntu 24.04 LTS
# =============================================================================
# Instala y ejecuta 1 instancia de Django (para 4 EC2 instances)
# Se comunica con RDS PostgreSQL
# Accesible SOLO desde Kong Gateway (Security Group)
# Usa SSM para acceso administrativo
# =============================================================================

echo "========== Django Server Setup =========="

# Habilitar SSH con PasswordAuthentication
echo "Enabling SSH PasswordAuthentication..."
sed -i 's/^#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Actualizar sistema
apt-get update
apt-get upgrade -y

# Instalar Python 3.12 y pip
apt-get install -y \
  python3.12 \
  python3.12-venv \
  python3.12-dev \
  python3-pip \
  git \
  postgresql-client \
  curl \
  build-essential

# Crear directorio de aplicación
mkdir -p /opt/disponibilidad
cd /opt/disponibilidad

# Clonar repo (si existe en git)
# git clone <repo-url> . || true

# O descargar via S3/curl (aquí asumimos que está disponible localmente)
# Por ahora, crear structure básica y instalar dependencies

# Crear virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Instalar Django y dependencias
pip install --upgrade pip
pip install Django==5.0.6 psycopg2-binary==2.9.9 gunicorn==22.0.0 python-decouple==3.8

# Configurar variables de entorno para Django
cat > /opt/disponibilidad/.env <<EOF
DEBUG=False
DJANGO_SECRET_KEY=django-insecure-change-me-in-production
DB_HOST=${db_host}
DB_PORT=${db_port}
DB_NAME=${db_name}
DB_USER=${db_user}
DB_PASSWORD=${db_password}
ALLOWED_HOSTS=*
USE_X_FORWARDED_HOST=True
HEARTBEAT_DISABLED=0
EOF

# Crear script de inicio de Django con Gunicorn
cat > /opt/disponibilidad/start_django.sh <<'SCRIPT'
#!/bin/bash
source /opt/disponibilidad/venv/bin/activate
cd /opt/disponibilidad

# Ejecutar migraciones
python manage.py migrate --noinput 2>/dev/null || true

# Ejecutar Gunicorn
gunicorn src.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
SCRIPT

chmod +x /opt/disponibilidad/start_django.sh

# Crear systemd service para Django
cat > /etc/systemd/system/django.service <<'SERVICE'
[Unit]
Description=Django Disponibilidad Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/disponibilidad
ExecStart=/opt/disponibilidad/start_django.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Iniciar servicio
systemctl daemon-reload
systemctl start django
systemctl enable django

echo "Django server started successfully!"
echo "Django Listening on: 0.0.0.0:8000"
echo "PostgreSQL Host: ${db_host}"
