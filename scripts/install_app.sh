#!/bin/bash
apt-get update -y
apt-get install -y docker.io docker-compose git

systemctl start docker
systemctl enable docker

cd /home/ubuntu
git clone -b escalabilidad https://github.com/michellecfino/arquisoft_fiveware.git
cd arquisoft_fiveware

cat <<EOT > .env
DATABASE_URL=postgresql://admin_user:michi1234@${rds_endpoint}/bit_db
RABBITMQ_URL=amqp://guest:guest@${rabbitmq_ip}:5672/
EOT

docker-compose up -d --build