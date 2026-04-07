#!/bin/bash
apt-get update -y
apt-get install -y docker.io

systemctl start docker

docker network create kong-net

cat <<EOT > /home/ubuntu/kong.yml
_format_version: "3.0"

services:
  - name: app-service
    url: http://${alb_dns}:8001
    routes:
      - name: app-route
        paths:
          - /
EOT

docker run -d --name kong \
  --network=kong-net \
  -v "/home/ubuntu:/kong/declarative/" \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml" \
  -p 8000:8000 \
  kong/kong-gateway:2.7.2.0-alpine
  