#!/bin/bash

apt-get update -y
apt-get install -y docker.io

systemctl start docker
systemctl enable docker

cat <<EOF > /home/ubuntu/kong.yml
_format_version: "3.0"

services:
  - name: reportes
    url: http://${alb_dns}:8001
    routes:
      - name: reportes-route
        paths:
          - /reporte-mensual
EOF

docker run -d --name kong \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong.yml" \
  -p 8000:8000 \
  -p 8001:8001 \
  -v /home/ubuntu/kong.yml:/kong.yml \
  kong/kong-gateway:3.0