Para `smtp-simulator-instance`:

```bash
ssh -i <llave>.pem ubuntu@<IP_PUBLICA_SMTP>
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker
sudo docker run -d \
  --name mailhog \
  -p 1025:1025 \
  -p 8025:8025 \
  mailhog/mailhog