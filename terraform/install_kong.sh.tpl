#!/bin/bash
set -euxo pipefail

# Instalar Docker en la máquina de Amazon Linux
dnf update -y
dnf install -y docker

systemctl enable docker
systemctl start docker

# Escribir la configuración declarativa
mkdir -p /etc/kong
cat << 'KONGEOF' > /etc/kong/kong.yml
${kong_config}
KONGEOF

# Levantar Kong apuntando al archivo
docker run -d --name kong \
  -v /etc/kong:/usr/local/kong/declarative \
  -p 8000:8000 \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/usr/local/kong/declarative/kong.yml" \
  --restart always \
  kong:3.6.1
