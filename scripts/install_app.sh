#!/bin/bash
apt-get update -y
apt-get install -y docker.io docker-compose
systemctl start docker
systemctl enable docker

cd /home/ubuntu
git clone -b escalabilidad https://github.com/michellecfino/arquisoft_fiveware.git
cd arquisoft_fiveware

cat <<EOT > .env
DATABASE_URL=postgresql://admin_user:michi1234@${rds_endpoint}/bit_db
RABBITMQ_URL=amqp://guest:guest@${rabbitmq_ip}:5672/
MAIL_SERVER=sandbox.smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=2590727e8400fc
MAIL_PASSWORD=48eca203f8ea51
EOT

chown -R ubuntu:ubuntu /home/ubuntu/arquisoft_fiveware
docker-compose up -d --build

sleep 15 

MY_IP=$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)
curl -X POST http://${kong_private_ip}:8001/upstreams/flask_cluster/targets --data "target=$MY_IP:8000"