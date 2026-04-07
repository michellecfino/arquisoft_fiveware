#!/bin/bash

apt-get update -y
apt-get install -y docker.io

systemctl start docker
systemctl enable docker

docker network create kong-net

docker run -d --name kong \
  --network=kong-net \
  -e "KONG_DATABASE=off" \
  -e "KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml" \
  -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
  -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
  -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_LISTEN=0.0.0.0:8001" \
  -p 8000:8000 -p 8001:8001 \
  -v /home/ubuntu/kong.yml:/kong/declarative/kong.yml \
  kong/kong-gateway:3.0