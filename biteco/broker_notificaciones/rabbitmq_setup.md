# Setup broker-instance (RabbitMQ)
sudo apt update
sudo apt install rabbitmq-server -y
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl status rabbitmq-server.service
sudo rabbitmq-plugins enable rabbitmq_management
sudo rabbitmqctl add_user biteco_user isis2503
sudo rabbitmqctl set_user_tags biteco_user administrator
sudo rabbitmqctl set_permissions -p / biteco_user ".*" ".*" ".*"
sudo rabbitmqctl list_users
sudo rabbitmqctl list_queues
sudo rabbitmqctl list_exchanges

Abrir en navegador:
http://<IP_PUBLICA_BROKER>:15672

Usuario:
biteco_user

Clave:
isis2503