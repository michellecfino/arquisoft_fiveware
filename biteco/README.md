

worker:
ssh -i <llave>.pem ubuntu@<IP_PUBLICA_WORKER>

sudo apt update
sudo apt install python3 python3-pip python3-venv git libpq-dev build-essential python3-dev -y

git clone <REPO_URL>
cd biteco

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env worker_email/.env

cd worker_email
python manage.py consumir_cola_correos

-simulador smtp:
sudo apt update
sudo apt install docker.io -y
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl status docker
sudo docker run -d \
  --name mailhog \
  -p 1025:1025 \
  -p 8025:8025 \
  mailhog/mailhog
  sudo docker run -d \
  --name mailhog \
  -p 1025:1025 \
  -p 8025:8025 \
  mailhog/mailhog