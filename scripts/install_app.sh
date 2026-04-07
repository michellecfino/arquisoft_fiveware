#!/bin/bash
apt-get update -y
apt-get install -y docker.io docker-compose git

systemctl start docker
systemctl enable docker

cd /home/ubuntu
git clone -b escalabilidad https://github.com/michellecfino/arquisoft_fiveware.git
cd arquisoft_fiveware

cat <<EOT > .env
DB_HOST=${rds_endpoint}
DB_NAME=bit_db
DB_USER=admin_user
DB_PASS=michi1234
RABBITMQ_HOST=${rabbitmq_ip}
RABBIT_USER=guest
RABBIT_PASS=guest
EOT

docker-compose up -d --build