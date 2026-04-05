#!/bin/bash
apt-get update -y
apt-get install -y docker.io docker-compose
systemctl start docker
systemctl enable docker

cd /home/ubuntu
git clone -b escalabilidad https://github.com/michellecfino/arquisoft_fiveware.git
cd arquisoft_fiveware

cat <<EOT >> .env
DATABASE_URL=postgresql://admin_user:michi1234@${rds_endpoint}/bit_db
RABBITMQ_URL=amqp://guest:guest@${rabbitmq_ip}:5672/
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=TU_USUARIO_MAILTRAP
MAIL_PASSWORD=TU_PASSWORD_MAILTRAP
EOT

chown -R ubuntu:ubuntu /home/ubuntu/arquisoft_fiveware
docker-compose up -d --build