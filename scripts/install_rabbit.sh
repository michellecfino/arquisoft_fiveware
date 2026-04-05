#!/bin/bash
apt-get update -y
apt-get upgrade -y

apt-get install rabbitmq-server -y

systemctl enable rabbitmq-server
systemctl start rabbitmq-server

rabbitmq-plugins enable rabbitmq_management

rabbitmqctl add_user admin_biteco password123
rabbitmqctl set_user_tags admin_biteco administrator
rabbitmqctl set_permissions -p / admin_biteco ".*" ".*" ".*"

systemctl restart rabbitmq-server