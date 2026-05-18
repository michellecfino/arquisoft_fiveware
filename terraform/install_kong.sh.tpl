#!/bin/bash
set -e

# =============================================================================
# install_kong.sh.tpl — Instalación de Kong Gateway en Ubuntu 24.04 LTS
# =============================================================================
# Kong actúa como:
#   1. Proxy inverso
#   2. Balanceador de carga (hacia los 4 Django servers)
#   3. Gateway API único
#
# Los Django servers internos se comunican con Kong a través de sus IPs privadas
# =============================================================================

echo "========== Kong Gateway Setup =========="

# Habilitar SSH con PasswordAuthentication
echo "Enabling SSH PasswordAuthentication..."
sed -i 's/^#PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Actualizar sistema
apt-get update
apt-get upgrade -y

# Instalar dependencias
apt-get install -y \
  curl \
  wget \
  git \
  build-essential \
  libpcre3 \
  libpcre3-dev \
  zlib1g \
  zlib1g-dev \
  libssl-dev \
  libgd-dev \
  libgeoip-dev

# Instalar Kong (Debian/Ubuntu)
echo "Installing Kong..."
curl -1sLf "https://packagecloud.io/install/repositories/kong/kong/script.deb.sh" | sudo -E bash
apt-get install -y kong

# Iniciar Kong
systemctl start kong
systemctl enable kong

# Crear directorio de configuración declarativa
mkdir -p /etc/kong/

# Generar configuración Kong declarativa con upstreams
cat > /etc/kong/kong.yml <<'EOF'
_format_version: "3.0"
_transform: false

services:
  - name: disponibilidad-reportes
    url: http://127.0.0.1:8001  # Placeholder, se sobrescribe
    connect_timeout: 500
    write_timeout: 5000
    read_timeout: 5000
    retries: 0
    routes:
      - name: api-reports
        paths:
          - /api/reports
        strip_path: false
      - name: catch-all
        paths:
          - /
        strip_path: false

upstreams:
  - name: django-cluster
    algorithm: round_robin
    targets: []  # Se poblarán dinámicamente

plugins:
  - name: rate-limiting
    config:
      minute: 100
      hour: 10000
EOF

echo "Kong installed and configured successfully!"
echo "Kong Proxy: http://$(hostname -I | awk '{print $1}'):8000"
echo "Kong Admin:  http://$(hostname -I | awk '{print $1}'):8001"
